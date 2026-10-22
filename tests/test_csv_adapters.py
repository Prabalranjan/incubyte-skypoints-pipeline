"""Unit tests for country CSV adapters (Australia, India, and USA)."""
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from skypoints.adapters import (
    AusCsvAdapter,
    IndCsvAdapter,
    UsaCsvAdapter,
    get_csv_adapter_for_file,
)
from skypoints.models import ValidationStatus
from skypoints.storage import DatabaseManager


class TestCountryCsvAdapters(unittest.TestCase):
    """Test suite for country-specific CSV adapters."""

    def setUp(self):
        self.now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        self.mail_files_dir = Path(__file__).resolve().parent.parent / "Mail files"

    def test_aus_csv_adapter_synthetic(self):
        """Verify Australia CSV adapter handling of 'NULL' DOB and invalid month."""
        content = """Unique ID,Member Name,Tier Type,Date of Birth,Date of Enrollment,Date of Flight
1,Mike,PLT,NULL,2022-05-11,2022-08-01
2,Jonnathan,GLD,1997-12-13,2021-13-13,2022-01-05
3,Cristina,SLV,1998-03-12,2022-03-12,2022-03-20
"""
        adapter = AusCsvAdapter()
        raw_recs, member_recs = adapter.parse_content(content, "AUS.csv", self.now)

        self.assertEqual(len(raw_recs), 4)  # 1 header + 3 data lines
        self.assertEqual(len(member_recs), 3)

        # Row 1: Mike with literal "NULL" in DOB
        mike = member_recs[0]
        self.assertEqual(mike.member_id, "1")
        self.assertEqual(mike.member_name, "Mike")
        self.assertIsNone(mike.dob)  # "NULL" converted to None
        self.assertEqual(mike.enrollment_date, date(2022, 5, 11))
        self.assertEqual(mike.last_flight_date, date(2022, 8, 1))
        self.assertEqual(mike.country, "Australia")
        self.assertEqual(mike.validation_status, ValidationStatus.VALID)

        # Row 2: Jonnathan with invalid month 2021-13-13
        jon = member_recs[1]
        self.assertEqual(jon.member_id, "2")
        self.assertIsNone(jon.enrollment_date)  # Invalid month handled safely
        self.assertEqual(jon.validation_status, ValidationStatus.WARNING)
        self.assertIn("Unparseable Date of Enrollment", jon.validation_reason)

        # Row 3: Cristina happy path
        cristina = member_recs[2]
        self.assertEqual(cristina.dob, date(1998, 3, 12))
        self.assertEqual(cristina.enrollment_date, date(2022, 3, 12))
        self.assertEqual(cristina.last_flight_date, date(2022, 3, 20))
        self.assertEqual(cristina.validation_status, ValidationStatus.VALID)

    def test_ind_csv_adapter_synthetic(self):
        """Verify India CSV adapter handling of slash dates and field mappings."""
        content = """ID,Name,DOB,TierCode,EnrollmentDate,Individual or Corporate,Flight Date
1,Vikas,12/1/1998,SLV,1/1/2022,I,6/15/2022
2,Rahul,8/13/1982,GLD,3/5/2022,C,3/10/2022
"""
        adapter = IndCsvAdapter()
        raw_recs, member_recs = adapter.parse_content(content, "IND.csv", self.now)

        self.assertEqual(len(raw_recs), 3)
        self.assertEqual(len(member_recs), 2)

        vikas = member_recs[0]
        self.assertEqual(vikas.member_id, "1")
        self.assertEqual(vikas.member_name, "Vikas")
        self.assertEqual(vikas.dob, date(1998, 12, 1))
        self.assertEqual(vikas.enrollment_date, date(2022, 1, 1))
        self.assertEqual(vikas.last_flight_date, date(2022, 6, 15))
        self.assertEqual(vikas.tier_code, "SLV")
        self.assertEqual(vikas.country, "India")
        self.assertEqual(vikas.validation_status, ValidationStatus.VALID)

    def test_usa_csv_adapter_compact_dates(self):
        """Verify USA CSV adapter compact [M]MDDYYYY date parsing and missing DOB."""
        adapter = UsaCsvAdapter()
        # Test compact date static method
        self.assertEqual(adapter.parse_usa_compact_date("6152022"), date(2022, 6, 15))
        self.assertEqual(adapter.parse_usa_compact_date("8202022"), date(2022, 8, 20))
        self.assertEqual(adapter.parse_usa_compact_date("1052022"), date(2022, 1, 5))
        self.assertEqual(adapter.parse_usa_compact_date("12282021"), date(2021, 12, 28))

        content = """ID,Name,TierCode,EnrollmentDate,FlightDate
1,Sam,PLT,6152022,8202022
2,John,SLV,1052022,1152022
"""
        raw_recs, member_recs = adapter.parse_content(content, "USA.csv", self.now)
        self.assertEqual(len(member_recs), 2)

        sam = member_recs[0]
        self.assertEqual(sam.member_id, "1")
        self.assertEqual(sam.member_name, "Sam")
        self.assertEqual(sam.enrollment_date, date(2022, 6, 15))
        self.assertEqual(sam.last_flight_date, date(2022, 8, 20))
        self.assertIsNone(sam.dob)  # Missing from USA CSV schema
        self.assertEqual(sam.country, "USA")
        self.assertEqual(sam.validation_status, ValidationStatus.VALID)

    def test_adapter_factory(self):
        """Verify get_csv_adapter_for_file returns correct adapter instances."""
        self.assertIsInstance(get_csv_adapter_for_file("AUS(Sheet1).csv"), AusCsvAdapter)
        self.assertIsInstance(get_csv_adapter_for_file("IND(in).csv"), IndCsvAdapter)
        self.assertIsInstance(get_csv_adapter_for_file("USA(in).csv"), UsaCsvAdapter)
        with self.assertRaises(ValueError):
            get_csv_adapter_for_file("UNKNOWN.csv")

    def test_live_assessment_files_parsing(self):
        """Verify parsing of actual sample files in Mail files directory."""
        aus_file = self.mail_files_dir / "AUS(Sheet1).csv"
        ind_file = self.mail_files_dir / "IND(in).csv"
        usa_file = self.mail_files_dir / "USA(in).csv"

        if aus_file.exists():
            adapter = AusCsvAdapter()
            raw, members = adapter.parse_file(aus_file)
            self.assertEqual(len(members), 3)

        if ind_file.exists():
            adapter = IndCsvAdapter()
            raw, members = adapter.parse_file(ind_file)
            self.assertEqual(len(members), 3)

        if usa_file.exists():
            adapter = UsaCsvAdapter()
            raw, members = adapter.parse_file(usa_file)
            self.assertEqual(len(members), 3)

    def test_database_staging_integration(self):
        """Verify parsed CSV records insert cleanly into DuckDB staging."""
        adapter = IndCsvAdapter()
        content = """ID,Name,DOB,TierCode,EnrollmentDate,Individual or Corporate,Flight Date
1,Vikas,12/1/1998,SLV,1/1/2022,I,6/15/2022
"""
        raw_recs, member_recs = adapter.parse_content(content, "IND.csv", self.now)
        db = DatabaseManager(":memory:")
        db.insert_raw_records(raw_recs)
        db.insert_member_records("staging_members", member_recs)

        rows = db.conn.execute("SELECT member_id, member_name, country FROM staging_members WHERE source_system = 'IND_CSV';").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], ("1", "Vikas", "India"))
        db.close()


if __name__ == "__main__":
    unittest.main()
