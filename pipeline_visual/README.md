# SkyPoints Airline Loyalty Data Pipeline — Visual Presentation & Step-by-Step Guide

Welcome to the **SkyPoints Loyalty Data Pipeline Visual Presentation**. This folder contains an interactive, live visual dashboard that walks through every stage of the data pipeline using actual data from `sample_data/` and directly links each transformation to the exact file and lines of code responsible.

---

## 🚀 How to View the Visual Presentation

You have two easy ways to view the presentation:

### Option 1: Direct Browser View (Zero Setup)
Simply open [`index.html`](file:///d:/MY%20TASK/Incubyte/pipeline_visual/index.html) in any web browser (Chrome, Edge, Firefox, Safari).
- Data is bundled in `data.js`, so it loads instantly without any CORS issues or local server requirements.

### Option 2: Local HTTP Server
Run the lightweight server from your terminal:
```bash
python pipeline_visual/serve.py
```
Then visit: **`http://localhost:8080`**

### Re-generating Live Visual Data
If you update or add new sample files to `sample_data/`, refresh the visual data anytime by running:
```bash
python pipeline_visual/generate_visual_data.py
```

---

## 🧭 Pipeline Flow & Code Pointers

| Stage | Name | Key Functionality & Transformations | Responsible File & Code |
| :--- | :--- | :--- | :--- |
| **Stage 1** | **Source Ingestion & Discovery** | Scans `sample_data/`, inspects extensions, assigns modular adapters (`AusCsvAdapter`, `IndCsvAdapter`, `UsaCsvAdapter`, `HDAdapter`, `JsonRedemptionAdapter`). | [`src/skypoints/pipeline.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/pipeline.py#L43-L60)<br>[`src/skypoints/adapters/base.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/adapters/base.py)<br>[`src/skypoints/adapters/csv_adapter.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/adapters/csv_adapter.py) |
| **Stage 2** | **Bronze (Raw Landing)** | Verbatim capture of incoming lines with file name, file timestamp, line number, and load timestamp. Zero data loss. | [`src/skypoints/storage/database.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/storage/database.py#L93-L125)<br>[`src/skypoints/models/canonical.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/models/canonical.py#L12-L30)<br>[`sql/01_bronze_raw_landing.sql`](file:///d:/MY%20TASK/Incubyte/sql/01_bronze_raw_landing.sql) |
| **Stage 3** | **Silver (Quality & Derived)** | Cleans disparate date formats (`YYYY-MM-DD`, `M/D/YYYY`, `MMDDYYYY`), preserves string IDs with leading zeros, quarantines corrupted records, and derives `Age` (anniversary safe) and `Stale_Member` (`days > 90`). | [`src/skypoints/enrichment/derived_columns.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/enrichment/derived_columns.py#L12-L75)<br>[`src/skypoints/models/canonical.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/models/canonical.py#L32-L90)<br>[`sql/02_silver_staging_and_derived.sql`](file:///d:/MY%20TASK/Incubyte/sql/02_silver_staging_and_derived.sql) |
| **Stage 4** | **Gold (Country Routing & Moves)** | Dynamically generates `Table_<Country>` (`Table_Australia`, `Table_India`, `Table_USA`), deactivates prior country records upon relocation (`is_active = 'I'`), protects against late-arriving files, and creates unified view `Current_Member_Profiles`. | [`src/skypoints/router/table_router.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/router/table_router.py#L18-L135)<br>[`src/skypoints/storage/database.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/storage/database.py#L50-L90)<br>[`sql/03_gold_country_tables.sql`](file:///d:/MY%20TASK/Incubyte/sql/03_gold_country_tables.sql) |
| **Stage 5** | **Gold (JSON Redemptions & Join)** | Unnests nested JSON arrays into flat rows in `Table_Redemptions`, enforces idempotency on replay using `PRIMARY KEY (txn_id)`, and executes analytical `LEFT JOIN` against `Current_Member_Profiles` (retaining unmatched records). | [`src/skypoints/adapters/json_adapter.py`](file:///d:/MY%20TASK/Incubyte/src/skypoints/adapters/json_adapter.py#L16-L165)<br>[`sql/04_gold_redemptions_and_join.sql`](file:///d:/MY%20TASK/Incubyte/sql/04_gold_redemptions_and_join.sql) |
| **Stage 6** | **Edge-Case Simulators** | Interactive simulators to test Age anniversary boundary, strict 90-day flight staleness, cross-table moves, and out-of-order delivery protection. | Interactive in `index.html` via [`app.js`](file:///d:/MY%20TASK/Incubyte/pipeline_visual/app.js) |
| **Stage 7** | **Codebase & Architecture Map** | Full directory and symbol map linking directly to each file, class, method, and line number in the workspace. | Embedded in `index.html` |

---

## 🛡️ Git & Integrity Guarantee
- Everything created for this visual walkthrough is placed in `pipeline_visual/`.
- `pipeline_visual/` is listed in `.gitignore` so your Git status stays clean on `main` without pushing or branching.
- All 47 core automated tests in `tests/` remain 100% intact and passing.
