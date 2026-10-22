"""Unit tests for CountryRouter, state resolution, late-arriving files, and country moves."""
import unittest
from datetime import date, datetime, timezone
from skypoints.models import MemberRecord, ValidationStatus
from skypoints.storage import DatabaseManager
from skypoints.router import CountryRouter


class TestCountryRouter(unittest.TestCase):
    """Test suite for country routing, conflict resolution, and migration logic."""

    def setUp(self):
        self.router = CountryRouter()
        self.db = DatabaseManager(":memory:")
        self.t1 = datetime(2024, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
        self.t2 = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.db.close()

    def test_within_batch_tie_breaker(self):
        """Verify larger source_row_number wins when timestamps are identical."""
        recs = [
            MemberRecord(
                member_id="M01",
                member_name="First Version",
                tier_code="SLV",
                source_system="HD_FEED",
                source_file_name="feed.txt",
                source_file_timestamp=self.t1,
                source_row_number=5,
            ),
            MemberRecord(
                member_id="M01",
                member_name="Final State",
                tier_code="GLD",
                source_system="HD_FEED",
                source_file_name="feed.txt",
                source_file_timestamp=self.t1,
                source_row_number=12,
            ),
        ]
        resolved = self.router.deduplicate_and_resolve_latest(recs)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].member_name, "Final State")
        self.assertEqual(resolved[0].tier_code, "GLD")
        self.assertEqual(resolved[0].source_row_number, 12)

    def test_within_batch_timestamp_resolution(self):
        """Verify later file timestamp wins regardless of list order."""
        recs = [
            MemberRecord(
                member_id="M02",
                member_name="Newer Info",
                tier_code="PLT",
                source_system="HD_FEED",
                source_file_name="feed_new.txt",
                source_file_timestamp=self.t2,
                source_row_number=2,
            ),
            MemberRecord(
                member_id="M02",
                member_name="Older Info",
                tier_code="SLV",
                source_system="HD_FEED",
                source_file_name="feed_old.txt",
                source_file_timestamp=self.t1,
                source_row_number=99,
            ),
        ]
        resolved = self.router.deduplicate_and_resolve_latest(recs)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].member_name, "Newer Info")
        self.assertEqual(resolved[0].tier_code, "PLT")

    def test_country_routing_and_insertion(self):
        """Verify members are routed to appropriate Table_<Country> tables."""
        recs = [
            MemberRecord(
                member_id="IND01",
                member_name="Aarav",
                country="India",
                tier_code="GLD",
                source_system="HD_FEED",
                source_file_name="feed.txt",
                source_file_timestamp=self.t1,
                source_row_number=1,
            ),
            MemberRecord(
                member_id="USA01",
                member_name="Bob",
                country="USA",
                tier_code="PLT",
                source_system="HD_FEED",
                source_file_name="feed.txt",
                source_file_timestamp=self.t1,
                source_row_number=2,
            ),
        ]
        summary = self.router.apply_member_updates(recs, self.db)
        self.assertEqual(summary["inserted"], 2)
        self.assertIn("Table_India", self.db.get_table_names())
        self.assertIn("Table_USA", self.db.get_table_names())

        ind_rows = self.db.conn.execute("SELECT member_name, is_active FROM Table_India;").fetchall()
        self.assertEqual(ind_rows, [("Aarav", "A")])

        usa_rows = self.db.conn.execute("SELECT member_name, is_active FROM Table_USA;").fetchall()
        self.assertEqual(usa_rows, [("Bob", "A")])

    def test_late_arriving_file_protection(self):
        """Verify older files loaded after newer files do NOT overwrite current profiles."""
        newer_rec = MemberRecord(
            member_id="M100",
            member_name="Current Name",
            tier_code="PLT",
            country="USA",
            source_system="HD_FEED",
            source_file_name="feed_day2.txt",
            source_file_timestamp=self.t2,  # Jan 15
            source_row_number=1,
        )
        self.router.apply_member_updates([newer_rec], self.db)

        # Now an older file arrives out of sequence (dated Jan 10)
        older_rec = MemberRecord(
            member_id="M100",
            member_name="Old Stale Name",
            tier_code="SLV",
            country="USA",
            source_system="HD_FEED",
            source_file_name="feed_day1.txt",
            source_file_timestamp=self.t1,  # Jan 10
            source_row_number=1,
        )
        summary = self.router.apply_member_updates([older_rec], self.db)
        self.assertEqual(summary["skipped_late"], 1)

        # Confirm data in Table_USA did not regress to old info
        row = self.db.conn.execute("SELECT member_name, tier_code FROM Table_USA WHERE member_id = 'M100';").fetchone()
        self.assertEqual(row, ("Current Name", "PLT"))

    def test_country_move_handling(self):
        """Verify member moving countries has old record marked 'I' and new record created 'A'."""
        # Initial state: Member in India on Jan 10
        rec_india = MemberRecord(
            member_id="MOVE99",
            member_name="Priya",
            country="India",
            tier_code="GLD",
            source_system="HD_FEED",
            source_file_name="feed_day1.txt",
            source_file_timestamp=self.t1,
            source_row_number=1,
        )
        self.router.apply_member_updates([rec_india], self.db)

        ind_state = self.db.conn.execute("SELECT is_active FROM Table_India WHERE member_id = 'MOVE99';").fetchone()
        self.assertEqual(ind_state, ("A",))

        # Member relocates to Australia on Jan 15
        rec_aus = MemberRecord(
            member_id="MOVE99",
            member_name="Priya",
            country="Australia",
            tier_code="GLD",
            source_system="HD_FEED",
            source_file_name="feed_day2.txt",
            source_file_timestamp=self.t2,
            source_row_number=1,
        )
        summary = self.router.apply_member_updates([rec_aus], self.db)
        self.assertEqual(summary["moved"], 1)

        # Previous record in Table_India is now marked Inactive ('I')
        old_ind = self.db.conn.execute("SELECT is_active FROM Table_India WHERE member_id = 'MOVE99';").fetchone()
        self.assertEqual(old_ind, ("I",))

        # New record in Table_Australia is Active ('A')
        new_aus = self.db.conn.execute("SELECT is_active FROM Table_Australia WHERE member_id = 'MOVE99';").fetchone()
        self.assertEqual(new_aus, ("A",))

        # Unified view has exactly 1 active profile for MOVE99
        active_view = self.db.conn.execute(
            "SELECT country, is_active FROM Current_Member_Profiles WHERE member_id = 'MOVE99';"
        ).fetchall()
        self.assertEqual(len(active_view), 1)
        self.assertEqual(active_view[0], ("Australia", "A"))

    def test_quarantine_records_routed_to_quarantine_table(self):
        """Verify quarantined records do not enter Gold tables."""
        quarantine_rec = MemberRecord(
            member_id="",
            member_name="Unknown",
            country="USA",
            source_system="HD_FEED",
            source_file_name="bad.txt",
            source_file_timestamp=self.t1,
            source_row_number=1,
            validation_status=ValidationStatus.QUARANTINE,
            validation_reason="Missing member_id",
        )
        summary = self.router.apply_member_updates([quarantine_rec], self.db)
        self.assertEqual(summary["quarantined"], 1)

        quarantine_rows = self.db.conn.execute("SELECT validation_reason FROM quarantine_members;").fetchall()
        self.assertEqual(len(quarantine_rows), 1)
        self.assertEqual(quarantine_rows[0][0], "Missing member_id")


if __name__ == "__main__":
    unittest.main()
