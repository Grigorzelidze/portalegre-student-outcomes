#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
. ./scripts/env.sh
psql -v ON_ERROR_STOP=1 -f sql/00_schemas.sql
psql -v ON_ERROR_STOP=1 -f sql/10_raw.sql
psql -v ON_ERROR_STOP=1 -c "\\copy raw.student FROM 'data/src/for_copy.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8')"
if ! command -v dbt >/dev/null 2>&1; then
    USER_BIN=$(python3 -c 'import site; print(site.getuserbase() + "/bin")')
    PATH="$USER_BIN:$PATH"
    export PATH
fi
export DBT_PROFILES_DIR="$PWD"
export DBT_SEND_ANONYMOUS_USAGE_STATS=false
dbt build --project-dir "$PWD" --profiles-dir "$PWD"
psql -v ON_ERROR_STOP=1 -f sql/40_checks.sql
python3 checks/recompute.py
python3 checks/render.py
echo "build ok"
