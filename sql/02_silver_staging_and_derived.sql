-- ======================================================================
-- SKYPOINTS DATA PIPELINE: SILVER LAYER (STAGING & ENRICHMENT)
-- Compatible with Snowflake & DuckDB
-- ======================================================================

-- 1. Silver Staging Table: Standardized member records across all feeds
CREATE TABLE IF NOT EXISTS staging_members (
    member_id               VARCHAR(32),
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
    validation_status       VARCHAR(20),  -- 'VALID', 'WARNING'
    validation_reason       VARCHAR
);

-- 2. Silver Quarantine Table: Malformed rows and missing mandatory keys
CREATE TABLE IF NOT EXISTS quarantine_members (
    member_id               VARCHAR(32),
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
    validation_status       VARCHAR(20) DEFAULT 'QUARANTINE',
    validation_reason       VARCHAR
);

-- ======================================================================
-- DERIVED METRICS TRANSFORMATION VIEW
-- Computes completed years of Age and strict 90-day Stale Member flag
-- ======================================================================
CREATE OR REPLACE VIEW View_Enriched_Staging_Members AS
SELECT 
    member_id,
    member_name,
    enrollment_date,
    last_flight_date,
    tier_code,
    agent_name,
    state,
    country,
    post_code,
    dob,
    is_active,
    
    -- Exact Completed Years of Age (evaluating anniversary boundary)
    CASE 
        WHEN dob IS NULL THEN NULL
        WHEN dob > CURRENT_DATE THEN NULL
        ELSE 
            DATEDIFF('year', dob, CURRENT_DATE) - 
            CASE 
                WHEN (MONTH(CURRENT_DATE) < MONTH(dob)) OR 
                     (MONTH(CURRENT_DATE) = MONTH(dob) AND DAY(CURRENT_DATE) < DAY(dob)) 
                THEN 1 ELSE 0 
            END
    END AS age,

    -- Stale Member Flag: days since last flight > 90
    -- 90 days = FALSE, 91 days = TRUE, NULL if missing flight date
    CASE 
        WHEN last_flight_date IS NULL THEN NULL
        ELSE (DATEDIFF('day', last_flight_date, CURRENT_DATE) > 90)
    END AS stale_member,

    source_system,
    source_file_name,
    source_file_timestamp,
    source_row_number,
    ingested_at,
    validation_status
FROM staging_members
WHERE validation_status != 'QUARANTINE';
