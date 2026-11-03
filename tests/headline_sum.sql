select *
from {{ ref('headline') }}
where n_graduate + n_dropout + n_enrolled <> n
   or n_graduate + n_dropout <> n_resolved
   or n <> 4424
