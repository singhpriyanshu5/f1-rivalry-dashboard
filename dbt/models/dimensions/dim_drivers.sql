select distinct
    driver_id,
    driver_code,
    driver_name
from {{ ref('stg_qualifying') }}
where driver_id is not null
