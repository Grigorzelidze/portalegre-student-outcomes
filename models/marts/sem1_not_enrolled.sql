select count(*)::integer as n
from {{ ref('student') }}
where sem1_enrolled = 0
