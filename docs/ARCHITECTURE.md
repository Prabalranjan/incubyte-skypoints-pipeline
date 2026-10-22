# System Architecture, Data Inventory & Technical Assumptions

This document provides a comprehensive technical breakdown of the Skypoints Loyalty Data Pipeline, including source feed discovery, canonical data models, 3-layer Medallion architecture, and documented design assumptions.

---

## 1. Source Feed Inventory & Data Discovery

An initial audit of the incoming assessment data revealed heterogeneous schemas, disjoint identity keys, and variable data formats across sources:

### A. Feed Inventory Matrix
| Feed Name | Format / Delimiter | Key Column | Date Format(s) | Notable Quirks & Quality Findings |
| :--- | :--- | :--- | :--- | :--- |
| **H/D Feed** | Pipe-delimited (`\|`) with Header/Detail records | `Member_Id` | `YYYY-MM-DD` | Authoritative global member key. `Post Code` omitted from file layout. Header line (`H`) must be stripped. |
| **Australia Feed** (`AUS(Sheet1).csv`) | CSV (comma-separated) | `Unique ID` | `YYYY-MM-DD` | Contains string literal `"NULL"` in DOB. Row 2 contains invalid month `2021-13-13` in enrollment date. |
| **India Feed** (`IND(in).csv`) | CSV (comma-separated) | `ID` | `M/D/YYYY` | Slash-separated dates without leading zeros. Contains extra unmapped business column: `Individual or Corporate`. |
| **USA Feed** (`USA(in).csv`) | CSV (comma-separated) | `ID` | `[M]MDDYYYY` | Compact numeric dates with stripped leading zeros (e.g., `6152022` $\rightarrow$ June 15, 2022). DOB column completely missing. |
| **Redemptions Feed** | JSON document | `txn_id` | `YYYY-MM-DD` | Nested document structure with an array of transactions. Requires array unnesting / flattening. |

### B. Member Identity & Key Isolation
- **Global Key**: `Member_Id` in the H/D feed is the authoritative enterprise identifier.
- **Source-Local Keys**: `Unique ID` (AUS) and `ID` (IND, USA) are source-specific row numbers and **must not** be directly joined or conflated with `Member_Id` without an explicit crosswalk.
- **Architectural Decision**: Feeds are ingested through isolated, standalone adapter pipelines. CSV records are standardized and audited in separate staging/audit targets without corrupting core member profiles.

---

## 2. 3-Layer Medallion Architecture

```
+--------------------------------------------------------------------------------------------------+
| LAYER 1: RAW / LANDING (Bronze)                                                                  |
| - Ingests raw feeds verbatim (H/D, AUS CSV, IND CSV, USA CSV, JSON)                             |
| - Captures audit lineage: source file name, file timestamp, source row number, ingested_at       |
+--------------------------------------------------------------------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------------------------+
| LAYER 2: STANDARDIZATION & ENRICHMENT (Silver)                                                   |
| - Plug-and-play adapters normalize field names & date strings into ISO-8601 (YYYY-MM-DD)          |
| - Derived Columns Engine:                                                                        |
|     * Age: Completed years computed from DOB relative to execution run date                      |
|     * Stale_Member: Boolean flag indicating if (run_date - last_flight_date) > 90 days            |
| - Validation engine partitions records into VALID vs QUARANTINE                                  |
+--------------------------------------------------------------------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------------------------+
| LAYER 3: TARGET TABLES & REDEMPTIONS (Gold)                                                      |
| - Dynamic Country Router routes members to Table_<Country>                                       |
| - Idempotent, safe DDL generation for newly encountered countries                                |
| - State Resolution: "Latest Record Wins" based on source file arrival timestamp                  |
| - Country Moves: Deactivates or migrates historical records upon relocation                      |
| - Flattened JSON transactions loaded into Table_Redemptions and joined to member profiles        |
+--------------------------------------------------------------------------------------------------+
```

---

## 3. Canonical Schemas

