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

### 3. Running Tests
```bash
pytest
```
