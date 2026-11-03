#!/bin/sh
# Local cluster unless the caller already pointed at Postgres (CI does).
if [ -z "${PGHOST:-}" ]; then
    ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
    export PGHOST=127.0.0.1
    export PGPORT=54332
    export PGUSER="${USER:-portalegre}"
    export PGDATABASE=portalegre
    export PGDATA="$ROOT/.pgdata"
fi
if [ -n "${PG_BIN:-}" ]; then
    PATH="$PG_BIN:$PATH"
    export PATH
fi
