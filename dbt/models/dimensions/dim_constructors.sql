select distinct
    constructor_id,
    constructor_name
from {{ ref('stg_qualifying') }}
where constructor_id is not null
