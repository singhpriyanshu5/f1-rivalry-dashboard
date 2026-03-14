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

-- NOTE: S3 layer skipped. Data flows directly from API → Snowflake raw tables.
