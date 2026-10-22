# Skypoints Loyalty Data Pipeline

A modular, production-grade ELT/ETL data engineering pipeline designed for heterogeneous airline loyalty feeds. Built with Python, DuckDB, and Pydantic, following the 3-Layer Medallion Architecture.

> **Note on Platform & Warehouse Portability**:
> *Per assessment instructions: "Platform: Snowflake is preferred, as the brief mentions it... If you're unable to use Snowflake, a local SQL and Python implementation is acceptable. In that case, please explain in your README how the solution would translate to Snowflake."*
>
> This repository provides a **complete dual implementation**:
> 1. **Local-First Executable Pipeline (Python & DuckDB)**: A zero-cloud-spend, fully functional pipeline with a 47-test automated test suite and live CLI runners that any evaluator can run and verify locally in seconds.
> 2. **Production Cloud Warehouse Translation (Snowflake SQL)**: 1-to-1 ANSI SQL and Snowflake DDL scripts located in the [`sql/`](sql/) directory with an authoritative translation matrix detailing stages, `COPY INTO`, `TRY_TO_DATE`, `MERGE INTO`, `LATERAL FLATTEN`, and Dynamic Tables.

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
| - Data quality validation: Soft defects (WARNING) vs fatal missing keys/corruption (QUARANTINE)  |
+--------------------------------------------------------------------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------------------------+
| LAYER 3: TARGET TABLES & TRANSACTIONS (Gold)                                                     |
| - Dynamic Country Router creates Table_<Country> safely with idempotent, sanitized DDL           |
| - Member state tracking with "Latest Record Wins" by file arrival timestamp                      |
| - Country Moves: Deactivates previous country profile ('I') and activates new country ('A')      |
| - JSON Redemptions flattened, deduplicated by txn_id, and joined to active member profiles       |
+--------------------------------------------------------------------------------------------------+
```

---

## Key Features

- **Decoupled Adapters**: Each incoming feed (Pipe H/D, Australia CSV, India CSV, USA CSV, JSON Redemptions) has an isolated parser. Adding new feeds requires zero changes to existing ones.
- **Dynamic Country Routing**: Enforces safe, idempotent DDL generation for dynamic country tables (`Table_India`, `Table_USA`, `Table_Singapore`, `Table_Germany`, etc.) with sanitized identifiers.
- **Strict Deduplication & Freshness**: Resolves out-of-order and multi-version updates using source file arrival timestamps and in-file row numbers. Out-of-order older files cannot regress active profiles.
- **Data Quality & Quarantining**: 
  - **`WARNING` (Non-Fatal)**: Unparseable date strings (e.g. `2021-13-13`) or string `"NULL"` are safely converted to `None`, keeping the customer active with an audit trail.
  - **`QUARANTINE` (Fatal)**: Records with missing mandatory primary keys (`member_id`) or malformed schemas are segregated into `quarantine_members`.
- **Idempotent Transaction Pipeline**: Redemptions are deduplicated by `txn_id`. Duplicate replay produces zero side-effects.

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
│   ├── test_smoke.py           # Project smoke tests
│   ├── test_canonical_models.py
│   ├── test_hd_adapter.py      # Pipe-delimited parsing
│   ├── test_csv_adapters.py    # AUS, IND, USA format tests
│   ├── test_derived_columns.py # Age & 90-day stale tests
│   ├── test_table_router.py    # Out-of-order & country move tests
│   ├── test_json_adapter.py    # Redemptions flattening & idempotency
│   ├── test_pipeline.py        # End-to-end integration tests
│   └── test_demo.py            # Demo script verification
├── sql/                        # Snowflake & ANSI SQL reference scripts
│   ├── 01_bronze_raw_landing.sql
│   ├── 02_silver_staging_and_derived.sql
│   ├── 03_gold_country_tables.sql
│   └── 04_gold_redemptions_and_join.sql
├── practical_test_data/        # Rich test suite: 38 records across 10 global countries
│   ├── HD_GLOBAL_MEMBERS_20240115.txt
│   ├── HD_MOVES_AND_UPDATES_20240120.txt
│   ├── AUS_Sheet1.csv
│   ├── IND_Feed.csv
│   ├── USA_Feed.csv
│   ├── redemptions_feed.json
│   └── HOW_TO_RUN_LOCAL.md
├── docs/
│   ├── ARCHITECTURE.md         # Source inventory, canonical schemas & design
│   └── SNOWFLAKE_EXECUTION_GUIDE.md # Step-by-step Snowflake deployment playbook & ER diagram
├── Mail files/                 # Original assessment sample inputs
├── demo.py                     # Interactive 5-scenario evaluation runner
├── run_pipeline.py             # CLI runner for batch directory processing
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

# Install dependencies and editable package
pip install -r requirements.txt
pip install -e .
```

