-- F1 Rivalry Dashboard — Snowflake Setup
-- Run with ACCOUNTADMIN role

USE ROLE ACCOUNTADMIN;

-- Database
CREATE DATABASE IF NOT EXISTS F1_ANALYTICS;
USE DATABASE F1_ANALYTICS;

-- Schemas
CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS STAGING;
CREATE SCHEMA IF NOT EXISTS ANALYTICS;

-- Warehouse
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
    WITH WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

USE WAREHOUSE COMPUTE_WH;

-- =============================================================================
-- Raw Tables (Jolpica API data)
-- =============================================================================

CREATE TABLE IF NOT EXISTS RAW.RAW_QUALIFYING (
    raw_data        VARIANT,
    season          INTEGER,
    round           INTEGER,
    _ingested_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file    VARCHAR,
    CONSTRAINT uq_qualifying UNIQUE (season, round)
);

CREATE TABLE IF NOT EXISTS RAW.RAW_RESULTS (
    raw_data        VARIANT,
    season          INTEGER,
    round           INTEGER,
    _ingested_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file    VARCHAR,
    CONSTRAINT uq_results UNIQUE (season, round)
);

CREATE TABLE IF NOT EXISTS RAW.RAW_SPRINT_RESULTS (
    raw_data        VARIANT,
    season          INTEGER,
    round           INTEGER,
    _ingested_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file    VARCHAR,
    CONSTRAINT uq_sprint_results UNIQUE (season, round)
);

CREATE TABLE IF NOT EXISTS RAW.RAW_DRIVER_STANDINGS (
    raw_data        VARIANT,
    season          INTEGER,
    round           INTEGER,
    _ingested_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file    VARCHAR,
    CONSTRAINT uq_standings UNIQUE (season, round)
);

-- =============================================================================
-- Raw Tables (OpenF1 API data)
-- =============================================================================

CREATE TABLE IF NOT EXISTS RAW.RAW_LAPS (
    raw_data            VARIANT,
    session_key         INTEGER,
    driver_number       INTEGER,
    lap_number          INTEGER,
    _ingested_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file        VARCHAR,
    CONSTRAINT uq_laps UNIQUE (session_key, driver_number, lap_number)
);

CREATE TABLE IF NOT EXISTS RAW.RAW_STINTS (
    raw_data            VARIANT,
    session_key         INTEGER,
    driver_number       INTEGER,
    stint_number        INTEGER,
    _ingested_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file        VARCHAR,
    CONSTRAINT uq_stints UNIQUE (session_key, driver_number, stint_number)
);

CREATE TABLE IF NOT EXISTS RAW.RAW_SESSIONS (
    raw_data            VARIANT,
    session_key         INTEGER,
    season              INTEGER,
    round               INTEGER,
    _ingested_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file        VARCHAR,
    CONSTRAINT uq_sessions UNIQUE (session_key)
);

CREATE TABLE IF NOT EXISTS RAW.RAW_PIT_STOPS (
    raw_data            VARIANT,
    session_key         INTEGER,
    driver_number       INTEGER,
    lap_number          INTEGER,
    _ingested_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file        VARCHAR,
    CONSTRAINT uq_pit_stops UNIQUE (session_key, driver_number, lap_number)
);

-- =============================================================================
-- Raw Tables (LLM-generated narratives)
-- =============================================================================

CREATE TABLE IF NOT EXISTS RAW.RAW_SEASON_NARRATIVES (
    season              INTEGER,
    constructor_id      VARCHAR,
    driver_1_code       VARCHAR(3),
    driver_2_code       VARCHAR(3),
    narrative_text      VARCHAR(16384),
    model_id            VARCHAR(100),
    prompt_hash         VARCHAR(64),
    generated_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT uq_narrative UNIQUE (season, constructor_id, driver_1_code, driver_2_code)
);

-- NOTE: S3 layer skipped. Data flows directly from API → Snowflake raw tables.
