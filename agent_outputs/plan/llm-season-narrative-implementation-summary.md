# LLM Season Narrative — Implementation Summary

**Date**: 2026-03-22
**Branch**: `feature/llm-season-narrative`
**Status**: Complete — all steps verified, ready for merge

## What Was Built

An "AI Season Story" widget on the F1 Rivalry Dashboard. For each season + driver pairing, Claude Sonnet generates a structured narrative summary covering qualifying battles, race-day drama, key moments, and a verdict. Narratives are pre-generated, stored in Snowflake, and served to Evidence like any other mart.

## Files Changed (12 total)

| File | Action | Purpose |
|------|--------|---------|
| `sql/snowflake_setup.sql` | Modified | Added `RAW.RAW_SEASON_NARRATIVES` table DDL |
| `dbt/models/sources.yml` | Modified | Added `raw_season_narratives` source |
| `dbt/models/marts/mart_season_narrative.sql` | **New** | Thin passthrough model (RAW → RAW_ANALYTICS) |
| `dbt/models/marts/schema.yml` | Modified | Added model definition + not_null tests |
| `evidence/sources/snowflake/mart_season_narrative.sql` | **New** | Evidence source query |
| `airflow/dags/f1_pipeline_dag.py` | Modified | Added `generate_narratives` + `dbt_run_narratives` tasks |
| `airflow/requirements.txt` | Modified | Added `anthropic==0.42.0` |
| `airflow/docker-compose.yml` | Modified | Pass `ANTHROPIC_API_KEY` to container |
| `.env.example` | Modified | Added `ANTHROPIC_API_KEY` placeholder |
| `evidence/pages/index.md` | Modified | Narrative query + `{@html}` card widget |
| `evidence/pages/+layout.svelte` | Modified | CSS for narrative card, hook, labels, bullets |
| `scripts/generate_narratives.py` | **New** | Standalone script for local testing |

## Architecture

```
detect_rounds → ingest_rounds → dbt_run → generate_narratives → dbt_run_narratives → trigger_evidence_build
                                              │                        │
                                              ▼                        ▼
                                   RAW.RAW_SEASON_NARRATIVES    RAW_ANALYTICS.MART_SEASON_NARRATIVE
                                   (Claude Sonnet API call)     (dbt passthrough)
```

## Key Design Decisions

- **Schema**: dbt creates marts in `RAW_ANALYTICS` (not `ANALYTICS`). Both DAG and standalone script reference `RAW_ANALYTICS.*` accordingly.
- **Caching**: SHA-256 hash of the full prompt (which includes all mart data). If mart data hasn't changed, prompt hash stays the same → no API call. Completed seasons are effectively free.
- **Structured HTML output**: LLM returns HTML with specific CSS classes (`f1-narrative-hook`, `f1-narrative-item`, `f1-narrative-label`). Evidence renders via `{@html}`.
- **Season-aware prompts**: Prompt includes whether a season is COMPLETED or IN-PROGRESS (`season < current_year`). In-progress seasons use qualifiers like "so far", "through X rounds" instead of definitive statements.
- **Third-person only**: Prompt explicitly forbids second-person ("you", "your") to avoid awkward phrasing.
- **Graceful degradation**: Missing `ANTHROPIC_API_KEY` → task skips. API failure per pairing → logged, loop continues. No narrative → card hidden via `{#if narrative.length > 0}`.
- **Idempotent writes**: DELETE + INSERT per (season, constructor, d1, d2).

## What Was Tested & Verified

- [x] Snowflake DDL executed — `RAW.RAW_SEASON_NARRATIVES` table created
- [x] Standalone script ran — 39 pairings across 2024/2025/2026 generated, 0 errors
- [x] Cache works — re-running without `--force` correctly skips all 39 (prompt hash match)
- [x] dbt materialization — `RAW_ANALYTICS.MART_SEASON_NARRATIVE` created successfully
- [x] Evidence source refresh — 39 rows pulled
- [x] Dashboard widget renders — structured card with hook sentence + labeled bullets
- [x] Widget responds to dropdown changes (season/constructor/pairing)
- [x] Card hides gracefully when no narrative exists
- [x] Narratives regenerated with final prompt (third-person + in-progress season rules) — 39/39 success, 0 errors
- [x] Airflow Docker image rebuilt with `anthropic==0.42.0` — build succeeded
- [x] `generate_narratives` Airflow task tested — connected to Snowflake, cache logic worked (39 cached), marked SUCCESS
- [x] `dbt_run_narratives` Airflow task tested — dbt ran `mart_season_narrative` inside container, PASS=1 ERROR=0, marked SUCCESS

## Additional UI Changes (post-initial implementation)

- **Dashboard title hierarchy**: "FORMULA 1" is now the biggest heading (3.2rem) with "1" in red, "TEAMMATE RIVALRY" appears as a smaller subtitle (1.4rem) beneath it — makes the F1 context immediately clear
- **Narrative card footer**: Replaced generation timestamp with round count context — now shows "Based on {N} rounds of {season} season data · Powered by {model_id}" so users know how much data the AI summary is based on

## Production Considerations

- Add `ANTHROPIC_API_KEY` to the production `.env` / secrets manager
- Cost estimate: ~$0.09 per pipeline run (only current-season pairings regenerate)
- Monitor for LLM output format drift — if Claude stops returning the expected HTML structure, the card may render incorrectly

## Optional Future Enhancements

- Add narrative quality validation (check for expected HTML structure before storing)
- Consider adding a round-level narrative (per race, not just per season)
