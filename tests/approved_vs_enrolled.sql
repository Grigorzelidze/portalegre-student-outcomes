select *
from {{ ref('student') }}
where sem1_approved > sem1_enrolled
   or sem2_approved > sem2_enrolled
   or sem1_credited > sem1_enrolled
   or sem2_credited > sem2_enrolled
