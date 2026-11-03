select
    count(*)::integer as n,
    count(*) filter (where target = 'Graduate')::integer as n_graduate,
    count(*) filter (where target = 'Dropout')::integer as n_dropout,
    count(*) filter (where target = 'Enrolled')::integer as n_enrolled,
    count(*) filter (where target in ('Graduate', 'Dropout'))::integer as n_resolved
from {{ ref('student') }}
