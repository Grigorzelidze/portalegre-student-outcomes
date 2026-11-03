#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
. ./scripts/env.sh
psql -v ON_ERROR_STOP=1 -f sql/00_schemas.sql
psql -v ON_ERROR_STOP=1 -f sql/10_raw.sql
psql -v ON_ERROR_STOP=1 -c "\\copy raw.student FROM 'data/src/for_copy.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8')"
psql -v ON_ERROR_STOP=1 -f sql/20_clean.sql
psql -v ON_ERROR_STOP=1 -f sql/30_marts.sql
psql -v ON_ERROR_STOP=1 -f sql/40_checks.sql
python3 checks/recompute.py
python3 checks/render.py
echo "build ok"
