select
    status,
    category
from {{ ref('dnf_status_mapping') }}