### A. Canonical Member Schema (`Table_<Country>`)
| Field Name | Type | Description | Handling Rule |
| :--- | :--- | :--- | :--- |
| `member_id` | `VARCHAR(32)` | Authoritative global key | Preserves leading zeros |
| `member_name` | `VARCHAR(255)` | Full member name | Trimmed string |
| `enrollment_date` | `DATE` | Program enrollment date | Normalized to `YYYY-MM-DD` |
| `last_flight_date` | `DATE` | Most recent flight date | Normalized to `YYYY-MM-DD` |
| `tier_code` | `VARCHAR(10)` | Membership tier code | `GLD`, `SLV`, `PLT`, etc. |
| `agent_name` | `VARCHAR(255)` | Servicing agent name | `NULL` if absent |
| `state` | `VARCHAR(50)` | State / province | `NULL` if absent |
| `country` | `VARCHAR(50)` | Normalized country name | Standardized (e.g., `India`, `USA`, `Australia`) |
| `post_code` | `VARCHAR(20)` | Postal / ZIP code | Preserved if present; `NULL` if absent |
| `dob` | `DATE` | Date of birth | Normalized to `YYYY-MM-DD` |
| `is_active` | `CHAR(1)` | Active record flag | Default `'A'`; `'I'` if superseded or moved |
| `age` | `INTEGER` | Completed years of age | Derived from `dob` |
| `stale_member` | `BOOLEAN` | Flight date freshness | `TRUE` if days > 90; `FALSE` if <= 90 |
| `source_system` | `VARCHAR(50)` | Origin feed identifier | e.g., `HD_FEED`, `AUS_CSV` |
| `source_file_name` | `VARCHAR(255)` | Lineage: input file name | Audit traceability |
| `source_file_timestamp` | `TIMESTAMP` | File arrival timestamp | Used for freshness ordering |
| `source_row_number` | `INTEGER` | File row index | Deterministic tie-breaker |
| `ingested_at` | `TIMESTAMP` | Ingestion timestamp | System processing time |
| `validation_status` | `VARCHAR(20)` | Record quality status | `VALID`, `WARNING`, `QUARANTINE` |

### B. Canonical Redemption Schema (`Table_Redemptions`)
| Field Name | Type | Description | Handling Rule |
| :--- | :--- | :--- | :--- |
| `txn_id` | `VARCHAR(64)` | Unique transaction ID | **Primary Key** (enforces idempotency) |
| `member_id` | `VARCHAR(32)` | Member identifier | **Foreign Key** to Member Profile |
| `feed_date` | `DATE` | Date feed was generated | Normalized date |
| `txn_date` | `DATE` | Transaction date | Normalized date |
| `partner` | `VARCHAR(100)` | Partner airline name | String |
| `miles_redeemed` | `INTEGER` | Miles redeemed | Positive integer |
| `status` | `VARCHAR(50)` | Transaction status | `COMPLETED`, `PENDING`, etc. |
| `source_file_name` | `VARCHAR(255)` | Lineage: input file name | Audit traceability |
| `ingested_at` | `TIMESTAMP` | Ingestion timestamp | System processing time |

---

## 4. Key Business Logic & Transformations

### A. Derived Columns Specification
1. **Age (Completed Years)**:
   * Computed relative to the batch execution run date (`as_of_date`).
   * Explicitly evaluates whether the member has reached their birthday anniversary in the current calendar year.
   * If `dob` is missing or invalid, `age` resolves to `NULL`.
2. **Stale Member Flag**:
   $$\text{Stale\_Member} = (\text{as\_of\_date} - \text{last\_flight\_date}) > 90$$
   * Exact boundary rule:
     * 90 days $\rightarrow$ `FALSE`
     * 91 days $\rightarrow$ `TRUE`
     * Missing flight date $\rightarrow$ `NULL`

### B. Dynamic Country Routing & Safe DDL
- Country names are standardized via a mapping dictionary (e.g., `IND` $\rightarrow$ `India`, `AUS` $\rightarrow$ `Australia`).
- Table identifiers are sanitized against an alphanumeric allowlist (`^[A-Za-z0-9_]+$`).
- Dynamic tables (`Table_<Country>`) are instantiated using idempotent DDL:
  ```sql
  CREATE TABLE IF NOT EXISTS Table_<SanitizedCountry> ( ...columns... );
  ```
- Unmapped or corrupt country entries route to `Table_Unassigned_Country` to prevent SQL injection or table explosion.

### C. Freshness & Conflict Resolution ("Latest Record Wins")
1. **File-Level Freshness**: Incoming files are stamped with arrival timestamps. Newer file timestamps supersede older ones.
2. **Deterministic Tie-Breaker**: When identical keys appear within the same file, the record with the higher `source_row_number` is preserved.
3. **Late-Arriving Data Guard**: Older files arriving out of sequence are ingested into audit staging but blocked from overwriting newer records in Gold target tables.
4. **Country Moves**: When a member relocates, their profile is created in the new country table and their previous record in the old country table is deactivated (`is_active = 'I'`).

---

## 5. Explicit Technical Assumptions

1. **Member Identity Separation**: CSV `ID` values are strictly local identifiers and are not merged into H/D `Member_Id` records without an explicit mapping.
2. **CSV Lifecycle**: CSV records undergo full standardization and validation and are stored in dedicated country/quarantine audit tables without corrupting global loyalty profiles.
3. **File Timestamp Fallback**: When filenames lack timestamps, the system relies on file system `last_modified` metadata or execution batch timestamps.
4. **Missing Post Code**: Since the H/D feed omits `Post Code`, the canonical column is populated with `NULL` without failing schema validation.
5. **Idempotent Transactions**: The `txn_id` attribute is treated as unique across redemptions, ensuring repeated pipeline runs do not produce duplicate entries.
