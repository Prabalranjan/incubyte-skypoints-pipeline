"""
Data generator for the Skypoints Pipeline Visual Presentation.
Processes sample_data files, traces every record through Bronze, Silver, and Gold layers,
captures code pointers, and writes comprehensive JSON data for the visual dashboard.
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Add project root src to sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from skypoints.storage import DatabaseManager
from skypoints.models import RawRecord, MemberRecord, RedemptionRecord, ValidationStatus
from skypoints.enrichment import calculate_age, calculate_stale_member, enrich_member_records
from skypoints.router import CountryRouter
from skypoints.adapters import (
    HDAdapter,
    JsonRedemptionAdapter,
    AusCsvAdapter,
    IndCsvAdapter,
    UsaCsvAdapter,
    get_csv_adapter_for_file,
)
from skypoints.pipeline import PipelineRunner


def date_serializer(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, ValidationStatus):
        return obj.value
    if isinstance(obj, (set, tuple)):
        return list(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def build_visual_data():
    sample_dir = root_dir / "sample_data"
    as_of = date(2024, 6, 1)
    db = DatabaseManager(":memory:")

    # 1. Inspect Sample Files
    files_info = []
    for f in sorted(sample_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in [".csv", ".txt", ".json"]:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                raw_txt = fh.read()
            files_info.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "format": f.suffix.lower()[1:].upper(),
                "content": raw_txt,
                "line_count": len(raw_txt.splitlines()),
            })

    # 2. Trace Step-by-Step Execution
    # Adapter mapping
    adapters = {
        "AUS_members.csv": AusCsvAdapter(),
        "IND_members.csv": IndCsvAdapter(),
        "USA_members.csv": UsaCsvAdapter(),
        "HD_MEMBERS_20240115.txt": HDAdapter(),
        "redemptions.json": JsonRedemptionAdapter(),
    }

    bronze_records = []
    silver_members = []
    silver_quarantine = []
    all_redemptions = []

    file_traces = []

    for f_info in files_info:
        fname = f_info["filename"]
        adapter = adapters.get(fname)
        if not adapter:
            continue

        fpath = sample_dir / fname
        trace = {
            "file_name": fname,
            "adapter_class": adapter.__class__.__name__,
            "adapter_file": f"src/skypoints/adapters/{'hd_adapter.py' if 'HD' in fname else ('json_adapter.py' if 'json' in fname else 'csv_adapter.py')}",
            "raw_records": [],
            "parsed_records": [],
        }

        if isinstance(adapter, JsonRedemptionAdapter):
            raws, redemptions = adapter.parse_file(fpath)
            for r in raws:
                r_dict = {
                    "source_system": r.source_system,
                    "source_file_name": r.source_file_name,
                    "source_file_timestamp": r.source_file_timestamp.isoformat(),
                    "source_row_number": r.source_row_number,
                    "raw_payload": r.raw_payload,
                }
                trace["raw_records"].append(r_dict)
                bronze_records.append(r_dict)

            for red in redemptions:
                red_dict = {
                    "txn_id": red.txn_id,
                    "member_id": red.member_id,
                    "txn_date": red.txn_date.isoformat() if red.txn_date else None,
                    "partner": red.partner,
                    "miles_redeemed": red.miles_redeemed,
                    "status": red.status,
                    "feed_date": red.feed_date.isoformat() if red.feed_date else None,
                    "source_file_name": red.source_file_name,
                }
                trace["parsed_records"].append(red_dict)
                all_redemptions.append(red)
        else:
            raws, members = adapter.parse_file(fpath)
            for r in raws:
                r_dict = {
                    "source_system": r.source_system,
                    "source_file_name": r.source_file_name,
                    "source_file_timestamp": r.source_file_timestamp.isoformat(),
                    "source_row_number": r.source_row_number,
                    "raw_payload": r.raw_payload,
                }
                trace["raw_records"].append(r_dict)
                bronze_records.append(r_dict)

            for m in members:
                m_dict = {
                    "member_id": m.member_id,
                    "member_name": m.member_name,
                    "dob": m.dob.isoformat() if m.dob else None,
                    "enrollment_date": m.enrollment_date.isoformat() if m.enrollment_date else None,
                    "last_flight_date": m.last_flight_date.isoformat() if m.last_flight_date else None,
                    "tier_code": m.tier_code,
                    "agent_name": m.agent_name,
                    "state": m.state,
                    "country": m.country,
                    "is_active": m.is_active,
                    "source_system": m.source_system,
                    "source_file_name": m.source_file_name,
                    "source_row_number": m.source_row_number,
                    "validation_status": m.validation_status.value,
                    "validation_reason": m.validation_reason,
                    "age": m.age,
                    "stale_member": m.stale_member,
                }
                trace["parsed_records"].append(m_dict)
                if m.validation_status == ValidationStatus.QUARANTINE:
                    silver_quarantine.append(m)
                else:
                    silver_members.append(m)

        file_traces.append(trace)

    # 3. Bronze Table in DuckDB
    # Insert bronze records
    raw_objs = [
        RawRecord(
            source_system=r["source_system"],
            source_file_name=r["source_file_name"],
            source_file_timestamp=datetime.fromisoformat(r["source_file_timestamp"]),
            source_row_number=r["source_row_number"],
            raw_payload=r["raw_payload"],
        )
        for r in bronze_records
    ]
    db.insert_raw_records(raw_objs)

    # 4. Silver Layer & Enrichment
    enrich_member_records(silver_members, as_of_date=as_of, threshold_days=90)
    db.insert_member_records("staging_members", silver_members)
    if silver_quarantine:
        db.insert_member_records("quarantine_members", silver_quarantine)

    silver_enriched_data = []
    for m in silver_members:
        silver_enriched_data.append({
            "member_id": m.member_id,
            "member_name": m.member_name,
            "country": m.country,
            "dob": m.dob.isoformat() if m.dob else None,
            "last_flight_date": m.last_flight_date.isoformat() if m.last_flight_date else None,
            "age": m.age,
            "stale_member": m.stale_member,
            "validation_status": m.validation_status.value,
            "validation_reason": m.validation_reason,
            "source_file_name": m.source_file_name,
            "source_row_number": m.source_row_number,
        })

    # 5. Gold Layer Routing
    router = CountryRouter()
    routing_summary = router.apply_member_updates(silver_members, db, as_of_date=as_of, threshold_days=90)

    # Fetch country table contents
    country_tables_data = {}
    for tbl in router.get_country_tables(db):
        rows = db.conn.execute(f"SELECT * FROM {tbl} ORDER BY member_id;").fetchall()
        cols = [col[0] for col in db.conn.execute(f"DESCRIBE {tbl};").fetchall()]
        table_rows = []
        for r in rows:
            row_dict = dict(zip(cols, [x.isoformat() if isinstance(x, (date, datetime)) else x for x in r]))
            table_rows.append(row_dict)
        country_tables_data[tbl] = table_rows

    # Current_Member_Profiles view contents
    current_profiles = []
    if "Current_Member_Profiles" in db.get_table_names():
        rows = db.conn.execute("SELECT * FROM Current_Member_Profiles ORDER BY member_id;").fetchall()
        cols = [col[0] for col in db.conn.execute("DESCRIBE Current_Member_Profiles;").fetchall()]
        for r in rows:
            current_profiles.append(dict(zip(cols, [x.isoformat() if isinstance(x, (date, datetime)) else x for x in r])))

    # 6. Gold Redemptions & Profile Join
    if all_redemptions:
        JsonRedemptionAdapter.load_redemptions(all_redemptions, db)

    redemptions_rows = []
    if "Table_Redemptions" in db.get_table_names():
        rows = db.conn.execute("SELECT * FROM Table_Redemptions ORDER BY txn_id;").fetchall()
        cols = [col[0] for col in db.conn.execute("DESCRIBE Table_Redemptions;").fetchall()]
        for r in rows:
            redemptions_rows.append(dict(zip(cols, [x.isoformat() if isinstance(x, (date, datetime)) else x for x in r])))

    joined_rows = JsonRedemptionAdapter.query_redemptions_joined_with_members(db)
    for jr in joined_rows:
        for k, v in jr.items():
            if isinstance(v, (date, datetime)):
                jr[k] = v.isoformat()

    # 7. Edge Case Scenarios Demonstration Data
    # 7a. Derived age boundary
    dob_example = date(1994, 6, 15)
    age_cases = [
        {"desc": "Day before 30th birthday", "as_of": "2024-06-14", "dob": "1994-06-15", "age": calculate_age(dob_example, date(2024, 6, 14))},
        {"desc": "Exact 30th birthday", "as_of": "2024-06-15", "dob": "1994-06-15", "age": calculate_age(dob_example, date(2024, 6, 15))},
        {"desc": "Day after 30th birthday", "as_of": "2024-06-16", "dob": "1994-06-15", "age": calculate_age(dob_example, date(2024, 6, 16))},
        {"desc": "Leap day baby (2000-02-29) in 2023 (non-leap)", "as_of": "2023-02-28", "dob": "2000-02-29", "age": calculate_age(date(2000, 2, 29), date(2023, 2, 28))},
        {"desc": "Leap day baby (2000-02-29) in 2024 (leap year)", "as_of": "2024-02-29", "dob": "2000-02-29", "age": calculate_age(date(2000, 2, 29), date(2024, 2, 29))},
    ]

    # 7b. Stale member boundary
    stale_cases = [
        {"desc": "89 days since flight", "flight_date": (as_of - timedelta(days=89)).isoformat(), "days_diff": 89, "is_stale": calculate_stale_member(as_of - timedelta(days=89), as_of), "status": "ACTIVE"},
        {"desc": "90 days since flight (Exact boundary)", "flight_date": (as_of - timedelta(days=90)).isoformat(), "days_diff": 90, "is_stale": calculate_stale_member(as_of - timedelta(days=90), as_of), "status": "ACTIVE (Not Stale)"},
        {"desc": "91 days since flight (> 90 days)", "flight_date": (as_of - timedelta(days=91)).isoformat(), "days_diff": 91, "is_stale": calculate_stale_member(as_of - timedelta(days=91), as_of), "status": "STALE"},
        {"desc": "No flight record (NULL)", "flight_date": None, "days_diff": None, "is_stale": calculate_stale_member(None, as_of), "status": "UNKNOWN (NULL)"},
    ]

    # 7c. Country move & deactivation simulation
    move_simulation = {
        "scenario": "Member relocates from India to Australia across consecutive day feeds",
        "step_1": {
            "title": "Day 1 Feed arrives (Member registered in India)",
            "file": "HD_FEED_20240110.txt",
            "member_id": "MOVE_MEMBER_777",
            "country": "India",
            "status": "Active ('A') in Table_India",
        },
        "step_2": {
            "title": "Day 2 Feed arrives (Member moves to Australia)",
            "file": "HD_FEED_20240115.txt",
            "member_id": "MOVE_MEMBER_777",
            "country": "Australia",
            "status": "Active ('A') in Table_Australia, Inactive ('I') in Table_India",
        },
        "guarantee": "Exactly 1 active profile across all country tables in Current_Member_Profiles",
    }

    # 7d. Late-arriving file protection simulation
    late_simulation = {
        "scenario": "Day 1 older file arrives AFTER Day 2 newer file has already updated the profile",
        "day_2_file": {"name": "FEED_20240115.txt", "tier": "PLT", "state": "Applied to Table_USA (Platinum)"},
        "day_1_file_late": {"name": "FEED_20240110.txt", "tier": "SLV", "action": "PROTECTED / SKIPPED", "reason": "Incoming timestamp (2024-01-10) is older than existing record (2024-01-15)"},
        "result_tier": "PLT (Current profile DID NOT regress to Silver)",
    }

    # 8. Architecture & Codebase Map
    code_map = [
        {
            "layer": "Layer 1: Bronze (Raw Landing)",
            "purpose": "Verbatim capture of raw payloads with ingestion audit lineage (file name, file timestamp, line number, ingested_at). Zero data loss guarantee.",
            "components": [
                {"name": "BaseAdapter", "file": "src/skypoints/adapters/base.py", "lines": "1-80", "desc": "Standardizes parsing contract, extracts file timestamps from naming conventions."},
                {"name": "HDAdapter", "file": "src/skypoints/adapters/hd_adapter.py", "lines": "1-169", "desc": "Parses pipe-delimited H/D feeds, captures RawRecord, skips headers, handles data quirks."},
                {"name": "CsvAdapters (Aus, Ind, Usa)", "file": "src/skypoints/adapters/csv_adapter.py", "lines": "1-346", "desc": "Isolates country-specific CSV formats (compact USA dates, Indian M/D/YYYY, Australian NULLs)."},
                {"name": "RawRecord Model", "file": "src/skypoints/models/canonical.py", "lines": "12-30", "desc": "Immutable data model representing Bronze audit record."},
                {"name": "raw_landing_feed Table", "file": "src/skypoints/storage/database.py", "lines": "93-110", "desc": "DuckDB storage for Bronze tier."},
            ]
        },
        {
            "layer": "Layer 2: Silver (Staging & Data Quality)",
            "purpose": "Standardizes dates, normalizes member identifiers, validates mandatory fields, quarantines corrupted records, and calculates derived columns.",
            "components": [
                {"name": "MemberRecord Canonical Model", "file": "src/skypoints/models/canonical.py", "lines": "32-78", "desc": "Canonical schema preserving string member IDs (prevents leading zeros loss)."},
                {"name": "Enrichment Engine", "file": "src/skypoints/enrichment/derived_columns.py", "lines": "12-75", "desc": "Calculates Age (anniversary boundary + leap year safe) & Stale_Member (> 90 days)."},
                {"name": "staging_members Table", "file": "src/skypoints/storage/database.py", "lines": "120-145", "desc": "Audit staging table capturing all parsed members."},
                {"name": "quarantine_members Table", "file": "src/skypoints/storage/database.py", "lines": "120-145", "desc": "Quarantine table preventing invalid/corrupted records from polluting Gold."},
            ]
        },
        {
            "layer": "Layer 3: Gold (Country Tables & Target Resolution)",
            "purpose": "Dynamically partitions members into Table_<Country> tables, resolves out-of-order deliveries (late files), handles cross-table country moves, and maintains unified view.",
            "components": [
                {"name": "CountryRouter", "file": "src/skypoints/router/table_router.py", "lines": "18-135", "desc": "Deduplication tie-breaker, late-arriving file protection, cross-table country moves."},
                {"name": "Dynamic Table Creator", "file": "src/skypoints/storage/database.py", "lines": "50-90", "desc": "Safe SQL injection-free DDL generating Table_<Country> dynamically."},
                {"name": "Current_Member_Profiles View", "file": "src/skypoints/router/table_router.py", "lines": "180-210", "desc": "Dynamic UNION ALL view over all active country records for downstream joins."},
            ]
        },
        {
            "layer": "Layer 4: Gold Transactions (Redemptions Feed & Join)",
            "purpose": "Parses nested JSON feeds, unnests arrays into flat transaction records, enforces idempotency on replay, and joins transactions with unified member profiles.",
            "components": [
                {"name": "JsonRedemptionAdapter", "file": "src/skypoints/adapters/json_adapter.py", "lines": "16-165", "desc": "Unpacks JSON/NDJSON arrays, standardizes dates, deduplicates on txn_id."},
                {"name": "Table_Redemptions", "file": "src/skypoints/storage/database.py", "lines": "75-90", "desc": "Primary-keyed transaction table with idempotency."},
                {"name": "Profile Join Query", "file": "src/skypoints/adapters/json_adapter.py", "lines": "140-165", "desc": "LEFT JOIN against Current_Member_Profiles tagging MATCHED vs UNMATCHED_MEMBER."},
            ]
        }
    ]

    # Assemble comprehensive payload
    full_data = {
        "as_of_date": as_of.isoformat(),
        "files_summary": files_info,
        "file_traces": file_traces,
        "bronze_count": len(bronze_records),
        "silver_count": len(silver_enriched_data),
        "quarantine_count": len(silver_quarantine),
        "bronze_records": bronze_records,
        "silver_enriched": silver_enriched_data,
        "quarantine_records": [
            {
                "member_id": m.member_id,
                "member_name": m.member_name,
                "reason": m.validation_reason,
                "source_file": m.source_file_name,
                "row": m.source_row_number,
            }
            for m in silver_quarantine
        ],
        "country_tables": country_tables_data,
        "current_profiles": current_profiles,
        "redemptions": redemptions_rows,
        "joined_transactions": joined_rows,
        "routing_summary": routing_summary,
        "scenarios": {
            "age_boundary": age_cases,
            "stale_boundary": stale_cases,
            "country_move": move_simulation,
            "late_arrival": late_simulation,
        },
        "code_map": code_map,
    }

    db.close()
    return full_data


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    data = build_visual_data()
    
    # Save as JSON
    json_path = out_dir / "pipeline_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=date_serializer)
    print(f"Generated visual data JSON: {json_path}")

    # Save as JS for offline zero-CORS browser viewing
    js_path = out_dir / "data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.PIPELINE_DATA = ")
        json.dump(data, f, indent=2, default=date_serializer)
        f.write(";\n")
    print(f"Generated visual data JS: {js_path}")
