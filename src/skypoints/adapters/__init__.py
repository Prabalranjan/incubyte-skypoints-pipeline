"""File and feed ingestion adapters."""
from skypoints.adapters.base import BaseAdapter
from skypoints.adapters.hd_adapter import HDAdapter

__all__ = [
    "BaseAdapter",
    "HDAdapter",
]
