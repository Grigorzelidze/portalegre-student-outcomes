select *
from {{ ref('student') }}
where sem1_grade < 0 or sem1_grade > 20
   or sem2_grade < 0 or sem2_grade > 20