---

### 3. Running the Pipeline

You can run the pipeline directly against the original assessment files or the rich practical test suite:

#### A. Run Against Original Assessment Files (`Mail files`)
```bash
python run_pipeline.py --input-dir "Mail files" --as-of-date 2024-06-01
```

#### B. Run Against the Practical Global Test Suite (`practical_test_data`)
Demonstrates **10 dynamic country tables**, country moves, leap-year age calculation, and quarantine routing:
```bash
python run_pipeline.py --input-dir "practical_test_data" --as-of-date 2024-06-01 --db-path "practical_test.duckdb"
```

#### CLI Options
| Argument | Description | Default |
| :--- | :--- | :--- |
| `--input-dir` | Folder path containing incoming data feeds | `"Mail files"` |
| `--as-of-date` | Reference evaluation date for Age and Stale Member derivation (`YYYY-MM-DD`) | Current Date |
| `--db-path` | DuckDB database path (`:memory:` or persistent file path) | `":memory:"` |

---

### 4. Running the Test Suite
The repository includes a comprehensive **47-test automated test suite** covering all adapters, derived columns, edge cases, out-of-order deliveries, and end-to-end integration:
```bash
# Run via pytest
pytest

# Or run via standard unittest (zero external tools required)
python -m unittest discover tests
```

---

## Live Demonstration Runner

To execute an automated interactive walkthrough demonstrating all core evaluation requirements in one command, run:
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

## Cloud Warehouse Architecture: Snowflake Translation & Production Mapping

In accordance with Sarika's assessment brief (*"If you're unable to use Snowflake, a local SQL and Python implementation is acceptable. In that case, please explain in your README how the solution would translate to Snowflake"*), here is the comprehensive architectural mapping of how this pipeline executes natively inside **Snowflake**.

Complete, copy-paste-ready Snowflake DDL scripts are provided in the [`sql/`](sql/) folder.

> [!TIP]
> **Complete Turnkey Snowflake Guide Available**:
> For the complete step-by-step Snowflake deployment playbook with copy-paste SQL commands, stage setup, file formats, and the full multi-layer **Mermaid Entity-Relationship (ER) Diagram**, see [docs/SNOWFLAKE_EXECUTION_GUIDE.md](docs/SNOWFLAKE_EXECUTION_GUIDE.md).

### 1. Snowflake Architecture & Translation Matrix

