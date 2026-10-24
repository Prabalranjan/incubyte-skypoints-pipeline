# Practical Local Test Guide: Skypoints Pipeline

This folder (`practical_test_data/`) contains rich, multi-source raw feeds designed to demonstrate all assessment edge cases and dynamic country routing on your local machine using Python and DuckDB.

---

## 1. What's Inside This Folder

| File Name | Format | Test Cases & Edge Cases Covered |
| :--- | :--- | :--- |
| **`HD_GLOBAL_MEMBERS_20240115.txt`** | Pipe-delimited (`H\|...`, `D\|...`) | **15 members across 8 global countries** (India, Singapore, Germany, Canada, Japan, UK, UAE, France). Tests leap-year birthdays (`2000-02-29`), birthday anniversaries on execution date, and flight freshness boundaries (89 days active, 90 days active, 91 days stale). |
| **`HD_MOVES_AND_UPDATES_20240120.txt`** | Pipe-delimited | **Country Move & Tier Upgrade**: Member `1000000015` moves from India to Australia with a newer file timestamp (`20240120`); Member `1000000001` tier upgraded from `GLD` to `PLT`. |
| **`AUS_Sheet1.csv`** | CSV | String literal `"NULL"` in DOB, invalid month `2021-13-13` in enrollment date without crashing. |
| **`IND_Feed.csv`** | CSV | Slash dates `M/D/YYYY` (`12/1/1998`) and corporate/individual flags (`I`/`C`). |
| **`USA_Feed.csv`** | CSV | Compact numeric dates `[M]MDDYYYY` (`6152022`, `1052022`) and missing DOB column. |
| **`redemptions_feed.json`** | JSON Array | 8 transactions across different partners (Air India, Singapore Airlines, Lufthansa, Qantas, Emirates), including an **unmatched member** (`GHOST_MEMBER_99999`) and duplicate replay idempotency check. |

---

## 2. How to Run the Pipeline Locally

Run the following command in your terminal from the project root:

```bash
python run_pipeline.py --input-dir "practical_test_data" --as-of-date 2024-06-01 --db-path "practical_test.duckdb"
```

### What This Command Does:
- Scans `practical_test_data/` and parses all 6 files.
- Lands 38 raw payloads into the **Bronze** layer (`raw_landing_feed`).
- Standardizes 32 members into the **Silver** staging table (`staging_members`).
- Quarantines 3 fatally corrupted records into `quarantine_members`.
- Dynamically creates **10 country tables** in the **Gold** layer:
  - `Table_India` (6 members)
  - `Table_Australia` (5 members)
  - `Table_USA` (4 members)
  - `Table_Singapore` (2 members)
  - `Table_Germany` (2 members)
  - `Table_Canada` (2 members)
  - `Table_Japan` (2 members)
  - `Table_United_Kingdom` (2 members)
  - `Table_France` (1 member)
  - `Table_Uae` (1 member)
- Flattens 8 redemptions into `Table_Redemptions`.
- Joins redemptions with active member profiles (7 matched, 1 retained as `UNMATCHED_MEMBER`).
- Saves everything into a local database file: `practical_test.duckdb`.

---

## 3. How to Inspect Your Local Tables

You can inspect the results using Python or the DuckDB CLI.

### Option A: Using Quick Python One-Liners

#### 1. See all dynamically generated country tables:
```bash
python -c "import duckdb; con = duckdb.connect('practical_test.duckdb'); print([t[0] for t in con.execute(\"SHOW TABLES\").fetchall() if 'Table_' in t[0]])"
```

#### 2. Query active Singapore members:
```bash
python -c "import duckdb; con = duckdb.connect('practical_test.duckdb'); print(con.execute('SELECT member_id, member_name, tier_code, age, stale_member FROM Table_Singapore').df())"
```

#### 3. Query active German members:
```bash
python -c "import duckdb; con = duckdb.connect('practical_test.duckdb'); print(con.execute('SELECT member_id, member_name, tier_code, age, stale_member FROM Table_Germany').df())"
```

#### 4. Query the Redemptions Join (Matched vs Unmatched):
```bash
python -c "import duckdb; con = duckdb.connect('practical_test.duckdb'); print(con.execute('SELECT r.txn_id, r.member_id, m.member_name, m.country, r.partner, r.miles_redeemed, CASE WHEN m.member_id IS NULL THEN \'UNMATCHED_MEMBER\' ELSE \'MATCHED\' END AS match_status FROM Table_Redemptions r LEFT JOIN Current_Member_Profiles m ON r.member_id = m.member_id ORDER BY r.txn_id').df())"
```

#### 5. Inspect Non-Fatal Data Quality Warnings (`WARNING` in `staging_members`):
Shows members with minor defects (e.g. Jonathan Taylor with invalid month `2021-13-13`) where identity is preserved and bad date converted to `None`:
```bash
python -c "import duckdb; con = duckdb.connect('practical_test.duckdb'); print(con.execute('SELECT member_id, member_name, enrollment_date, validation_status, validation_reason FROM staging_members WHERE validation_status != \'VALID\'').df())"
```

#### 6. Inspect Fatal Corrupted Records (`QUARANTINE` in `quarantine_members`):
Shows records blocked from Gold country tables due to missing mandatory keys or malformed delimiter counts:
```bash
python -c "import duckdb; con = duckdb.connect('practical_test.duckdb'); print(con.execute('SELECT source_file_name, member_name, validation_status, validation_reason FROM quarantine_members').df())"
```

---

## 4. Run an Interactive Python Inspection Shell
To explore tables freely:
```bash
python
```
Then paste:
```python
import duckdb

con = duckdb.connect("practical_test.duckdb")

# 1. Total active members across all countries
print(con.execute("SELECT country, COUNT(*) FROM Current_Member_Profiles GROUP BY country ORDER BY 2 DESC").df())

# 2. Check stale vs active members
print(con.execute("SELECT member_name, country, last_flight_date, stale_member FROM Current_Member_Profiles ORDER BY last_flight_date").df())

# 3. Check redemptions joined with member profiles
print(con.execute("SELECT r.txn_id, r.member_id, m.member_name, m.country, r.partner, r.miles_redeemed, CASE WHEN m.member_id IS NULL THEN 'UNMATCHED_MEMBER' ELSE 'MATCHED' END AS match_status FROM Table_Redemptions r LEFT JOIN Current_Member_Profiles m ON r.member_id = m.member_id ORDER BY r.txn_id").df())

# 4. Check data quality warnings in staging (non-fatal)
print(con.execute("SELECT member_id, member_name, validation_status, validation_reason FROM staging_members WHERE validation_status != 'VALID'").df())

# 5. Check quarantined records (fatal missing keys / broken structure)
print(con.execute("SELECT source_file_name, member_name, validation_status, validation_reason FROM quarantine_members").df())
```
