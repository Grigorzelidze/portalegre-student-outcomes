.PHONY: data db build check test stop

PG_BIN ?= /tmp/pgsql/postgresql-18.6.1-aarch64-apple-darwin/bin

data:
	sh scripts/get_data.sh

db:
	PG_BIN="$(PG_BIN)" sh scripts/pg_local.sh start

build: db
	PG_BIN="$(PG_BIN)" sh scripts/build.sh

check:
	export PG_BIN="$(PG_BIN)"; . ./scripts/env.sh && python3 checks/recompute.py && python3 checks/render.py --check

test: db
	export PG_BIN="$(PG_BIN)"; . ./scripts/env.sh && python3 checks/test_controls.py

stop:
	PG_BIN="$(PG_BIN)" sh scripts/pg_local.sh stop
