"""Unit tests for derived columns enrichment (Age and Stale_Member)."""
import unittest
from datetime import date, datetime, timedelta, timezone
import duckdb
from skypoints.models import MemberRecord
from skypoints.enrichment import (
    calculate_age,
    calculate_stale_member,
    enrich_member_record,
    enrich_member_records,
    get_duckdb_age_expression,
    get_duckdb_stale_expression,
)


class TestDerivedColumns(unittest.TestCase):
    """Test suite for Age and Stale Member business logic."""

    def test_age_exact_anniversary_boundaries(self):
        """Verify Age on birthday, day before, and day after."""
        dob = date(1994, 6, 15)

        # 1 day before 30th birthday -> 29
        self.assertEqual(calculate_age(dob, as_of_date=date(2024, 6, 14)), 29)

        # On exact 30th birthday -> 30
        self.assertEqual(calculate_age(dob, as_of_date=date(2024, 6, 15)), 30)

        # 1 day after 30th birthday -> 30
        self.assertEqual(calculate_age(dob, as_of_date=date(2024, 6, 16)), 30)

    def test_age_leap_year_birthdays(self):
        """Verify Age for Feb 29 leap year births."""
        dob = date(2000, 2, 29)

        # Non-leap year: Feb 28 -> still age 0
        self.assertEqual(calculate_age(dob, as_of_date=date(2001, 2, 28)), 0)

        # Non-leap year: March 1 -> turns age 1
        self.assertEqual(calculate_age(dob, as_of_date=date(2001, 3, 1)), 1)

        # Leap year: Feb 29, 2004 -> turns age 4
        self.assertEqual(calculate_age(dob, as_of_date=date(2004, 2, 29)), 4)

    def test_age_missing_or_future_dob(self):
        """Verify None is returned when DOB is missing or in the future."""
        self.assertIsNone(calculate_age(None, as_of_date=date(2024, 1, 1)))

        future_dob = date(2030, 1, 1)
        self.assertIsNone(calculate_age(future_dob, as_of_date=date(2024, 1, 1)))

    def test_stale_member_exact_90_day_boundary(self):
        """Verify strict assessment requirement: > 90 days. 90 days = FALSE, 91 days = TRUE."""
        as_of = date(2024, 6, 1)

        # 89 days ago -> False
        flight_89 = as_of - timedelta(days=89)
        self.assertFalse(calculate_stale_member(flight_89, as_of_date=as_of))

        # Exactly 90 days ago -> False
        flight_90 = as_of - timedelta(days=90)
        self.assertFalse(calculate_stale_member(flight_90, as_of_date=as_of))

        # 91 days ago -> True
        flight_91 = as_of - timedelta(days=91)
        self.assertTrue(calculate_stale_member(flight_91, as_of_date=as_of))

        # Same day flight -> False
        self.assertFalse(calculate_stale_member(as_of, as_of_date=as_of))

    def test_stale_member_missing_date(self):
        """Verify None returned when last_flight_date is missing."""
        self.assertIsNone(calculate_stale_member(None, as_of_date=date(2024, 6, 1)))

    def test_enrich_member_record_batch(self):
        """Verify enrichment of a batch of MemberRecords."""
        now = datetime.now(timezone.utc)
        as_of = date(2024, 6, 1)

        records = [
            MemberRecord(
                member_id="M01",
                member_name="Elena",
                dob=date(1994, 6, 15),
                last_flight_date=as_of - timedelta(days=90),
                source_system="TEST",
                source_file_name="test.txt",
                source_file_timestamp=now,
                source_row_number=1,
            ),
            MemberRecord(
                member_id="M02",
                member_name="Ravi",
                dob=date(1990, 1, 1),
                last_flight_date=as_of - timedelta(days=91),
                source_system="TEST",
                source_file_name="test.txt",
                source_file_timestamp=now,
                source_row_number=2,
            ),
        ]

        enrich_member_records(records, as_of_date=as_of)

        # Elena: not had 30th birthday yet -> age 29, exactly 90 days -> not stale
        self.assertEqual(records[0].age, 29)
        self.assertEqual(records[0].stale_member, False)

        # Ravi: has had 34th birthday -> age 34, 91 days -> stale
        self.assertEqual(records[1].age, 34)
        self.assertEqual(records[1].stale_member, True)

    def test_duckdb_sql_derived_expressions(self):
        """Verify DuckDB SQL expressions produce identical results to Python logic."""
        con = duckdb.connect(":memory:")
        con.execute("""
            CREATE TABLE members_test (
                id VARCHAR,
                dob DATE,
                last_flight_date DATE
            );
            INSERT INTO members_test VALUES
                ('1', DATE '1994-06-15', DATE '2024-03-03'), -- 90 days before 2024-06-01
                ('2', DATE '1994-06-15', DATE '2024-03-02'), -- 91 days before 2024-06-01
                ('3', NULL, NULL);
        """)

        as_of_str = "DATE '2024-06-01'"
        age_expr = get_duckdb_age_expression(as_of_str)
        stale_expr = get_duckdb_stale_expression(as_of_str, threshold_days=90)

        query = f"""
            SELECT id, {age_expr} AS age, {stale_expr} AS stale_member
            FROM members_test
            ORDER BY id;
        """
        results = con.execute(query).fetchall()

        # Row 1: age 29, stale False
        self.assertEqual(results[0], ("1", 29, False))
        # Row 2: age 29, stale True
        self.assertEqual(results[1], ("2", 29, True))
        # Row 3: age None, stale None
        self.assertEqual(results[2], ("3", None, None))
        con.close()


if __name__ == "__main__":
    unittest.main()
