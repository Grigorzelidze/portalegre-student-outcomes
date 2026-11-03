-- Bands are duplicated on purpose in checks/recompute.py.
select
    case
        when age_at_enrollment <= 20 then '<=20'
        when age_at_enrollment <= 23 then '21-23'
        when age_at_enrollment <= 26 then '24-26'
        else '27+'
    end as age_band,
    scholarship::text as scholarship,
    count(*) filter (where target in ('Graduate', 'Dropout'))::integer as n_resolved,
    count(*) filter (where target = 'Graduate')::integer as n_graduate
from {{ ref('student') }}
group by 1, 2
