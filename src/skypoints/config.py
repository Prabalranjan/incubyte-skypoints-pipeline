"""
Configuration and settings management for Skypoints Data Pipeline.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    """Core pipeline configuration settings."""
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    data_dir: Path = base_dir / "data"
    raw_dir: Path = data_dir / "raw"
    database_path: str = ":memory:"  # In-memory DuckDB by default, or path to persistent .duckdb
    stale_member_days_threshold: int = 90
