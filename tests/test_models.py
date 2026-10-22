"""Unit tests for canonical data models."""
import unittest
from datetime import date, datetime, timezone
from skypoints.models import (
    MemberRecord,
    RedemptionRecord,
    RawRecord,
    ValidationStatus,
)


class TestCanonicalModels(unittest.TestCase):
    """Test suite for canonical data model validation and serialization."""

    def test_member_record_preserves_leading_zeros(self):
        """Verify member_id retains leading zeros as string."""
        record = MemberRecord(
            member_id="000123",
            member_name="  Alice Smith  ",
            enrollment_date=date(2022, 1, 15),
            source_system="HD_FEED",
            source_file_name="feed.txt",
            source_file_timestamp=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            source_row_number=1,
        )
        self.assertEqual(record.member_id, "000123")
        self.assertEqual(record.member_name, "Alice Smith")
        self.assertEqual(record.validation_status, ValidationStatus.VALID)

    def test_member_record_serialization(self):
        """Verify to_dict produces expected keys and types."""
        now = datetime.now(timezone.utc)
        record = MemberRecord(
            member_id="M100",
            member_name="Bob Jones",
            country="India",
            age=35,
            stale_member=False,
            source_system="IND_CSV",
            source_file_name="IND.csv",
            source_file_timestamp=now,
            source_row_number=2,
            validation_status=ValidationStatus.WARNING,
            validation_reason="Missing Post Code",
        )
        data = record.to_dict()
        self.assertEqual(data["member_id"], "M100")
        self.assertEqual(data["country"], "India")
        self.assertEqual(data["age"], 35)
        self.assertEqual(data["stale_member"], False)
        self.assertEqual(data["validation_status"], "WARNING")
        self.assertEqual(data["validation_reason"], "Missing Post Code")

    def test_redemption_record_keys(self):
        """Verify redemption model retains string keys."""
        record = RedemptionRecord(
            txn_id="TXN_999",
            member_id="00055",
            feed_date=date(2024, 2, 1),
            txn_date=date(2024, 1, 28),
            partner="Delta",
            miles_redeemed=15000,
            status="COMPLETED",
            source_file_name="redemptions.json",
            source_file_timestamp=datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(record.txn_id, "TXN_999")
        self.assertEqual(record.member_id, "00055")
        self.assertEqual(record.miles_redeemed, 15000)

    def test_raw_record_audit(self):
        """Verify raw landing model stores payload verbatim."""
        now = datetime.now(timezone.utc)
        record = RawRecord(
            source_system="HD_FEED",
            source_file_name="feed.txt",
            source_file_timestamp=now,
            source_row_number=1,
            raw_payload="D|100001|John Doe|2022-01-01|...|",
        )
        self.assertEqual(record.raw_payload, "D|100001|John Doe|2022-01-01|...|")
        self.assertEqual(record.source_row_number, 1)


if __name__ == "__main__":
    unittest.main()
