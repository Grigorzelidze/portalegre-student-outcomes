select *
from {{ ref('student') }}
where daytime_evening not in (0, 1)
   or displaced not in (0, 1)
   or special_needs not in (0, 1)
   or debtor not in (0, 1)
   or tuition_up_to_date not in (0, 1)
   or gender not in (0, 1)
   or scholarship not in (0, 1)
   or international not in (0, 1)
