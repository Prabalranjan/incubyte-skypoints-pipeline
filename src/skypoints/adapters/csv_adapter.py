"""
Adapters for parsing country-specific CSV loyalty extracts (Australia, India, USA).
"""
import csv
from datetime import date, datetime, timezone
import io
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from skypoints.adapters.base import BaseAdapter
from skypoints.models.canonical import RawRecord, MemberRecord, ValidationStatus


class AusCsvAdapter(BaseAdapter):
    """
    Adapter for Australia CSV (AUS(Sheet1).csv).
    Columns: Unique ID, Member Name, Tier Type, Date of Birth, Date of Enrollment, Date of Flight
    Date format: YYYY-MM-DD
    Quirks: String literal 'NULL' in DOB, invalid month '2021-13-13'.
    """

    def __init__(self):
        super().__init__(source_system="AUS_CSV")

    def parse_file(self, file_path: Path) -> Tuple[List[RawRecord], List[MemberRecord]]:
        """Parse Australia CSV file from disk."""
        file_path = Path(file_path)
        file_timestamp = self.extract_file_timestamp(file_path)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return self.parse_content(content, file_path.name, file_timestamp)

    def parse_content(
        self, content: str, source_file_name: str, source_file_timestamp: datetime
    ) -> Tuple[List[RawRecord], List[MemberRecord]]:
        """Parse raw Australia CSV content."""
        raw_records: List[RawRecord] = []
        member_records: List[MemberRecord] = []

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            raw_records.append(
                RawRecord(
                    source_system=self.source_system,
                    source_file_name=source_file_name,
                    source_file_timestamp=source_file_timestamp,
                    source_row_number=idx,
                    raw_payload=line,
                )
            )

        reader = csv.DictReader(io.StringIO(content))
        for idx, row in enumerate(reader, start=2):
            # Normalize keys to strip whitespace
            clean_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
            
            raw_id = clean_row.get("Unique ID", "")
            name = clean_row.get("Member Name", "")
            tier = clean_row.get("Tier Type", "")
            raw_dob = clean_row.get("Date of Birth", "")
            raw_enroll = clean_row.get("Date of Enrollment", "")
            raw_flight = clean_row.get("Date of Flight", "")

            # Parse dates (YYYY-MM-DD)
            dob = self.parse_date(raw_dob, ["%Y-%m-%d"])
            enroll_date = self.parse_date(raw_enroll, ["%Y-%m-%d"])
            flight_date = self.parse_date(raw_flight, ["%Y-%m-%d"])

            status = ValidationStatus.VALID
            reasons = []

            if not raw_id:
                status = ValidationStatus.QUARANTINE
                reasons.append("Missing Unique ID")

            # Check invalid date warnings
            if raw_dob and raw_dob.upper() != "NULL" and not dob:
                status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
                reasons.append(f"Unparseable Date of Birth '{raw_dob}'")

            if raw_enroll and not enroll_date:
                status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
                reasons.append(f"Unparseable Date of Enrollment '{raw_enroll}'")

            if raw_flight and not flight_date:
                status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
                reasons.append(f"Unparseable Date of Flight '{raw_flight}'")

            reason_str = "; ".join(reasons) if reasons else None

            member_records.append(
                MemberRecord(
                    member_id=raw_id,
                    member_name=name,
                    enrollment_date=enroll_date,
                    last_flight_date=flight_date,
                    tier_code=tier or None,
                    country="Australia",
                    dob=dob,
                    is_active="A",
                    source_system=self.source_system,
                    source_file_name=source_file_name,
                    source_file_timestamp=source_file_timestamp,
                    source_row_number=idx,
                    validation_status=status,
                    validation_reason=reason_str,
                )
            )

        return raw_records, member_records


class IndCsvAdapter(BaseAdapter):
    """
    Adapter for India CSV (IND(in).csv).
    Columns: ID, Name, DOB, TierCode, EnrollmentDate, Individual or Corporate, Flight Date
    Date format: M/D/YYYY
    Quirks: Extra attribute 'Individual or Corporate'.
    """

    def __init__(self):
        super().__init__(source_system="IND_CSV")

    def parse_file(self, file_path: Path) -> Tuple[List[RawRecord], List[MemberRecord]]:
        """Parse India CSV file from disk."""
        file_path = Path(file_path)
        file_timestamp = self.extract_file_timestamp(file_path)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return self.parse_content(content, file_path.name, file_timestamp)

    def parse_content(
        self, content: str, source_file_name: str, source_file_timestamp: datetime
    ) -> Tuple[List[RawRecord], List[MemberRecord]]:
        """Parse raw India CSV content."""
        raw_records: List[RawRecord] = []
        member_records: List[MemberRecord] = []

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            raw_records.append(
                RawRecord(
                    source_system=self.source_system,
                    source_file_name=source_file_name,
                    source_file_timestamp=source_file_timestamp,
                    source_row_number=idx,
                    raw_payload=line,
                )
            )

        reader = csv.DictReader(io.StringIO(content))
        for idx, row in enumerate(reader, start=2):
            clean_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}

            raw_id = clean_row.get("ID", "")
            name = clean_row.get("Name", "")
            tier = clean_row.get("TierCode", "")
            raw_dob = clean_row.get("DOB", "")
            raw_enroll = clean_row.get("EnrollmentDate", "")
            raw_flight = clean_row.get("Flight Date", "")
            ind_corp = clean_row.get("Individual or Corporate", "")

            # Parse dates (M/D/YYYY)
            dob = self.parse_date(raw_dob, ["%m/%d/%Y"])
            enroll_date = self.parse_date(raw_enroll, ["%m/%d/%Y"])
            flight_date = self.parse_date(raw_flight, ["%m/%d/%Y"])

            status = ValidationStatus.VALID
            reasons = []

            if not raw_id:
                status = ValidationStatus.QUARANTINE
                reasons.append("Missing ID")

            if raw_dob and not dob:
                status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
                reasons.append(f"Unparseable DOB '{raw_dob}'")

            if raw_enroll and not enroll_date:
                status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
                reasons.append(f"Unparseable EnrollmentDate '{raw_enroll}'")

            if raw_flight and not flight_date:
                status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
                reasons.append(f"Unparseable Flight Date '{raw_flight}'")

            reason_str = "; ".join(reasons) if reasons else None

            member_records.append(
                MemberRecord(
                    member_id=raw_id,
                    member_name=name,
                    enrollment_date=enroll_date,
                    last_flight_date=flight_date,
                    tier_code=tier or None,
                    country="India",
                    dob=dob,
                    is_active="A",
                    source_system=self.source_system,
                    source_file_name=source_file_name,
                    source_file_timestamp=source_file_timestamp,
                    source_row_number=idx,
                    validation_status=status,
                    validation_reason=reason_str,
                )
            )

        return raw_records, member_records


