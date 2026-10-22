-- ======================================================================
-- SKYPOINTS DATA PIPELINE: REDEMPTIONS & PROFILE JOIN
-- Compatible with Snowflake & DuckDB
-- ======================================================================

-- 1. Table_Redemptions: Idempotent transaction table
CREATE TABLE IF NOT EXISTS Table_Redemptions (
    txn_id                  VARCHAR(64) PRIMARY KEY, -- Enforces idempotency (no duplicate transactions)
    member_id               VARCHAR(32) NOT NULL,    -- Foreign key referencing loyalty member
    feed_date               DATE,
    txn_date                DATE,
    partner                 VARCHAR(100),
    miles_redeemed          INTEGER,
    status                  VARCHAR(50),             -- e.g. 'COMPLETED', 'PENDING'
    source_file_name        VARCHAR(255),
    source_file_timestamp   TIMESTAMP,
    ingested_at             TIMESTAMP,
    validation_status       VARCHAR(20),
    validation_reason       VARCHAR
);

-- ======================================================================
-- 2. JSON ARRAY FLATTENING (SNOWFLAKE NATIVE SYNTAX)
-- Flattens JSON document containing 'redemptions' array into transaction rows
-- ======================================================================
-- In Snowflake:
-- INSERT INTO Table_Redemptions
-- SELECT 
--     r.value:txn_id::VARCHAR AS txn_id,
--     f.raw_payload:member_id::VARCHAR AS member_id,
--     TO_DATE(f.raw_payload:feed_date::VARCHAR, 'YYYYMMDD') AS feed_date,
--     TO_DATE(r.value:txn_date::VARCHAR, 'YYYYMMDD') AS txn_date,
--     r.value:partner::VARCHAR AS partner,
--     r.value:miles_redeemed::INTEGER AS miles_redeemed,
--     r.value:status::VARCHAR AS status,
--     f.source_file_name,
--     f.source_file_timestamp,
--     CURRENT_TIMESTAMP AS ingested_at,
--     'VALID' AS validation_status,
--     NULL AS validation_reason
-- FROM raw_landing_feed f,
-- LATERAL FLATTEN(input => PARSE_JSON(f.raw_payload):redemptions) r
-- WHERE f.source_system = 'JSON_FEED';

-- ======================================================================
-- 3. PROFILE JOIN QUERY
-- Joins transactions with active member profiles, retaining 100% of rows
-- Unmatched transactions are flagged as 'UNMATCHED_MEMBER' rather than dropped
-- ======================================================================
CREATE OR REPLACE VIEW View_Redemptions_Joined_Members AS
SELECT 
    r.txn_id,
    r.txn_date,
    r.feed_date,
    r.partner,
    r.miles_redeemed,
    r.status AS txn_status,
    r.member_id,
    m.member_name,
    m.tier_code,
    m.country,
    CASE 
        WHEN m.member_id IS NULL THEN 'UNMATCHED_MEMBER' 
        ELSE 'MATCHED' 
    END AS match_status
FROM Table_Redemptions r
LEFT JOIN Current_Member_Profiles m ON r.member_id = m.member_id
ORDER BY r.txn_id;
