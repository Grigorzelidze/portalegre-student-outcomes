select count(distinct target) as n
from {{ ref('student') }}
having count(distinct target) <> 3
