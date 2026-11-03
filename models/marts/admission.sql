select
    scholarship::text as scholarship,
    avg(admission_grade)::float8 as mean_grade,
    count(*)::integer as n
from {{ ref('student') }}
group by scholarship
