-- ======================================================================
-- SKYPOINTS DATA PIPELINE: GOLD LAYER (COUNTRY TABLES & STATE ROUTER)
-- Compatible with Snowflake & DuckDB
-- ======================================================================

-- 1. Dynamic Physical Country Tables (Created idempotently per normalized country)
CREATE TABLE IF NOT EXISTS Table_India (
    member_id               VARCHAR(32) PRIMARY KEY,
    member_name             VARCHAR(255),
    enrollment_date         DATE,
    last_flight_date        DATE,
    tier_code               VARCHAR(10),
    agent_name              VARCHAR(255),
    state                   VARCHAR(50),
    country                 VARCHAR(50),
    post_code               VARCHAR(20),
    dob                     DATE,
    is_active               CHAR(1) DEFAULT 'A', -- 'A' = Active, 'I' = Inactive (superseded/moved)
    age                     INTEGER,
    stale_member            BOOLEAN,
    source_system           VARCHAR(50),
    source_file_name        VARCHAR(255),
    source_file_timestamp   TIMESTAMP,
    source_row_number       INTEGER,
    ingested_at             TIMESTAMP,
    validation_status       VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS Table_USA (
    member_id               VARCHAR(32) PRIMARY KEY,
    member_name             VARCHAR(255),
    enrollment_date         DATE,
    last_flight_date        DATE,
    tier_code               VARCHAR(10),
    agent_name              VARCHAR(255),
    state                   VARCHAR(50),
    country                 VARCHAR(50),
    post_code               VARCHAR(20),
    dob                     DATE,
    is_active               CHAR(1) DEFAULT 'A',
    age                     INTEGER,
    stale_member            BOOLEAN,
    source_system           VARCHAR(50),
    source_file_name        VARCHAR(255),
    source_file_timestamp   TIMESTAMP,
    source_row_number       INTEGER,
    ingested_at             TIMESTAMP,
    validation_status       VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS Table_Australia (
    member_id               VARCHAR(32) PRIMARY KEY,
    member_name             VARCHAR(255),
    enrollment_date         DATE,
    last_flight_date        DATE,
    tier_code               VARCHAR(10),
    agent_name              VARCHAR(255),
    state                   VARCHAR(50),
    country                 VARCHAR(50),
    post_code               VARCHAR(20),
    dob                     DATE,
    is_active               CHAR(1) DEFAULT 'A',
    age                     INTEGER,
    stale_member            BOOLEAN,
    source_system           VARCHAR(50),
    source_file_name        VARCHAR(255),
    source_file_timestamp   TIMESTAMP,
    source_row_number       INTEGER,
    ingested_at             TIMESTAMP,
    validation_status       VARCHAR(20)
);

-- ======================================================================
-- 2. STATE RESOLUTION ("LATEST RECORD WINS" SQL PATTERN)
-- Ranks multiple records by file timestamp, using source row number as tie-breaker
-- ======================================================================
CREATE OR REPLACE VIEW View_Latest_Member_State AS
WITH RankedMembers AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY 
                CASE 
                    WHEN source_system = 'HD_FEED' THEN member_id 
                    ELSE source_system || ':' || member_id 
                END
            ORDER BY 
                source_file_timestamp DESC,
                source_row_number DESC
        ) AS rank_order
    FROM staging_members
    WHERE validation_status != 'QUARANTINE'
)
SELECT * EXCLUDE (rank_order)
FROM RankedMembers
WHERE rank_order = 1;

-- ======================================================================
-- 3. UNIFIED ACTIVE MEMBER PROFILES VIEW
-- Combines active records across all country tables for joins and analytics
-- ======================================================================
CREATE OR REPLACE VIEW Current_Member_Profiles AS
SELECT member_id, member_name, enrollment_date, last_flight_date, tier_code, agent_name, state, country, post_code, dob, is_active, age, stale_member, source_system, source_file_name, source_file_timestamp, source_row_number, ingested_at, validation_status
FROM Table_India WHERE is_active = 'A'
UNION ALL
SELECT member_id, member_name, enrollment_date, last_flight_date, tier_code, agent_name, state, country, post_code, dob, is_active, age, stale_member, source_system, source_file_name, source_file_timestamp, source_row_number, ingested_at, validation_status
FROM Table_USA WHERE is_active = 'A'
UNION ALL
SELECT member_id, member_name, enrollment_date, last_flight_date, tier_code, agent_name, state, country, post_code, dob, is_active, age, stale_member, source_system, source_file_name, source_file_timestamp, source_row_number, ingested_at, validation_status
FROM Table_Australia WHERE is_active = 'A';
