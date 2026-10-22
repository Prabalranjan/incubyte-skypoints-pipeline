"""
Top-level execution script for Skypoints Data Pipeline.
Usage:
    python run_pipeline.py --input-dir "Mail files" --as-of-date 2024-06-01
"""
import sys
from pathlib import Path

# Ensure src is in sys.path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from skypoints.pipeline import main

if __name__ == "__main__":
    main()
