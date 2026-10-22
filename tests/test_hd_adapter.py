"""Unit tests for HDAdapter (Header/Detail pipe-delimited feed)."""
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
import tempfile
from skypoints.adapters import HDAdapter
from skypoints.models import ValidationStatus
from skypoints.storage import DatabaseManager


class TestHDAdapter(unittest.TestCase):
    """Test suite for pipe-delimited H/D feed ingestion."""

    def setUp(self):
        self.adapter = HDAdapter()
        self.now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    def test_parse_happy_path_feed(self):
        """Verify standard H/D feed content with header and detail rows."""
        content = """H|Member_Name|Member_Id|Enrollment_Date|Last_Flight_Date|Tier_Code|Agent_Name|State|Country|DOB|Is_Active
D|Elena|223457|20101012|20121013|GLD|Sam|CA|USA|03051985|A
D|Ravi|003458|20101012|20121013|SLV|Sam|TN|IND|03051985|A
"""
        raw_recs, member_recs = self.adapter.parse_content(
            content, source_file_name="HD_FEED_20240115.txt", source_file_timestamp=self.now
        )

        # 3 raw records (1 header + 2 details)
        self.assertEqual(len(raw_recs), 3)
        self.assertEqual(raw_recs[0].source_row_number, 1)
        self.assertIn("H|Member_Name", raw_recs[0].raw_payload)

        # 2 member records (header skipped)
        self.assertEqual(len(member_recs), 2)

        # First member (Elena)
        elena = member_recs[0]
        self.assertEqual(elena.member_name, "Elena")
        self.assertEqual(elena.member_id, "223457")
        self.assertEqual(elena.enrollment_date, date(2010, 10, 12))
        self.assertEqual(elena.last_flight_date, date(2012, 10, 13))
        self.assertEqual(elena.tier_code, "GLD")
        self.assertEqual(elena.country, "USA")
        self.assertEqual(elena.dob, date(1985, 3, 5))
        self.assertEqual(elena.is_active, "A")
        self.assertIsNone(elena.post_code)  # Omitted in H/D layout
        self.assertEqual(elena.validation_status, ValidationStatus.VALID)

        # Second member (Ravi) - verify leading zero preservation
        ravi = member_recs[1]
        self.assertEqual(ravi.member_id, "003458")
        self.assertEqual(ravi.country, "IND")
        self.assertEqual(ravi.source_row_number, 3)

    def test_missing_mandatory_member_id_quarantined(self):
        """Verify row with empty member_id is tagged as QUARANTINE."""
        content = "D|Ghost||20101012|20121013|GLD|Sam|CA|USA|03051985|A"
        raw_recs, member_recs = self.adapter.parse_content(
            content, source_file_name="test.txt", source_file_timestamp=self.now
        )
        self.assertEqual(len(member_recs), 1)
        self.assertEqual(member_recs[0].validation_status, ValidationStatus.QUARANTINE)
        self.assertIn("Missing mandatory member_id", member_recs[0].validation_reason)

    def test_malformed_token_count_quarantined(self):
        """Verify row with fewer than 11 tokens is quarantined."""
        content = "D|Broken|1234|20101012|GLD"
        raw_recs, member_recs = self.adapter.parse_content(
            content, source_file_name="test.txt", source_file_timestamp=self.now
        )
        self.assertEqual(len(member_recs), 1)
        self.assertEqual(member_recs[0].validation_status, ValidationStatus.QUARANTINE)
        self.assertIn("expected 11 fields", member_recs[0].validation_reason)

    def test_unparseable_date_flagged_as_warning(self):
        """Verify invalid date string does not crash and flags warning."""
        content = "D|Alice|5555|not-a-date|20121013|GLD|Sam|CA|USA|03051985|A"
        raw_recs, member_recs = self.adapter.parse_content(
            content, source_file_name="test.txt", source_file_timestamp=self.now
        )
        self.assertEqual(len(member_recs), 1)
        self.assertEqual(member_recs[0].validation_status, ValidationStatus.WARNING)
        self.assertIsNone(member_recs[0].enrollment_date)
        self.assertIn("Unparseable Enrollment_Date", member_recs[0].validation_reason)

    def test_extract_file_timestamp(self):
        """Verify timestamp extraction from filename formats."""
        p1 = Path("HD_FEED_20240115_143000.txt")
        dt1 = self.adapter.extract_file_timestamp(p1)
        self.assertEqual(dt1, datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc))

        p2 = Path("HD_MEMBERS_20240220.txt")
        dt2 = self.adapter.extract_file_timestamp(p2)
        self.assertEqual(dt2, datetime(2024, 2, 20, 0, 0, 0, tzinfo=timezone.utc))

    def test_integration_with_database(self):
        """Verify parsed H/D records insert cleanly into DuckDB staging & raw tables."""
        content = """H|Member_Name|Member_Id|Enrollment_Date|Last_Flight_Date|Tier_Code|Agent_Name|State|Country|DOB|Is_Active
D|Mateo|223459|20101012|20121013|GLD|Sam|NCR|PHIL|03051985|A
"""
        raw_recs, member_recs = self.adapter.parse_content(
            content, source_file_name="feed.txt", source_file_timestamp=self.now
        )
        db = DatabaseManager(":memory:")
        db.insert_raw_records(raw_recs)
        db.insert_member_records("staging_members", member_recs)

        raw_rows = db.conn.execute("SELECT source_row_number, source_system FROM raw_landing_feed;").fetchall()
        self.assertEqual(len(raw_rows), 2)

        stg_rows = db.conn.execute("SELECT member_id, member_name, country FROM staging_members;").fetchall()
        self.assertEqual(len(stg_rows), 1)
        self.assertEqual(stg_rows[0], ("223459", "Mateo", "PHIL"))
        db.close()


if __name__ == "__main__":
    unittest.main()
