"""
End-to-end pipeline orchestrator for Skypoints loyalty feeds.
Coordinates file discovery, modular adapter parsing, Bronze raw landing,
Silver staging and enrichment, Gold country routing, and redemption joins.
"""
import argparse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from skypoints.config import PipelineConfig
from skypoints.storage.database import DatabaseManager
from skypoints.models.canonical import RawRecord, MemberRecord, RedemptionRecord, ValidationStatus
from skypoints.adapters.hd_adapter import HDAdapter
from skypoints.adapters.csv_adapter import (
    AusCsvAdapter,
    IndCsvAdapter,
    UsaCsvAdapter,
    get_csv_adapter_for_file,
)
from skypoints.adapters.json_adapter import JsonRedemptionAdapter
from skypoints.enrichment.derived_columns import enrich_member_records
from skypoints.router.table_router import CountryRouter


class PipelineRunner:
    """Orchestrates end-to-end execution of the 3-Layer Medallion loyalty pipeline."""

    SUPPORTED_EXTENSIONS = {".csv", ".txt", ".json", ".ndjson", ".dat"}

    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        config: Optional[PipelineConfig] = None,
        as_of_date: Optional[date] = None,
        stale_threshold_days: int = 90,
    ):
        self.config = config or PipelineConfig()
        self.db = db or DatabaseManager(self.config.database_path)
        self.as_of_date = as_of_date or date.today()
        self.stale_threshold_days = stale_threshold_days
        self.router = CountryRouter()

    def select_adapter_for_file(self, file_path: Path):
        """Inspect file extension and name to return the appropriate adapter."""
        name_lower = file_path.name.lower()
        suffix = file_path.suffix.lower()

        if suffix in (".json", ".ndjson"):
            return JsonRedemptionAdapter()
        elif suffix in (".txt", ".dat") or "hd" in name_lower or "pipe" in name_lower:
            return HDAdapter()
        elif suffix == ".csv":
            try:
                return get_csv_adapter_for_file(file_path.name)
            except ValueError:
                # Default to Australia or generic inspection
                return AusCsvAdapter()

        return None

    def run_on_directory(self, directory_path: Path) -> Dict[str, Any]:
        """Discover and process all supported feed files in a directory."""
        directory_path = Path(directory_path)
        if not directory_path.is_dir():
            raise FileNotFoundError(f"Input directory not found: {directory_path}")

        files_to_process = sorted(
            [f for f in directory_path.iterdir() if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS],
            key=lambda p: p.name,
        )

        return self.run_on_files(files_to_process)

    def run_on_files(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Execute the pipeline across an explicit list of files."""
        processed_files: List[str] = []
        all_raw_records: List[RawRecord] = []
        all_member_records: List[MemberRecord] = []
        all_redemptions: List[RedemptionRecord] = []

        # 1. Ingestion Stage (Adapters)
        for fpath in file_paths:
            adapter = self.select_adapter_for_file(fpath)
            if adapter is None:
                continue

            processed_files.append(fpath.name)
            if isinstance(adapter, JsonRedemptionAdapter):
                raws, redemptions = adapter.parse_file(fpath)
                all_raw_records.extend(raws)
                all_redemptions.extend(redemptions)
            else:
                raws, members = adapter.parse_file(fpath)
                all_raw_records.extend(raws)
                all_member_records.extend(members)

        # 2. Bronze Layer: Raw Landing
        if all_raw_records:
            self.db.insert_raw_records(all_raw_records)

        # 3. Silver Layer: Staging & Enrichment
        if all_member_records:
            # Audit staging table receives all member records
            self.db.insert_member_records("staging_members", all_member_records)
            # Apply derived Age and Stale_Member columns
            enrich_member_records(
                all_member_records, as_of_date=self.as_of_date, threshold_days=self.stale_threshold_days
            )

        # 4. Gold Layer: Member State Resolution, Dynamic Routing & Moves
        routing_summary = self.router.apply_member_updates(
            all_member_records, self.db, as_of_date=self.as_of_date, threshold_days=self.stale_threshold_days
        )

        # 5. Gold Layer: Redemptions Landing & Deduplication
        if all_redemptions:
            JsonRedemptionAdapter.load_redemptions(all_redemptions, self.db)

        # 6. Analytics: Query Profile Joins
        joined_transactions = JsonRedemptionAdapter.query_redemptions_joined_with_members(self.db)

        # 7. Compile Final Execution & Audit Metrics
        summary = self._compile_metrics(
            processed_files=processed_files,
            raw_count=len(all_raw_records),
            member_count=len(all_member_records),
            routing_summary=routing_summary,
            redemptions_count=len(all_redemptions),
            joined_transactions=joined_transactions,
        )

        return summary

    def _compile_metrics(
        self,
        processed_files: List[str],
        raw_count: int,
        member_count: int,
        routing_summary: Dict[str, Any],
        redemptions_count: int,
        joined_transactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Aggregate counts from the database tables into a clean execution report."""
        # Query active counts from all Table_<Country>
        country_counts = {}
        for tbl in self.router.get_country_tables(self.db):
            count = self.db.conn.execute(f"SELECT COUNT(*) FROM {tbl} WHERE is_active = 'A';").fetchone()[0]
            country_counts[tbl] = count

        # Unified active count
        total_active = 0
        if "Current_Member_Profiles" in self.db.get_table_names():
            total_active = self.db.conn.execute("SELECT COUNT(*) FROM Current_Member_Profiles;").fetchone()[0]

        # Match counts on transactions
        matched_txns = sum(1 for t in joined_transactions if t.get("match_status") == "MATCHED")
        unmatched_txns = sum(1 for t in joined_transactions if t.get("match_status") == "UNMATCHED_MEMBER")

        return {
            "execution_date": date.today().isoformat(),
            "as_of_date": self.as_of_date.isoformat(),
            "processed_files": processed_files,
            "bronze": {
                "raw_records_landed": raw_count,
            },
            "silver": {
                "standardized_members": member_count,
                "quarantined_records": routing_summary.get("quarantined", 0),
            },
            "gold": {
                "members_inserted": routing_summary.get("inserted", 0),
                "members_updated": routing_summary.get("updated", 0),
                "members_moved": routing_summary.get("moved", 0),
                "skipped_late_files": routing_summary.get("skipped_late", 0),
                "country_tables": country_counts,
                "total_active_members": total_active,
            },
            "redemptions": {
                "total_redemptions_loaded": redemptions_count,
                "matched_to_profile": matched_txns,
                "unmatched_retained": unmatched_txns,
            },
        }

    def format_summary_report(self, summary: Dict[str, Any]) -> str:
        """Render metrics as an elegant CLI terminal report."""
        files_str = ", ".join(summary["processed_files"]) if summary["processed_files"] else "None"
        country_lines = "\n".join(
            f"    - {tbl}: {cnt} active members" for tbl, cnt in summary["gold"]["country_tables"].items()
        ) or "    - No country tables instantiated"

        report = f"""
======================================================================
               SKYPOINTS LOYALTY DATA PIPELINE REPORT                 
======================================================================
Execution Timestamp : {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
Reference As-Of Date: {summary["as_of_date"]}
Files Processed ({len(summary["processed_files"])}):
  {files_str}
----------------------------------------------------------------------
LAYER 1: BRONZE (Raw Landing)
  - Raw Records Ingested : {summary["bronze"]["raw_records_landed"]}
----------------------------------------------------------------------
LAYER 2: SILVER (Staging & Data Quality)
  - Members Standardized : {summary["silver"]["standardized_members"]}
  - Quarantined Records  : {summary["silver"]["quarantined_records"]}
----------------------------------------------------------------------
LAYER 3: GOLD (Country Tables & Member State)
  - New Members Inserted : {summary["gold"]["members_inserted"]}
  - Profile Updates      : {summary["gold"]["members_updated"]}
  - Country Moves Handled: {summary["gold"]["members_moved"]}
  - Late Files Protected : {summary["gold"]["skipped_late_files"]}
  - Dynamic Target Tables:
{country_lines}
  - Total Active Profiles: {summary["gold"]["total_active_members"]}
----------------------------------------------------------------------
TRANSACTIONS (Redemption Feed & Join)
  - Redemptions Loaded   : {summary["redemptions"]["total_redemptions_loaded"]}
  - Matched to Member    : {summary["redemptions"]["matched_to_profile"]}
  - Unmatched (Retained) : {summary["redemptions"]["unmatched_retained"]}
======================================================================
"""
        return report.strip()


def main():
    """Command Line Interface entry point."""
    parser = argparse.ArgumentParser(description="Skypoints Loyalty Data Pipeline CLI")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="Mail files",
        help="Path to folder containing source data files (default: 'Mail files')",
    )
    parser.add_argument(
        "--as-of-date",
        type=str,
        default=None,
        help="Reference date for Age and Stale_Member calculation (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=":memory:",
        help="Path to persistent DuckDB database file (default: in-memory)",
    )

    args = parser.parse_args()

    as_of = None
    if args.as_of_date:
        as_of = datetime.strptime(args.as_of_date, "%Y-%m-%d").date()

    db = DatabaseManager(args.db_path)
    runner = PipelineRunner(db=db, as_of_date=as_of)

    input_path = Path(args.input_dir)
    print(f"Starting Skypoints Data Pipeline processing for directory: {input_path}...")
    summary = runner.run_on_directory(input_path)
    print(runner.format_summary_report(summary))


if __name__ == "__main__":
    main()
