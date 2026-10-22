"""
Adapter for parsing authoritative pipe-delimited Header/Detail (H/D) feeds.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Tuple
from skypoints.adapters.base import BaseAdapter
from skypoints.models.canonical import RawRecord, MemberRecord, ValidationStatus


class HDAdapter(BaseAdapter):
    """Parses pipe-delimited H/D loyalty files into RawRecord and MemberRecord models."""

    def __init__(self):
        super().__init__(source_system="HD_FEED")

    def parse_file(self, file_path: Path) -> Tuple[List[RawRecord], List[MemberRecord]]:
        """Read and parse an H/D flat file from disk."""
        file_path = Path(file_path)
        file_timestamp = self.extract_file_timestamp(file_path)

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return self.parse_content(content, file_path.name, file_timestamp)

    def parse_content(
        self, content: str, source_file_name: str, source_file_timestamp: datetime
    ) -> Tuple[List[RawRecord], List[MemberRecord]]:
        """Parse raw text content from an H/D feed."""
        raw_records: List[RawRecord] = []
        member_records: List[MemberRecord] = []

        lines = content.splitlines()
        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue

            # Always capture in Bronze landing
            raw_rec = RawRecord(
                source_system=self.source_system,
                source_file_name=source_file_name,
                source_file_timestamp=source_file_timestamp,
                source_row_number=idx,
                raw_payload=raw_line,
            )
            raw_records.append(raw_rec)

            tokens = [t.strip() for t in raw_line.split("|")]
            record_type = tokens[0].upper() if tokens else ""

            # Ignore Header line ('H') for member profiles
            if record_type == "H":
                continue

            if record_type == "D":
                member_rec = self._parse_detail_row(
                    tokens,
                    row_number=idx,
                    source_file_name=source_file_name,
                    source_file_timestamp=source_file_timestamp,
                )
                member_records.append(member_rec)
            else:
                # Unknown record type -> Quarantine
                quarantine_rec = MemberRecord(
                    member_id="",
                    member_name="",
                    source_system=self.source_system,
                    source_file_name=source_file_name,
                    source_file_timestamp=source_file_timestamp,
                    source_row_number=idx,
                    validation_status=ValidationStatus.QUARANTINE,
                    validation_reason=f"Unknown record type '{record_type}' (expected 'D')",
                )
                member_records.append(quarantine_rec)

        return raw_records, member_records

    def _parse_detail_row(
        self,
        tokens: List[str],
        row_number: int,
        source_file_name: str,
        source_file_timestamp: datetime,
    ) -> MemberRecord:
        """Parse tokens of a 'D' row into a MemberRecord."""
        # Expected layout:
        # 0: D
        # 1: Member_Name
        # 2: Member_Id
        # 3: Enrollment_Date
        # 4: Last_Flight_Date
        # 5: Tier_Code
        # 6: Agent_Name
        # 7: State
        # 8: Country
        # 9: DOB
        # 10: Is_Active
        if len(tokens) < 11:
            return MemberRecord(
                member_id=tokens[2] if len(tokens) > 2 else "",
                member_name=tokens[1] if len(tokens) > 1 else "",
                source_system=self.source_system,
                source_file_name=source_file_name,
                source_file_timestamp=source_file_timestamp,
                source_row_number=row_number,
                validation_status=ValidationStatus.QUARANTINE,
                validation_reason=f"Malformed H/D record: expected 11 fields, got {len(tokens)}",
            )

        member_name = tokens[1]
        member_id = tokens[2]
        enroll_raw = tokens[3]
        flight_raw = tokens[4]
        tier_code = tokens[5]
        agent_name = tokens[6]
        state = tokens[7]
        country = tokens[8]
        dob_raw = tokens[9]
        is_active = tokens[10] if tokens[10] else "A"

        # Parse dates
        enroll_date = self.parse_date(enroll_raw, ["%Y%m%d", "%Y-%m-%d"])
        flight_date = self.parse_date(flight_raw, ["%Y%m%d", "%Y-%m-%d"])
        dob_date = self.parse_date(dob_raw, ["%m%d%Y", "%d%m%Y", "%Y%m%d", "%Y-%m-%d"])

        status = ValidationStatus.VALID
        reasons = []

        if not member_id:
            status = ValidationStatus.QUARANTINE
            reasons.append("Missing mandatory member_id")

        if enroll_raw and not enroll_date:
            status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
            reasons.append(f"Unparseable Enrollment_Date '{enroll_raw}'")

        if flight_raw and not flight_date:
            status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
            reasons.append(f"Unparseable Last_Flight_Date '{flight_raw}'")

        if dob_raw and not dob_date:
            status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
            reasons.append(f"Unparseable DOB '{dob_raw}'")

        validation_reason = "; ".join(reasons) if reasons else None

        return MemberRecord(
            member_id=member_id,
            member_name=member_name,
            enrollment_date=enroll_date,
            last_flight_date=flight_date,
            tier_code=tier_code or None,
            agent_name=agent_name or None,
            state=state or None,
            country=country or None,
            post_code=None,  # Explicitly omitted in H/D file layout
            dob=dob_date,
            is_active=is_active,
            source_system=self.source_system,
            source_file_name=source_file_name,
            source_file_timestamp=source_file_timestamp,
            source_row_number=row_number,
            validation_status=status,
            validation_reason=validation_reason,
        )