class UsaCsvAdapter(BaseAdapter):
    """
    Adapter for USA CSV (USA(in).csv).
    Columns: ID, Name, TierCode, EnrollmentDate, FlightDate
    Date format: [M]MDDYYYY (compact numeric with stripped leading zeros, e.g. 6152022, 12282021)
    Quirks: DOB column omitted.
    """

    def __init__(self):
        super().__init__(source_system="USA_CSV")

    def parse_file(self, file_path: Path) -> Tuple[List[RawRecord], List[MemberRecord]]:
        """Parse USA CSV file from disk."""
        file_path = Path(file_path)
        file_timestamp = self.extract_file_timestamp(file_path)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return self.parse_content(content, file_path.name, file_timestamp)

    @staticmethod
    def parse_usa_compact_date(date_str: Optional[str]) -> Optional[date]:
        """
        Parse compact [M]MDDYYYY date strings.
        - 7 digits: M DD YYYY (e.g. 6152022 -> 2022-06-15)
        - 8 digits: MM DD YYYY (e.g. 12282021 -> 2021-12-28)
        """
        if not date_str:
            return None
        cleaned = str(date_str).strip()
        if not cleaned or not cleaned.isdigit():
            return None

        try:
            if len(cleaned) == 7:
                month = int(cleaned[0])
                day = int(cleaned[1:3])
                year = int(cleaned[3:7])
                return date(year, month, day)
            elif len(cleaned) == 8:
                month = int(cleaned[0:2])
                day = int(cleaned[2:4])
                year = int(cleaned[4:8])
                return date(year, month, day)
        except ValueError:
            return None

        return None

    def parse_content(
        self, content: str, source_file_name: str, source_file_timestamp: datetime
    ) -> Tuple[List[RawRecord], List[MemberRecord]]:
        """Parse raw USA CSV content."""
        raw_records: List[RawRecord] = []
        member_records: List[MemberRecord] = []

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            raw_records.append(
                RawRecord(
                    source_system=self.source_system,
                    source_file_name=source_file_name,
                    source_file_timestamp=source_file_timestamp,
                    source_row_number=idx,
                    raw_payload=line,
                )
            )

        reader = csv.DictReader(io.StringIO(content))
        for idx, row in enumerate(reader, start=2):
            clean_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}

            raw_id = clean_row.get("ID", "")
            name = clean_row.get("Name", "")
            tier = clean_row.get("TierCode", "")
            raw_enroll = clean_row.get("EnrollmentDate", "")
            raw_flight = clean_row.get("FlightDate", "")

            # Parse compact USA dates
            enroll_date = self.parse_usa_compact_date(raw_enroll)
            flight_date = self.parse_usa_compact_date(raw_flight)

            status = ValidationStatus.VALID
            reasons = []

            if not raw_id:
                status = ValidationStatus.QUARANTINE
                reasons.append("Missing ID")

            if raw_enroll and not enroll_date:
                status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
                reasons.append(f"Unparseable EnrollmentDate '{raw_enroll}'")

            if raw_flight and not flight_date:
                status = ValidationStatus.WARNING if status != ValidationStatus.QUARANTINE else status
                reasons.append(f"Unparseable FlightDate '{raw_flight}'")

            reason_str = "; ".join(reasons) if reasons else None

            member_records.append(
                MemberRecord(
                    member_id=raw_id,
                    member_name=name,
                    enrollment_date=enroll_date,
                    last_flight_date=flight_date,
                    tier_code=tier or None,
                    country="USA",
                    dob=None,  # Explicitly missing from USA CSV schema
                    is_active="A",
                    source_system=self.source_system,
                    source_file_name=source_file_name,
                    source_file_timestamp=source_file_timestamp,
                    source_row_number=idx,
                    validation_status=status,
                    validation_reason=reason_str,
                )
            )

        return raw_records, member_records


def get_csv_adapter_for_file(file_path_or_name: str) -> BaseAdapter:
    """Factory function returning the appropriate CSV adapter for a given filename."""
    name_upper = Path(file_path_or_name).name.upper()
    if "AUS" in name_upper or "AUSTRALIA" in name_upper:
        return AusCsvAdapter()
    elif "IND" in name_upper or "INDIA" in name_upper:
        return IndCsvAdapter()
    elif "USA" in name_upper or "UNITED_STATES" in name_upper:
        return UsaCsvAdapter()
    raise ValueError(f"No specific CSV adapter recognized for filename '{file_path_or_name}'")
