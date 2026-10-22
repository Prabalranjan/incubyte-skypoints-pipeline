"""Unit tests for JsonRedemptionAdapter and profile join logic."""
import unittest
from datetime import date, datetime, timezone
import json
from skypoints.adapters import JsonRedemptionAdapter
from skypoints.models import MemberRecord, RedemptionRecord, ValidationStatus
from skypoints.storage import DatabaseManager
from skypoints.router import CountryRouter


class TestJsonRedemptionAdapter(unittest.TestCase):
    """Test suite for JSON redemption feed flattening, validation, and joining."""

    def setUp(self):
        self.adapter = JsonRedemptionAdapter()
        self.db = DatabaseManager(":memory:")
        self.now = datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.db.close()

    def test_parse_single_member_document_pdf_sample(self):
        """Verify parsing of the exact JSON sample structure from assessment PDF."""
        content = """{
  "member_id": "223457",
  "feed_date": "20240115",
  "redemptions": [
    {"txn_id": "RX10091", "txn_date": "20240110", "partner": "AeroLink", "miles_redeemed": 12000, "status": "COMPLETED"},
    {"txn_id": "RX10092", "txn_date": "20240113", "partner": "SkyPoints", "miles_redeemed": 5000, "status": "PENDING"}
  ]
}"""
        raw_recs, redemptions = self.adapter.parse_content(content, "redemptions.json", self.now)

        self.assertEqual(len(raw_recs), 1)
        self.assertEqual(len(redemptions), 2)

        # First transaction
        t1 = redemptions[0]
        self.assertEqual(t1.txn_id, "RX10091")
        self.assertEqual(t1.member_id, "223457")
        self.assertEqual(t1.feed_date, date(2024, 1, 15))
        self.assertEqual(t1.txn_date, date(2024, 1, 10))
        self.assertEqual(t1.partner, "AeroLink")
        self.assertEqual(t1.miles_redeemed, 12000)
        self.assertEqual(t1.status, "COMPLETED")
        self.assertEqual(t1.validation_status, ValidationStatus.VALID)

        # Second transaction
        t2 = redemptions[1]
        self.assertEqual(t2.txn_id, "RX10092")
        self.assertEqual(t2.member_id, "223457")
        self.assertEqual(t2.txn_date, date(2024, 1, 13))
        self.assertEqual(t2.partner, "SkyPoints")
        self.assertEqual(t2.miles_redeemed, 5000)
        self.assertEqual(t2.status, "PENDING")

    def test_parse_json_array_of_members(self):
        """Verify parsing when root is a JSON array of member documents."""
        data = [
            {
                "member_id": "M01",
                "feed_date": "2024-01-15",
                "redemptions": [
                    {"txn_id": "TXN_A", "txn_date": "2024-01-12", "partner": "Airline1", "miles_redeemed": 1000}
                ],
            },
            {
                "member_id": "M02",
                "feed_date": "2024-01-15",
                "redemptions": [
                    {"txn_id": "TXN_B", "txn_date": "2024-01-14", "partner": "Airline2", "miles_redeemed": 2000}
                ],
            },
        ]
        raw_recs, redemptions = self.adapter.parse_content(json.dumps(data), "batch.json", self.now)
        self.assertEqual(len(redemptions), 2)
        self.assertEqual(redemptions[0].txn_id, "TXN_A")
        self.assertEqual(redemptions[1].txn_id, "TXN_B")

    def test_parse_newline_delimited_json(self):
        """Verify parsing of Newline-Delimited JSON (NDJSON)."""
        content = """{"member_id": "M01", "redemptions": [{"txn_id": "TX1", "partner": "P1", "miles_redeemed": 100}]}
{"member_id": "M02", "redemptions": [{"txn_id": "TX2", "partner": "P2", "miles_redeemed": 200}]}
"""
        raw_recs, redemptions = self.adapter.parse_content(content, "stream.ndjson", self.now)
        self.assertEqual(len(redemptions), 2)
        self.assertEqual(redemptions[0].txn_id, "TX1")
        self.assertEqual(redemptions[1].txn_id, "TX2")

    def test_quarantine_missing_identifiers(self):
        """Verify missing txn_id or member_id flags quarantine."""
        content = """{
  "member_id": "",
  "redemptions": [
    {"txn_id": "", "partner": "AeroLink", "miles_redeemed": 1000}
  ]
}"""
        raw_recs, redemptions = self.adapter.parse_content(content, "bad.json", self.now)
        self.assertEqual(len(redemptions), 1)
        self.assertEqual(redemptions[0].validation_status, ValidationStatus.QUARANTINE)

    def test_malformed_json_syntax_quarantined_without_crash(self):
        """Verify malformed JSON syntax is caught and quarantined safely."""
        bad_syntax = "{ 'invalid_json': True, missing_quotes }"
        raw_recs, redemptions = self.adapter.parse_content(bad_syntax, "corrupt.json", self.now)
        self.assertEqual(len(redemptions), 1)
        self.assertEqual(redemptions[0].validation_status, ValidationStatus.QUARANTINE)
        self.assertIn("Invalid JSON syntax", redemptions[0].validation_reason)

    def test_idempotent_reprocessing(self):
        """Verify replaying the same transaction does not duplicate in Table_Redemptions."""
        content = """{
  "member_id": "M01",
  "redemptions": [
    {"txn_id": "REPLAY_01", "partner": "Airline1", "miles_redeemed": 5000, "status": "PENDING"}
  ]
}"""
        raw, recs = self.adapter.parse_content(content, "f1.json", self.now)
        self.adapter.load_redemptions(recs, self.db)

        # Replay same transaction with updated status
        content_updated = """{
  "member_id": "M01",
  "redemptions": [
    {"txn_id": "REPLAY_01", "partner": "Airline1", "miles_redeemed": 5000, "status": "COMPLETED"}
  ]
}"""
        raw2, recs2 = self.adapter.parse_content(content_updated, "f2.json", self.now)
        self.adapter.load_redemptions(recs2, self.db)

        rows = self.db.conn.execute("SELECT txn_id, status FROM Table_Redemptions;").fetchall()
        # Exactly 1 row (no duplication), status updated to COMPLETED
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], ("REPLAY_01", "COMPLETED"))

    def test_profile_join_matched_and_unmatched(self):
        """Verify joining redemptions with active member profiles."""
        # 1. Setup a member in Table_USA
        router = CountryRouter()
        elena = MemberRecord(
            member_id="223457",
            member_name="Elena",
            tier_code="GLD",
            country="USA",
            source_system="HD_FEED",
            source_file_name="hd.txt",
            source_file_timestamp=self.now,
            source_row_number=1,
        )
        router.apply_member_updates([elena], self.db)

        # 2. Insert two redemptions: one for Elena, one for unknown member
        content = """[
  {
    "member_id": "223457",
    "redemptions": [
      {"txn_id": "TX_MATCHED", "txn_date": "2024-01-10", "partner": "AeroLink", "miles_redeemed": 1000}
    ]
  },
  {
    "member_id": "UNKNOWN_999",
    "redemptions": [
      {"txn_id": "TX_UNMATCHED", "txn_date": "2024-01-11", "partner": "SkyPoints", "miles_redeemed": 2000}
    ]
  }
]"""
        raw, redemptions = self.adapter.parse_content(content, "test.json", self.now)
        self.adapter.load_redemptions(redemptions, self.db)

        # 3. Query joined view
        joined_rows = self.adapter.query_redemptions_joined_with_members(self.db)
        self.assertEqual(len(joined_rows), 2)

        # Row 1: Matched to Elena
        r1 = joined_rows[0]
        self.assertEqual(r1["txn_id"], "TX_MATCHED")
        self.assertEqual(r1["member_name"], "Elena")
        self.assertEqual(r1["tier_code"], "GLD")
        self.assertEqual(r1["country"], "USA")
        self.assertEqual(r1["match_status"], "MATCHED")

        # Row 2: Unmatched
        r2 = joined_rows[1]
        self.assertEqual(r2["txn_id"], "TX_UNMATCHED")
        self.assertEqual(r2["member_id"], "UNKNOWN_999")
        self.assertIsNone(r2["member_name"])
        self.assertEqual(r2["match_status"], "UNMATCHED_MEMBER")


if __name__ == "__main__":
    unittest.main()
