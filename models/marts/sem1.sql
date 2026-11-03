select grp, n_resolved, n_graduate, n_dropout
from (
    select
        'zero'::text as grp,
        count(*)::integer as n_resolved,
        count(*) filter (where target = 'Graduate')::integer as n_graduate,
        count(*) filter (where target = 'Dropout')::integer as n_dropout
    from {{ ref('student') }}
    where target in ('Graduate', 'Dropout')
      and sem1_enrolled > 0
      and sem1_approved = 0
    union all
    select
        'some'::text,
        count(*)::integer,
        count(*) filter (where target = 'Graduate')::integer,
        count(*) filter (where target = 'Dropout')::integer
    from {{ ref('student') }}
    where target in ('Graduate', 'Dropout')
      and sem1_enrolled > 0
      and sem1_approved > 0
) s
