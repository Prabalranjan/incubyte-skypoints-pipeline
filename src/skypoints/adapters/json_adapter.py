"""
Adapter for parsing semi-structured JSON redemption feeds, flattening transaction arrays,
and joining transactions with current member profiles.
"""
from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from skypoints.adapters.base import BaseAdapter
from skypoints.models.canonical import RawRecord, RedemptionRecord, ValidationStatus
from skypoints.storage.database import DatabaseManager


class JsonRedemptionAdapter(BaseAdapter):
    """
    Parses semi-structured JSON redemption feeds.
    Unpacks nested 'redemptions' array into flat RedemptionRecord models.
    """

    def __init__(self):
        super().__init__(source_system="JSON_REDEMPTION_FEED")

    def parse_file(self, file_path: Path) -> Tuple[List[RawRecord], List[RedemptionRecord]]:
        """Read and parse a JSON redemption file from disk."""
        file_path = Path(file_path)
        file_timestamp = self.extract_file_timestamp(file_path)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return self.parse_content(content, file_path.name, file_timestamp)

    def parse_content(
        self, content: str, source_file_name: str, source_file_timestamp: datetime
    ) -> Tuple[List[RawRecord], List[RedemptionRecord]]:
        """
        Parse JSON content supporting:
        - Single JSON object
        - JSON array of objects
        - Newline-delimited JSON (NDJSON)
        """
        raw_records: List[RawRecord] = []
        redemption_records: List[RedemptionRecord] = []

        cleaned_content = content.strip()
        if not cleaned_content:
            return raw_records, redemption_records

        # Capture raw payload for Bronze layer
        raw_records.append(
            RawRecord(
                source_system=self.source_system,
                source_file_name=source_file_name,
                source_file_timestamp=source_file_timestamp,
                source_row_number=1,
                raw_payload=content,
            )
        )

        # Attempt JSON parsing: either standard JSON or NDJSON
        parsed_objects: List[Dict[str, Any]] = []
        try:
            loaded = json.loads(cleaned_content)
            if isinstance(loaded, list):
                parsed_objects = loaded
            elif isinstance(loaded, dict):
                parsed_objects = [loaded]
        except json.JSONDecodeError:
            # Fallback to Newline-Delimited JSON (NDJSON)
            lines = cleaned_content.splitlines()
            for line_idx, line in enumerate(lines, start=1):
                trimmed = line.strip()
                if not trimmed:
                    continue
                try:
                    obj = json.loads(trimmed)
                    if isinstance(obj, dict):
                        parsed_objects.append(obj)
                except json.JSONDecodeError as e:
                    # Quarantine malformed JSON line
                    redemption_records.append(
                        RedemptionRecord(
                            txn_id=f"MALFORMED_LINE_{line_idx}",
                            member_id="",
                            partner="UNKNOWN",
                            miles_redeemed=0,
                            status="MALFORMED_JSON",
                            source_file_name=source_file_name,
                            source_file_timestamp=source_file_timestamp,
                            validation_status=ValidationStatus.QUARANTINE,
                            validation_reason=f"Invalid JSON syntax on line {line_idx}: {str(e)}",
                        )
                    )

        # Flatten redemptions array for each member document
        for obj in parsed_objects:
            member_id = str(obj.get("member_id", "")).strip()
            raw_feed_date = obj.get("feed_date")
            feed_date = self.parse_date(str(raw_feed_date) if raw_feed_date else None, ["%Y%m%d", "%Y-%m-%d"])

            redemptions_list = obj.get("redemptions")
            if not isinstance(redemptions_list, list):
                if not member_id:
                    continue
                # If redemptions attribute is missing or not a list
                redemption_records.append(
                    RedemptionRecord(
                        txn_id=f"NO_TXN_FOR_{member_id}",
                        member_id=member_id,
                        feed_date=feed_date,
                        partner="UNKNOWN",
                        miles_redeemed=0,
                        status="MISSING_REDEMPTIONS_ARRAY",
                        source_file_name=source_file_name,
                        source_file_timestamp=source_file_timestamp,
                        validation_status=ValidationStatus.WARNING,
                        validation_reason="Missing or non-array 'redemptions' key",
                    )
                )
                continue

            for txn in redemptions_list:
                if not isinstance(txn, dict):
                    continue

                txn_id = str(txn.get("txn_id", "")).strip()
                raw_txn_date = txn.get("txn_date")
                txn_date = self.parse_date(str(raw_txn_date) if raw_txn_date else None, ["%Y%m%d", "%Y-%m-%d"])
                partner = str(txn.get("partner", "")).strip()
                status = str(txn.get("status", "COMPLETED")).strip()
                
                # Miles parsing & validation
                raw_miles = txn.get("miles_redeemed", 0)
                try:
                    miles_redeemed = int(raw_miles)
                except (ValueError, TypeError):
                    miles_redeemed = 0

                # Data quality validation
                rec_status = ValidationStatus.VALID
                reasons = []

                if not txn_id:
                    rec_status = ValidationStatus.QUARANTINE
                    reasons.append("Missing mandatory txn_id")

                if not member_id:
                    rec_status = ValidationStatus.QUARANTINE
                    reasons.append("Missing mandatory member_id")

                if miles_redeemed < 0:
                    rec_status = ValidationStatus.WARNING if rec_status != ValidationStatus.QUARANTINE else rec_status
                    reasons.append(f"Negative miles value '{raw_miles}'")

                if raw_txn_date and not txn_date:
                    rec_status = ValidationStatus.WARNING if rec_status != ValidationStatus.QUARANTINE else rec_status
                    reasons.append(f"Unparseable txn_date '{raw_txn_date}'")

                reason_str = "; ".join(reasons) if reasons else None

                redemption_records.append(
                    RedemptionRecord(
                        txn_id=txn_id,
                        member_id=member_id,
                        feed_date=feed_date,
                        txn_date=txn_date,
                        partner=partner,
                        miles_redeemed=miles_redeemed,
                        status=status,
                        source_file_name=source_file_name,
                        source_file_timestamp=source_file_timestamp,
                        validation_status=rec_status,
                        validation_reason=reason_str,
                    )
                )

        return raw_records, redemption_records

    @staticmethod
    def load_redemptions(records: List[RedemptionRecord], db: DatabaseManager):
        """Idempotently load redemptions into Table_Redemptions."""
        valid_records = [r for r in records if r.validation_status != ValidationStatus.QUARANTINE and r.txn_id]
        db.insert_redemption_records(valid_records)

    @staticmethod
    def query_redemptions_joined_with_members(db: DatabaseManager) -> List[Dict[str, Any]]:
        """
        Execute join between Table_Redemptions and Current_Member_Profiles view.
        Retains all redemptions, marking unmatched ones with 'UNMATCHED_MEMBER'.
        """
        # Ensure view exists
        tables = db.get_table_names()
        if "Table_Redemptions" not in tables:
            return []

        # If Current_Member_Profiles view doesn't exist yet, query Table_Redemptions directly
        if "Current_Member_Profiles" not in tables:
            sql = """
                SELECT 
                    r.txn_id,
                    r.txn_date,
                    r.feed_date,
                    r.partner,
                    r.miles_redeemed,
                    r.status AS txn_status,
                    r.member_id,
                    CAST(NULL AS VARCHAR) AS member_name,
                    CAST(NULL AS VARCHAR) AS tier_code,
                    CAST(NULL AS VARCHAR) AS country,
                    'UNMATCHED_MEMBER' AS match_status
                FROM Table_Redemptions r
                ORDER BY r.txn_id;
            """
        else:
            sql = """
                SELECT 
                    r.txn_id,
                    r.txn_date,
                    r.feed_date,
                    r.partner,
                    r.miles_redeemed,
                    r.status AS txn_status,
                    r.member_id,
                    m.member_name,
                    m.tier_code,
                    m.country,
                    CASE 
                        WHEN m.member_id IS NULL THEN 'UNMATCHED_MEMBER' 
                        ELSE 'MATCHED' 
                    END AS match_status
                FROM Table_Redemptions r
                LEFT JOIN Current_Member_Profiles m ON r.member_id = m.member_id
                ORDER BY r.txn_id;
            """

        df = db.conn.execute(sql).df()
        return df.to_dict(orient="records")
