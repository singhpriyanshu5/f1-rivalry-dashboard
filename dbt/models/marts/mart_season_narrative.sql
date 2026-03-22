-- Thin passthrough: surfaces LLM-generated season narratives from RAW
-- into the ANALYTICS schema so Evidence can read them like any other mart.

select
    season,
    constructor_id,
    driver_1_code,
    driver_2_code,
    narrative_text,
    model_id,
    prompt_hash,
    generated_at
from {{ source('raw', 'raw_season_narratives') }}
