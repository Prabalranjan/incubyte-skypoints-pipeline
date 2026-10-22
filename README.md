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
The repository includes a comprehensive 47-test automated test suite covering all units, adapters, edge-cases, and end-to-end integration:
```bash
# Run via pytest
pytest

# Or run via standard unittest (zero external tools required)
python -m unittest discover tests
```

---

## Live Demonstration Runner

To execute an automated walkthrough demonstrating all 5 core evaluation requirements in one command, run:
```bash
python demo.py
```

### Demonstration Scenarios Covered:
1. **Multi-Source Ingestion & Decoupled Adapters**:
   * Scans and parses `Mail files/` ([AUS(Sheet1).csv](Mail%20files/AUS(Sheet1).csv), [IND(in).csv](Mail%20files/IND(in).csv), [USA(in).csv](Mail%20files/USA(in).csv)).
   * Demonstrates string `"NULL"` handling, invalid month `2021-13-13` warnings, and compact date padding without pipeline crashes.
2. **Derived Metrics (Age & Strict 90-Day Stale Member Rule)**:
   * `Age`: Exact birthday anniversary calculation (evaluating before vs on birthday).
   * `Stale_Member`: Strict boundary demonstration: 89 days (Active), 90 days (Not Stale), 91 days (Stale).
3. **Late-Arriving Older File Protection**:
   * Simulates Day 2 profile arrival (`2024-01-15`) followed by a delayed Day 1 file (`2024-01-10`).
   * Proves that the current profile in `Table_USA` does not regress to the older state.
4. **Country Moves & Cross-Table Membership Consistency**:
   * Simulates a member relocating from India to Australia.
   * Proves that `Table_India` record is marked inactive (`is_active = 'I'`) and `Table_Australia` is created active (`is_active = 'A'`), guaranteeing exactly 1 active country profile.
5. **JSON Redemptions & Profile Join**:
   * Demonstrates array unnesting into `Table_Redemptions`, idempotency on duplicate transaction replay, and SQL join with `Current_Member_Profiles` preserving unmatched records with `UNMATCHED_MEMBER`.

---

## Warehouse Portability: Snowflake & ANSI SQL Scripts

For cloud warehouse deployments (e.g., Snowflake, BigQuery, PostgreSQL) or pure SQL reviews, standalone production DDL scripts are provided in the `sql/` directory:
- [sql/01_bronze_raw_landing.sql](sql/01_bronze_raw_landing.sql): Raw landing table DDL and audit metadata.
- [sql/02_silver_staging_and_derived.sql](sql/02_silver_staging_and_derived.sql): Staging DDL, quarantine table, and SQL expressions for `Age` & `Stale_Member`.
- [sql/03_gold_country_tables.sql](sql/03_gold_country_tables.sql): Dynamic target table DDL (`Table_India`, `Table_USA`, `Table_Australia`), "Latest Record Wins" window function query, and `Current_Member_Profiles` view.
- [sql/04_gold_redemptions_and_join.sql](sql/04_gold_redemptions_and_join.sql): `Table_Redemptions` DDL, native Snowflake `LATERAL FLATTEN` JSON query, and profile join view.
