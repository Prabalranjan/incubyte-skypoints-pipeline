-- ======================================================================
-- SKYPOINTS DATA PIPELINE: BRONZE LAYER (RAW LANDING)
-- Compatible with Snowflake & DuckDB
-- ======================================================================

-- Raw Landing Table: Captures raw payload strings verbatim with lineage
CREATE TABLE IF NOT EXISTS raw_landing_feed (
    source_system           VARCHAR(50) NOT NULL,  -- e.g. 'HD_FEED', 'AUS_CSV', 'IND_CSV', 'USA_CSV', 'JSON_FEED'
    source_file_name        VARCHAR(255) NOT NULL, -- e.g. 'HD_MEMBERS_20240115.txt'
    source_file_timestamp   TIMESTAMP NOT NULL,    -- Timestamp extracted from filename or file arrival
    source_row_number       INTEGER NOT NULL,      -- Row index within file (deterministic tie-breaker)
    raw_payload             VARCHAR,               -- Raw unparsed line or raw JSON string
    ingested_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Ingestion audit timestamp
);
