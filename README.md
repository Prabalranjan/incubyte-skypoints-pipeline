# Skypoints Loyalty Data Pipeline

A modular, production-grade ELT/ETL pipeline designed for heterogeneous airline loyalty feeds. Built with Python, DuckDB, and Pydantic, following the 3-Layer Medallion Architecture.

---

## Architecture & System Design

For full details on source feed inventory, data quality discovery, canonical schemas, and technical assumptions, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
+--------------------------------------------------------------------------------------------------+
| LAYER 1: RAW / LANDING (Bronze)                                                                  |
| - Ingests heterogeneous feeds: Pipe-delimited (H/D), Custom CSVs (AUS, IND, USA), JSON Feeds    |
| - Captures source metadata (file timestamp, line number, ingestion timestamp)                    |
+--------------------------------------------------------------------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------------------------+
| LAYER 2: STANDARDIZATION & ENRICHMENT (Silver)                                                   |
| - Modular adapters normalize date formats (YYYY-MM-DD, M/D/YYYY, MMDDYYYY) to ISO-8601           |
| - Derived metrics: Age (exact birthday boundary) & Stale_Member (> 90 days since flight)        |
| - Data quality validation & quarantine routing                                                   |
+--------------------------------------------------------------------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------------------------+
| LAYER 3: TARGET TABLES & TRANSACTIONS (Gold)                                                     |
| - Dynamic Country Router creates Table_<Country> safely with idempotent DDL                      |
| - Member state tracking with "Latest Record Wins" by file arrival timestamp                      |
| - JSON Redemptions flattened, deduplicated by txn_id, and joined to member profiles              |
+--------------------------------------------------------------------------------------------------+
```

---

## Key Features

- **Decoupled Adapters**: Each incoming feed (Pipe H/D, Australia CSV, India CSV, USA CSV, JSON Redemptions) has an isolated parser. Adding new feeds requires zero changes to existing ones.
- **Dynamic Country Routing**: Enforces safe, idempotent DDL generation for dynamic country tables (`Table_India`, `Table_USA`, etc.) with sanitized identifiers.
- **Strict Deduplication & Freshness**: Resolves out-of-order and multi-version updates using source file arrival timestamps and in-file row numbers.
- **Data Quality & Quarantining**: Invalid dates, unmapped country codes, or missing required attributes are quarantined with descriptive error tags.

---

## Directory Structure

```
├── src/
│   └── skypoints/
│       ├── __init__.py
│       ├── config.py           # Central settings and paths
│       ├── models/             # Canonical schema dataclasses / Pydantic models
│       ├── adapters/           # Modular ingestion adapters (H/D, CSVs, JSON)
│       ├── enrichment/         # Derived columns (Age, Stale_Member)
│       ├── validation/         # Schema and business rule validators
│       ├── router/             # Dynamic country router & DDL generator
│       ├── storage/            # Database engine and table management
│       └── pipeline.py         # Main pipeline orchestrator
├── tests/
│   ├── __init__.py
│   └── test_smoke.py           # Project smoke tests
├── docs/
│   └── ARCHITECTURE.md         # Source inventory, canonical schemas & design
├── Mail files/                 # Original assessment sample inputs
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (tested with Python 3.13)
- Git

### 2. Environment Setup
```bash
# Clone the repository
git clone git@github.com:Prabalranjan/incubyte-skypoints-pipeline.git
cd incubyte-skypoints-pipeline

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Pipeline
You can run the pipeline directly using the top-level runner:
```bash
# Run against the supplied assessment files in 'Mail files'
python run_pipeline.py --input-dir "Mail files" --as-of-date 2024-06-01
```

Or using a persistent DuckDB database file for permanent inspection:
```bash
python run_pipeline.py --input-dir "Mail files" --as-of-date 2024-06-01 --db-path "skypoints_data.duckdb"
```

#### CLI Options
| Argument | Description | Default |
| :--- | :--- | :--- |
| `--input-dir` | Folder path containing incoming data feeds | `"Mail files"` |
| `--as-of-date` | Reference evaluation date for Age and Stale Member derivation (`YYYY-MM-DD`) | Current Date |
| `--db-path` | DuckDB database path (e.g. `:memory:` or file path) | `":memory:"` |

---

### 4. Running the Test Suite
The repository includes a comprehensive 46-test automated test suite covering all units, adapters, edge-cases, and end-to-end integration:
```bash
# Run via pytest
pytest

# Or run via standard unittest (zero external tools required)
python -m unittest discover tests
```

---

## Live Demonstration Walkthrough

When presenting or demonstrating this solution, the following core features can be demonstrated:

1. **Multi-Source Ingestion & Decoupled Adapters**:
   * Run `python run_pipeline.py --input-dir "Mail files"` to demonstrate automatic discovery of Pipe (H/D), custom CSVs, and JSON feeds.
2. **Data Cleaning & Date Normalization**:
   * Demonstrates how diverse date layouts (`YYYY-MM-DD`, `M/D/YYYY`, compact `[M]MDDYYYY`) and anomalies (literal `"NULL"` DOB, invalid month `2021-13-13`) are cleanly parsed and validated without crashes.
3. **Derived Metrics**:
   * `Age`: Exact birthday anniversary calculation relative to `--as-of-date`.
   * `Stale_Member`: Strict boundary check (`days_since_flight > 90`).
4. **Dynamic Country Routing & Moves**:
   * Demonstrates safe dynamic generation of `Table_<Country>` (`Table_Australia`, `Table_India`, `Table_USA`).
   * Demonstrates relocation: moving a member to a new country table automatically deactivates their historical record (`is_active = 'I'`) in their old country table.
5. **JSON Redemptions & Profile Join**:
   * Demonstrates array unnesting into `Table_Redemptions`, idempotency on duplicate replay, and SQL join with `Current_Member_Profiles` preserving unmatched records with `UNMATCHED_MEMBER`.
