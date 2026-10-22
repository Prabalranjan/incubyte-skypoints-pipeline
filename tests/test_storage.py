"""Unit tests for DuckDB database and storage manager."""
import unittest
from datetime import datetime, timezone
from skypoints.storage import DatabaseManager
from skypoints.models import MemberRecord, RedemptionRecord, RawRecord


class TestDatabaseManager(unittest.TestCase):
    """Test suite for database initialization and operations."""

    def setUp(self):
        """Create in-memory database for testing."""
        self.db = DatabaseManager(":memory:")

    def tearDown(self):
        """Close connection."""
        self.db.close()

    def test_core_schemas_initialized(self):
        """Verify Bronze, Silver, and Gold core tables exist upon init."""
        tables = self.db.get_table_names()
        self.assertIn("raw_landing_feed", tables)
        self.assertIn("staging_members", tables)
        self.assertIn("quarantine_members", tables)
        self.assertIn("Table_Redemptions", tables)

    def test_sanitize_country_name(self):
        """Verify country name normalization and safety sanitization."""
        self.assertEqual(self.db.sanitize_country_name("IND"), "India")
        self.assertEqual(self.db.sanitize_country_name("india"), "India")
        self.assertEqual(self.db.sanitize_country_name("USA"), "USA")
        self.assertEqual(self.db.sanitize_country_name("AUS"), "Australia")
        self.assertEqual(self.db.sanitize_country_name("CAN"), "Canada")
        self.assertEqual(self.db.sanitize_country_name("PHIL"), "Philippines")
        self.assertEqual(self.db.sanitize_country_name(None), "Unassigned")
        self.assertEqual(self.db.sanitize_country_name(""), "Unassigned")
        # SQL injection or bad character protection
        self.assertEqual(self.db.sanitize_country_name("United States; DROP TABLE;"), "United_States_Drop_Table")

    def test_dynamic_country_table_creation(self):
        """Verify dynamic Table_<Country> creation is safe and idempotent."""
        table_ind = self.db.create_country_table_if_not_exists("IND")
        self.assertEqual(table_ind, "Table_India")
        self.assertIn("Table_India", self.db.get_table_names())

        # Calling again should not raise error (idempotent)
        table_ind_again = self.db.create_country_table_if_not_exists("IND")
        self.assertEqual(table_ind_again, "Table_India")

        # Dynamic new country
        table_can = self.db.create_country_table_if_not_exists("Canada")
        self.assertEqual(table_can, "Table_Canada")
        self.assertIn("Table_Canada", self.db.get_table_names())

    def test_insert_member_records(self):
        """Verify inserting member records into dynamic country table."""
        now = datetime.now(timezone.utc)
        records = [
            MemberRecord(
                member_id="M001",
                member_name="Raj Sharma",
                country="India",
                tier_code="GLD",
                age=30,
                stale_member=False,
                source_system="IND_CSV",
                source_file_name="IND.csv",
                source_file_timestamp=now,
                source_row_number=1,
            )
        ]
        self.db.insert_member_records("Table_India", records)
        rows = self.db.conn.execute("SELECT member_id, member_name, tier_code, age FROM Table_India;").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], ("M001", "Raj Sharma", "GLD", 30))

    def test_redemptions_deduplication(self):
        """Verify redemptions table enforces idempotency on txn_id."""
        now = datetime.now(timezone.utc)
        rec1 = RedemptionRecord(
            txn_id="TX100",
            member_id="M001",
            partner="Air France",
            miles_redeemed=5000,
            status="PENDING",
            source_file_name="feed.json",
            source_file_timestamp=now,
        )
        rec2_updated = RedemptionRecord(
            txn_id="TX100",
            member_id="M001",
            partner="Air France",
            miles_redeemed=5000,
            status="COMPLETED",  # Status changed to COMPLETED
            source_file_name="feed_replay.json",
            source_file_timestamp=now,
        )
        self.db.insert_redemption_records([rec1])
        # Replay updated transaction
        self.db.insert_redemption_records([rec2_updated])

        rows = self.db.conn.execute("SELECT txn_id, status FROM Table_Redemptions;").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], ("TX100", "COMPLETED"))


if __name__ == "__main__":
    unittest.main()
