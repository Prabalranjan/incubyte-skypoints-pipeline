"""
Storage engine and DuckDB schema management for Skypoints Data Pipeline.
"""
import re
from typing import Optional, List, Dict, Any
import duckdb
import pandas as pd
from skypoints.models.canonical import RawRecord, MemberRecord, RedemptionRecord


class DatabaseManager:
    """Manages DuckDB connections, schema initializations, and dynamic table generation."""

    def __init__(self, database_path: str = ":memory:"):
        """Initialize database connection."""
        self.database_path = database_path
        self.conn = duckdb.connect(database_path)
        self.initialize_core_schemas()

    def initialize_core_schemas(self):
        """Set up Bronze raw landing, Silver staging, and Gold redemption schemas."""
        # 1. Bronze: Raw Landing Table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_landing_feed (
                source_system VARCHAR,
                source_file_name VARCHAR,
                source_file_timestamp TIMESTAMP,
                source_row_number INTEGER,
                raw_payload VARCHAR,
                ingested_at TIMESTAMP
            );
        """)

        # 2. Silver: Staging & Quarantine Tables
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS staging_members (
                member_id VARCHAR,
                member_name VARCHAR,
                enrollment_date DATE,
                last_flight_date DATE,
                tier_code VARCHAR,
                agent_name VARCHAR,
                state VARCHAR,
                country VARCHAR,
                post_code VARCHAR,
                dob DATE,
                is_active VARCHAR(1),
                age INTEGER,
                stale_member BOOLEAN,
                source_system VARCHAR,
                source_file_name VARCHAR,
                source_file_timestamp TIMESTAMP,
                source_row_number INTEGER,
                ingested_at TIMESTAMP,
                validation_status VARCHAR,
                validation_reason VARCHAR
            );
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS quarantine_members (
                member_id VARCHAR,
                member_name VARCHAR,
                enrollment_date DATE,
                last_flight_date DATE,
                tier_code VARCHAR,
                agent_name VARCHAR,
                state VARCHAR,
                country VARCHAR,
                post_code VARCHAR,
                dob DATE,
                is_active VARCHAR(1),
                age INTEGER,
                stale_member BOOLEAN,
                source_system VARCHAR,
                source_file_name VARCHAR,
                source_file_timestamp TIMESTAMP,
                source_row_number INTEGER,
                ingested_at TIMESTAMP,
                validation_status VARCHAR,
                validation_reason VARCHAR
            );
        """)

        # 3. Gold: Redemptions Target Table (Primary Key on txn_id ensures idempotency)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS Table_Redemptions (
                txn_id VARCHAR PRIMARY KEY,
                member_id VARCHAR,
                feed_date DATE,
                txn_date DATE,
                partner VARCHAR,
                miles_redeemed INTEGER,
                status VARCHAR,
                source_file_name VARCHAR,
                source_file_timestamp TIMESTAMP,
                ingested_at TIMESTAMP,
                validation_status VARCHAR,
                validation_reason VARCHAR
            );
        """)

    @staticmethod
    def sanitize_country_name(country: Optional[str]) -> str:
        """
        Normalize and sanitize country names into safe SQL table identifiers.
        E.g., 'IND' -> 'India', 'USA' -> 'USA', 'AU' -> 'Australia'.
        """
        if not country or not country.strip():
            return "Unassigned"

        clean = country.strip().upper()
        # Normalization mapping
        mapping = {
            "IND": "India",
            "INDIA": "India",
            "USA": "USA",
            "US": "USA",
            "UNITED STATES": "USA",
            "AU": "Australia",
            "AUS": "Australia",
            "AUSTRALIA": "Australia",
            "CAN": "Canada",
            "CANADA": "Canada",
            "PHIL": "Philippines",
            "PHILIPPINES": "Philippines",
        }
        normalized = mapping.get(clean, clean.title())
        # Replace non-alphanumeric characters with underscore
        sanitized = re.sub(r"[^A-Za-z0-9]", "_", normalized)
        # Collapse multiple underscores and strip boundary underscores
        sanitized = re.sub(r"_+", "_", sanitized).strip("_")
        return sanitized or "Unassigned"

    def create_country_table_if_not_exists(self, country: Optional[str]) -> str:
        """
        Dynamically generate safe, idempotent DDL for Table_<Country>.
        Returns the safe target table name.
        """
        sanitized_country = self.sanitize_country_name(country)
        table_name = f"Table_{sanitized_country}"

        # Safe parameterized execution (sanitized_country only contains [A-Za-z0-9_])
        ddl = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                member_id VARCHAR,
                member_name VARCHAR,
                enrollment_date DATE,
                last_flight_date DATE,
                tier_code VARCHAR,
                agent_name VARCHAR,
                state VARCHAR,
                country VARCHAR,
                post_code VARCHAR,
                dob DATE,
                is_active VARCHAR(1),
                age INTEGER,
                stale_member BOOLEAN,
                source_system VARCHAR,
                source_file_name VARCHAR,
                source_file_timestamp TIMESTAMP,
                source_row_number INTEGER,
                ingested_at TIMESTAMP,
                validation_status VARCHAR,
                PRIMARY KEY (member_id)
            );
        """
        self.conn.execute(ddl)
        return table_name

    def insert_raw_records(self, records: List[RawRecord]):
        """Bulk insert raw landing payloads into raw_landing_feed."""
        if not records:
            return
        dicts = [r.to_dict() for r in records]
        df = pd.DataFrame(dicts)
        self.conn.register("temp_raw_records", df)
        self.conn.execute("INSERT INTO raw_landing_feed SELECT * FROM temp_raw_records;")
        self.conn.unregister("temp_raw_records")

    def insert_member_records(self, table_name: str, records: List[MemberRecord]):
        """Insert member records into a specific target table."""
        if not records:
            return
        # Ensure target table exists if it is a dynamic country table
        if table_name.startswith("Table_"):
            country_part = table_name.replace("Table_", "")
            self.create_country_table_if_not_exists(country_part)

        dicts = [r.to_dict() for r in records]
        df = pd.DataFrame(dicts)
        columns = [col[0] for col in self.conn.execute(f"DESCRIBE {table_name};").fetchall()]
        cols_str = ", ".join(columns)
        self.conn.register("temp_member_records", df)

        # For Gold country tables, use INSERT OR REPLACE (deduplicate on member_id)
        # For Staging/Quarantine, use standard INSERT (append-only audit history)
        if table_name.startswith("Table_"):
            sql = f"INSERT OR REPLACE INTO {table_name} ({cols_str}) SELECT {cols_str} FROM temp_member_records;"
        else:
            sql = f"INSERT INTO {table_name} ({cols_str}) SELECT {cols_str} FROM temp_member_records;"

        self.conn.execute(sql)
        self.conn.unregister("temp_member_records")

    def insert_redemption_records(self, records: List[RedemptionRecord]):
        """Idempotently insert redemption records (upsert on txn_id)."""
        if not records:
            return
        dicts = [r.to_dict() for r in records]
        df = pd.DataFrame(dicts)
        columns = [col[0] for col in self.conn.execute("DESCRIBE Table_Redemptions;").fetchall()]
        cols_str = ", ".join(columns)
        self.conn.register("temp_redemptions", df)
        self.conn.execute(f"INSERT OR REPLACE INTO Table_Redemptions ({cols_str}) SELECT {cols_str} FROM temp_redemptions;")
        self.conn.unregister("temp_redemptions")

    def get_table_names(self) -> List[str]:
        """Fetch list of all user tables in the database."""
        result = self.conn.execute("SHOW TABLES;").fetchall()
        return [row[0] for row in result]

    def close(self):
        """Close connection."""
        self.conn.close()
