"""End-to-end integration tests for PipelineRunner and CLI execution."""
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
import tempfile
from skypoints.pipeline import PipelineRunner
from skypoints.storage import DatabaseManager
from skypoints.adapters import (
    HDAdapter,
    AusCsvAdapter,
    IndCsvAdapter,
    UsaCsvAdapter,
    JsonRedemptionAdapter,
)


class TestPipelineOrchestrator(unittest.TestCase):
    """Integration test suite for the complete pipeline orchestrator."""

    def setUp(self):
        self.mail_files_dir = Path(__file__).resolve().parent.parent / "Mail files"

    def test_adapter_selection(self):
        """Verify dynamic adapter selection for diverse filenames and extensions."""
        runner = PipelineRunner(db=DatabaseManager(":memory:"))

        self.assertIsInstance(runner.select_adapter_for_file(Path("members.json")), JsonRedemptionAdapter)
        self.assertIsInstance(runner.select_adapter_for_file(Path("HD_FEED.txt")), HDAdapter)
        self.assertIsInstance(runner.select_adapter_for_file(Path("AUS(Sheet1).csv")), AusCsvAdapter)
        self.assertIsInstance(runner.select_adapter_for_file(Path("IND(in).csv")), IndCsvAdapter)
        self.assertIsInstance(runner.select_adapter_for_file(Path("USA(in).csv")), UsaCsvAdapter)
        self.assertIsNone(runner.select_adapter_for_file(Path("assessment.pdf")))

    def test_end_to_end_synthetic_pipeline(self):
        """Verify full 3-layer execution from files to Bronze, Silver, Gold, and Joins."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # 1. Write H/D feed
            hd_file = tmppath / "HD_FEED_20240115.txt"
            hd_file.write_text(
                """H|Member_Name|Member_Id|Enrollment_Date|Last_Flight_Date|Tier_Code|Agent_Name|State|Country|DOB|Is_Active
D|Elena|223457|20101012|20121013|GLD|Sam|CA|USA|03051985|A
D|Ravi|223458|20101012|20121013|SLV|Sam|TN|IND|03051985|A
""",
                encoding="utf-8",
            )

            # 2. Write JSON redemption feed
            json_file = tmppath / "redemptions_20240115.json"
            json_file.write_text(
                """{
  "member_id": "223457",
  "feed_date": "20240115",
  "redemptions": [
    {"txn_id": "RX10091", "txn_date": "20240110", "partner": "AeroLink", "miles_redeemed": 12000, "status": "COMPLETED"},
    {"txn_id": "RX99999", "txn_date": "20240112", "partner": "SkyPoints", "miles_redeemed": 3000, "status": "PENDING"}
  ]
}""",
                encoding="utf-8",
            )

            # Execute pipeline
            db = DatabaseManager(":memory:")
            runner = PipelineRunner(db=db, as_of_date=date(2024, 6, 1))
            summary = runner.run_on_directory(tmppath)

            # Check metrics
            self.assertEqual(len(summary["processed_files"]), 2)
            self.assertGreater(summary["bronze"]["raw_records_landed"], 0)
            self.assertEqual(summary["silver"]["standardized_members"], 2)
            self.assertEqual(summary["gold"]["members_inserted"], 2)
            self.assertEqual(summary["redemptions"]["total_redemptions_loaded"], 2)

            # Check Country Tables
            tables = db.get_table_names()
            self.assertIn("Table_USA", tables)
            self.assertIn("Table_India", tables)
            self.assertIn("Table_Redemptions", tables)

            # Check Formatted Report Output
            report_text = runner.format_summary_report(summary)
            self.assertIn("SKYPOINTS LOYALTY DATA PIPELINE REPORT", report_text)
            self.assertIn("Table_USA", report_text)
            self.assertIn("Table_India", report_text)

    def test_live_mail_files_directory_run(self):
        """Verify pipeline execution on actual Mail files directory."""
        if self.mail_files_dir.is_dir():
            db = DatabaseManager(":memory:")
            runner = PipelineRunner(db=db, as_of_date=date(2024, 6, 1))
            summary = runner.run_on_directory(self.mail_files_dir)

            # Should process AUS, IND, USA CSVs (ignoring .pdf and .md)
            self.assertIn("AUS(Sheet1).csv", summary["processed_files"])
            self.assertIn("IND(in).csv", summary["processed_files"])
            self.assertIn("USA(in).csv", summary["processed_files"])
            self.assertGreaterEqual(summary["silver"]["standardized_members"], 9)


if __name__ == "__main__":
    unittest.main()
