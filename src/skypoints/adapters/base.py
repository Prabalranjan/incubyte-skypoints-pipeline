"""
Base adapter interface and utilities for feed ingestion.
"""
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from pathlib import Path
import re
from typing import Optional, List, Tuple
from skypoints.models.canonical import RawRecord, MemberRecord, ValidationStatus


class BaseAdapter(ABC):
    """Abstract base class for all file and feed ingestion adapters."""

    def __init__(self, source_system: str):
        self.source_system = source_system

    @abstractmethod
    def parse_file(self, file_path: Path) -> Tuple[List[RawRecord], List[MemberRecord]]:
        """
        Parse an incoming source file into Bronze RawRecords and Silver MemberRecords.
        """
        pass

    @staticmethod
    def extract_file_timestamp(file_path: Path) -> datetime:
        """
        Extract timestamp from filename pattern (e.g. YYYYMMDD_HHMMSS or YYYYMMDD).
        Falls back to filesystem modification time (st_mtime) in UTC.
        """
        name = file_path.name
        # Match YYYYMMDD_HHMMSS
        match_dt = re.search(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", name)
        if match_dt:
            y, m, d, h, mi, s = map(int, match_dt.groups())
            return datetime(y, m, d, h, mi, s, tzinfo=timezone.utc)

        # Match YYYYMMDD
        match_d = re.search(r"(\d{4})(\d{2})(\d{2})", name)
        if match_d:
            y, m, d = map(int, match_d.groups())
            return datetime(y, m, d, 0, 0, 0, tzinfo=timezone.utc)

        # Fallback to file mtime
        if file_path.exists():
            mtime = file_path.stat().st_mtime
            return datetime.fromtimestamp(mtime, tz=timezone.utc)

        return datetime.now(timezone.utc)

    @staticmethod
    def parse_date(date_str: Optional[str], preferred_formats: Optional[List[str]] = None) -> Optional[date]:
        """
        Parse a date string into a datetime.date object.
        Returns None if string is empty, null-like, or malformed.
        """
        if not date_str:
            return None

        cleaned = str(date_str).strip()
        if not cleaned or cleaned.upper() in ("NULL", "NONE", "NA", "N/A"):
            return None

        # Build format list
        formats = preferred_formats or []
        default_formats = [
            "%Y-%m-%d",
            "%Y%m%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%m%d%Y",
            "%d%m%Y",
            "%Y/%m/%d",
        ]
        for fmt in default_formats:
            if fmt not in formats:
                formats.append(fmt)

        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue

        return None
