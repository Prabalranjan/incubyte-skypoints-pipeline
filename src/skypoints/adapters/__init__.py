"""File and feed ingestion adapters."""
from skypoints.adapters.base import BaseAdapter
from skypoints.adapters.hd_adapter import HDAdapter
from skypoints.adapters.csv_adapter import (
    AusCsvAdapter,
    IndCsvAdapter,
    UsaCsvAdapter,
    get_csv_adapter_for_file,
)

__all__ = [
    "BaseAdapter",
    "HDAdapter",
    "AusCsvAdapter",
    "IndCsvAdapter",
    "UsaCsvAdapter",
    "get_csv_adapter_for_file",
]
