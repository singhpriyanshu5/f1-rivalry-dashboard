# LLM Season Narrative Feature — Implementation Plan

**Date**: 2026-03-22
**Status**: Planned

## Overview

Add an LLM-generated "AI Season Story" widget to the F1 Rivalry Dashboard. When a user selects a season + driver pairing, a catchy narrative summary appears at the top — synthesizing qualifying battles, race drama, momentum shifts, and DNF impact into 2-3 engaging paragraphs.

The narrative is **pre-generated** as part of the E2E pipeline (not on-the-fly), stored in Snowflake, and served to Evidence like any other data mart.

## Architecture

```
detect_rounds → ingest_rounds → dbt_run → generate_narratives → dbt_run_narratives → trigger_evidence_build
                                              │                        │
                                              ▼                        ▼
                                   RAW.RAW_SEASON_NARRATIVES    RAW_ANALYTICS.MART_SEASON_NARRATIVE
                                   (Claude Sonnet API call)     (dbt passthrough materialization)
```

- **LLM**: Claude Sonnet (`claude-sonnet-4-20250514`) via Anthropic Python SDK
- **Caching**: SHA-256 prompt hash — skip regeneration if mart data hasn't changed
- **Cost**: ~$0.009/pairing/run, ~$0.09/pipeline run, ~$4/full season

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `sql/snowflake_setup.sql` | Append | `RAW_SEASON_NARRATIVES` table DDL |
| `dbt/models/sources.yml` | Modify | Add `raw_season_narratives` source |
| `dbt/models/marts/mart_season_narrative.sql` | **New** | Thin passthrough model |
| `dbt/models/marts/schema.yml` | Modify | Add model + tests |
| `evidence/sources/snowflake/mart_season_narrative.sql` | **New** | Evidence source query |
| `airflow/dags/f1_pipeline_dag.py` | Modify | Add `generate_narratives` + `dbt_run_narratives` tasks |
| `airflow/requirements.txt` | Modify | Add `anthropic` package |
| `evidence/pages/index.md` | Modify | Narrative query, card widget, CSS |
| `.env.example` | Modify | `ANTHROPIC_API_KEY` placeholder |
| `airflow/docker-compose.yml` | Modify | Pass `ANTHROPIC_API_KEY` to container |

## Data Flow

1. **Query mart data** — `generate_narratives` task queries 5 marts (`season_summary`, `qualifying_h2h`, `race_h2h`, `points_trajectory`, `lap_pace_summary`) for each (season, constructor, pairing)
2. **Build prompt** — Structured prompt with verdicts, round-by-round stats, consistency scores, and tone instructions (150-250 words, punchy F1 analyst style)
3. **Cache check** — SHA-256 hash of prompt compared to stored `prompt_hash`; skip if unchanged
4. **LLM call** — Claude Sonnet generates the narrative
5. **Store** — DELETE+INSERT into `RAW.RAW_SEASON_NARRATIVES` (idempotent)
6. **Materialize** — `dbt_run_narratives` runs `dbt run --select mart_season_narrative` to push into `RAW_ANALYTICS`
7. **Display** — Evidence reads `mart_season_narrative`, renders styled card between driver legend and section nav

## Error Handling

- Missing `ANTHROPIC_API_KEY` → graceful skip, pipeline continues
- Claude API failure per pairing → caught, logged, loop continues
- Total API outage → old narratives remain, card still renders previous version
- No narrative exists → `{#if narrative.length > 0}` hides the card entirely
- Snowflake write failure → task fails (real infra issue, should alert)

## Snowflake DDL

```sql
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
```

## Frontend Widget

Positioned after driver legend, before section nav. Dark gradient card with "AI Season Story" badge, italic narrative text, and subtle timestamp. Matches existing `f1-` class naming convention and red/teal color palette.

## Backfill

No special logic needed — `generate_narratives` queries ALL pairings from `MART_SEASON_SUMMARY`. Running the DAG with existing 2024/2025 data generates narratives for all historical seasons. Completed seasons are generated once (prompt hash won't change since underlying data is static).
