"""
Dynamic country router, state resolution, late-arriving file protection, and country moves.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Tuple, Any
from skypoints.models.canonical import MemberRecord, ValidationStatus
from skypoints.storage.database import DatabaseManager
from skypoints.enrichment.derived_columns import enrich_member_record


class CountryRouter:
    """Handles dynamic country table routing, conflict resolution, and country moves."""

    @staticmethod
    def deduplicate_and_resolve_latest(records: List[MemberRecord]) -> List[MemberRecord]:
        """
        Deduplicate within a batch/stream based on:
        1. Latest source_file_timestamp wins.
        2. Deterministic tie-breaker: largest source_row_number wins within the same file/timestamp.
        """
        grouped: Dict[str, MemberRecord] = {}

        for rec in records:
            key = rec.member_id
            if not key:
                # Retain keyless records as-is (they will be quarantined)
                continue

            if key not in grouped:
                grouped[key] = rec
            else:
                existing = grouped[key]
                # Compare (timestamp, row_number)
                existing_key = (existing.source_file_timestamp, existing.source_row_number)
                incoming_key = (rec.source_file_timestamp, rec.source_row_number)

                if incoming_key > existing_key:
                    grouped[key] = rec

        # Also include any keyless quarantine records
        keyless_quarantine = [r for r in records if not r.member_id]
        return list(grouped.values()) + keyless_quarantine

    @staticmethod
    def get_country_tables(db: DatabaseManager) -> List[str]:
        """Return list of existing dynamic country tables in the database."""
        all_tables = db.get_table_names()
        return [
            t for t in all_tables
            if t.startswith("Table_") and t not in ("Table_Redemptions", "Table_Unassigned_Country")
        ]

    def find_existing_active_member(
        self, member_id: str, db: DatabaseManager
    ) -> Optional[Tuple[str, datetime]]:
        """
        Search all active country tables for an existing active profile for member_id.
        Returns (table_name, source_file_timestamp) if found, else None.
        """
        country_tables = self.get_country_tables(db)
        for tbl in country_tables:
            query = f"SELECT source_file_timestamp FROM {tbl} WHERE member_id = ? AND is_active = 'A';"
            res = db.conn.execute(query, [member_id]).fetchall()
            if res:
                timestamp = res[0][0]
                return (tbl, timestamp)
        return None

    def apply_member_updates(
        self,
        records: List[MemberRecord],
        db: DatabaseManager,
        as_of_date: Optional[date] = None,
        threshold_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Route and apply member records to Gold country tables:
        - Resolves latest records within batch.
        - Enforces late-arriving file protection.
        - Handles country moves (deactivates old country row, inserts in new country table).
        - Quarantines invalid records into quarantine_members.
        """
        summary = {
            "total_processed": len(records),
            "inserted": 0,
            "updated": 0,
            "skipped_late": 0,
            "moved": 0,
            "quarantined": 0,
            "routed_tables": set(),
        }

        # 1. Resolve within-batch latest records
        resolved_records = self.deduplicate_and_resolve_latest(records)

        for rec in resolved_records:
            # Check quarantine status
            if rec.validation_status == ValidationStatus.QUARANTINE or not rec.member_id:
                db.insert_member_records("quarantine_members", [rec])
                summary["quarantined"] += 1
                continue

            # Ensure derived columns are enriched
            enrich_member_record(rec, as_of_date=as_of_date, threshold_days=threshold_days)

            # Determine target country table
            target_table = db.create_country_table_if_not_exists(rec.country)

            # Check if active member already exists anywhere in the database
            existing = self.find_existing_active_member(rec.member_id, db)

            if existing is None:
                # Case 1: Brand new member
                rec.is_active = "A"
                db.insert_member_records(target_table, [rec])
                summary["inserted"] += 1
                summary["routed_tables"].add(target_table)
            else:
                existing_table, existing_timestamp = existing

                # Case 2: Late-arriving older file protection
                # Convert timestamps to comparable UTC if needed
                if rec.source_file_timestamp < existing_timestamp.replace(tzinfo=rec.source_file_timestamp.tzinfo):
                    # Incoming record is older than the current profile in DB
                    summary["skipped_late"] += 1
                    continue

                # Case 3: Country Move
                if target_table != existing_table:
                    # Deactivate in previous country table
                    db.conn.execute(
                        f"UPDATE {existing_table} SET is_active = 'I' WHERE member_id = ?;",
                        [rec.member_id],
                    )
                    rec.is_active = "A"
                    db.insert_member_records(target_table, [rec])
                    summary["moved"] += 1
                    summary["routed_tables"].add(target_table)
                else:
                    # Case 4: Update within same country table
                    rec.is_active = "A"
                    db.insert_member_records(target_table, [rec])
                    summary["updated"] += 1
                    summary["routed_tables"].add(target_table)

        # Refresh unified view for downstream querying
        self.create_unified_members_view(db)
        return summary

    def create_unified_members_view(self, db: DatabaseManager):
        """Create or replace a unified view of all active members across country tables."""
        country_tables = self.get_country_tables(db)
        if not country_tables:
            return

        union_queries = [
            f"SELECT member_id, member_name, enrollment_date, last_flight_date, tier_code, agent_name, state, country, post_code, dob, is_active, age, stale_member, source_system, source_file_name, source_file_timestamp, source_row_number, ingested_at, validation_status FROM {tbl} WHERE is_active = 'A'"
            for tbl in country_tables
        ]
        full_sql = f"CREATE OR REPLACE VIEW Current_Member_Profiles AS {' UNION ALL '.join(union_queries)};"
        db.conn.execute(full_sql)
