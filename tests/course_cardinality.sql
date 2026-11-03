select count(distinct course) as n
from {{ ref('student') }}
having count(distinct course) <> 17