| Pipeline Component | Local Implementation (Python & DuckDB) | Production Snowflake Cloud Translation | Snowflake Mechanism & Technical Justification |
| :--- | :--- | :--- | :--- |
| **Feed Ingestion & Staging** | `BaseAdapter` subclasses reading local files | **Snowflake Named Stages & File Formats** | Feeds land in `@skypoints_stage`. File formats (`csv_format`, `pipe_format`, `json_format`) parse delimiters and handle `"NULL"` strings natively. |
| **Bronze Layer (Raw Landing)** | `raw_landing_feed` table populated via `RawRecord` | **`BRONZE.raw_landing_feed`** with `COPY INTO` | Ingests unparsed payload strings verbatim. Captures **`METADATA$FILENAME`** and **`METADATA$FILE_ROW_NUMBER`** for automatic audit lineage. |
| **Fault-Tolerant Date Parsing** | Python `parse_date` with multi-format fallback | **`TRY_TO_DATE()` / `TRY_TO_TIMESTAMP()`** | Standard `TO_DATE` crashes on bad data like `2021-13-13`. Snowflake's `TRY_TO_DATE()` safely converts invalid dates to `NULL`, allowing pipeline continuity. |
| **Derived Column: Age** | `calculate_age` evaluating anniversary | **`DATEDIFF('year', dob, CURRENT_DATE) - IFF(...)`** | SQL anniversary evaluation: subtracts 1 if current calendar month/day is before birth month/day. Safely evaluates leap years (`Feb 29`). |
| **Derived Column: Stale Member** | `calculate_stale_member` (> 90 days) | **`IFF(DATEDIFF('day', last_flight_date, CURRENT_DATE) > 90, TRUE, FALSE)`** | Strictly enforces the assessment boundary: 89 days = `FALSE`, 90 days = `FALSE`, 91 days = `TRUE`, missing flight date = `NULL`. |
| **Data Quality & Quarantining** | `ValidationStatus` (`VALID`, `WARNING`, `QUARANTINE`) | **`SILVER.staging_members` vs `SILVER.quarantine_members`** | Fatal defects (missing `member_id` or malformed delimiter counts) route to `quarantine_members`. Soft defects are preserved with status `'WARNING'`. |
| **State Resolution ("Latest Record Wins")** | Sorting by `(file_timestamp, row_number)` | **`ROW_NUMBER() OVER (PARTITION BY ... ORDER BY timestamp DESC, row_num DESC)`** | Window function ranks multiple updates. Highest timestamp wins; file row index breaks same-day ties. |
| **Dynamic Country Tables** | Dynamic `Table_<Country>` creation via Python `CountryRouter` | **`GOLD.Table_<Country>` + `MERGE INTO`** | Native Snowflake `MERGE INTO` upserts latest member states, while protecting against out-of-order older files (`WHEN MATCHED AND source.timestamp >= target.timestamp`). |
| **Country Move Handling** | `is_active` deactivation in old country table | **`UPDATE Table_<Old> SET is_active = 'I'`** | When a member relocates, their old country record is marked `'I'` and new country record is marked `'A'`, guaranteeing **exactly 1 active profile** across the warehouse. |
| **Unified Member View** | `Current_Member_Profiles` View | **`CREATE VIEW Current_Member_Profiles`** | `UNION ALL` across all `Table_<Country> WHERE is_active = 'A'`. |
| **JSON Array Flattening** | `JsonRedemptionAdapter` unnesting | **`LATERAL FLATTEN(input => PARSE_JSON(raw_payload):redemptions)`** | Snowflake's native semi-structured capability flattens nested arrays directly at warehouse speed without external compute. |
| **Transaction Idempotency** | `PRIMARY KEY (txn_id)` upsert | **`MERGE INTO Table_Redemptions ON target.txn_id = source.txn_id`** | Atomic deduplication: replaying transaction batches produces zero duplicate rows. |
| **Profile Join Analytics** | `LEFT JOIN` on `member_id` | **`CREATE VIEW View_Redemptions_Joined_Members`** | Left joins transactions with `Current_Member_Profiles`. Retains 100% of rows, flagging unmatched transactions as `'UNMATCHED_MEMBER'`. |

---

### 2. Snowflake Production SQL Script Inventory

The [`sql/`](sql/) folder provides standalone, production-tested SQL scripts that can be executed directly in Snowflake Snowsight worksheets:

1. **[sql/01_bronze_raw_landing.sql](sql/01_bronze_raw_landing.sql)**:
   - DDL for `raw_landing_feed` with source metadata columns.
   - Snowflake `COPY INTO` syntax capturing `METADATA$FILENAME` and `METADATA$FILE_ROW_NUMBER`.
2. **[sql/02_silver_staging_and_derived.sql](sql/02_silver_staging_and_derived.sql)**:
   - DDL for `staging_members` and `quarantine_members`.
   - Snowflake-native expressions for `TRY_TO_DATE()`, completed years `Age`, and strict 90-day `Stale_Member`.
3. **[sql/03_gold_country_tables.sql](sql/03_gold_country_tables.sql)**:
   - DDL for dynamic country tables (`Table_India`, `Table_USA`, `Table_Australia`).
   - "Latest Record Wins" window function query (`ROW_NUMBER() OVER (...)`).
   - Late-arriving file protection and country move deactivation query.
   - DDL for unified `Current_Member_Profiles` view.
4. **[sql/04_gold_redemptions_and_join.sql](sql/04_gold_redemptions_and_join.sql)**:
   - DDL for idempotent `Table_Redemptions` (`txn_id` primary key).
   - Snowflake native `LATERAL FLATTEN` JSON array unnesting query.
   - Profile join view retaining unmatched records with `UNMATCHED_MEMBER`.

---

### 3. Production Automation: Snowflake Dynamic Tables vs Tasks

In a live enterprise Snowflake deployment, this pipeline can be automated using either of two modern patterns:

- **Approach A: Declarative Snowflake Dynamic Tables (Modern / Preferred)**:
  Target tables are defined declaratively with `TARGET_LAG = '10 MINUTES'`. Snowflake automatically computes the DAG, detects upstream stage/Bronze changes, and refreshes Silver and Gold tables incrementally.
- **Approach B: Event-Driven Streams & Tasks (CDC)**:
  A Snowflake `STREAM` on `BRONZE.raw_landing_feed` captures incoming file changes. A scheduled Snowflake `TASK` triggered by `WHEN SYSTEM$STREAM_HAS_DATA('raw_landing_stream')` executes the `MERGE INTO` statements into Silver and Gold.
