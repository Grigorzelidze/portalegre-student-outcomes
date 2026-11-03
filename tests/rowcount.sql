select count(*) as n
from {{ ref('student') }}
having count(*) <> 4424
