select
    scholarship::text as level,
    count(*)::integer as n,
    count(*) filter (where target in ('Graduate', 'Dropout'))::integer as n_resolved,
    count(*) filter (where target = 'Graduate')::integer as n_graduate,
    count(*) filter (where target = 'Dropout')::integer as n_dropout
from {{ ref('student') }}
group by scholarship
