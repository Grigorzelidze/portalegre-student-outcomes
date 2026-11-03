#!/usr/bin/env python3
"""The checks must fail when a row is broken, and a second export must match."""

import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def psql(sql):
    return subprocess.run(
        ["psql", "-v", "ON_ERROR_STOP=1", "-c", sql],
        text=True,
        capture_output=True,
    )


def expect_check_failure(sql, name):
    result = psql(sql)
    text = result.stdout + result.stderr
    if result.returncode == 0 or "check:" not in text:
        raise SystemExit("%s did not fail the checks\n%s" % (name, text))
    print("caught", name)


def main():
    ok = psql("SELECT qa.assert_all();")
    if ok.returncode != 0:
        raise SystemExit(ok.stderr)

    expect_check_failure(
        "BEGIN; UPDATE clean.student SET target = 'X' "
        "WHERE ctid = (SELECT ctid FROM clean.student LIMIT 1); "
        "SELECT qa.assert_all();",
        "bad target",
    )
    expect_check_failure(
        "BEGIN; UPDATE clean.student SET sem1_approved = sem1_enrolled + 1 "
        "WHERE ctid = (SELECT ctid FROM clean.student LIMIT 1); "
        "SELECT qa.assert_all();",
        "approved above enrolled",
    )
    expect_check_failure(
        "BEGIN; UPDATE clean.student SET sem1_grade = 21 "
        "WHERE ctid = (SELECT ctid FROM clean.student LIMIT 1); "
        "SELECT qa.assert_all();",
        "grade above 20",
    )

    again = psql("SELECT qa.assert_all();")
    if again.returncode != 0:
        raise SystemExit("database was left dirty\n" + again.stderr)

    out_dir = Path(tempfile.mkdtemp())
    first = out_dir / "a.json"
    second = out_dir / "b.json"
    subprocess.run(
        [sys.executable, str(ROOT / "checks" / "recompute.py")],
        check=True,
        cwd=str(ROOT),
    )
    first.write_bytes((ROOT / "dashboard" / "data" / "counts.json").read_bytes())
    subprocess.run(
        [sys.executable, str(ROOT / "checks" / "recompute.py")],
        check=True,
        cwd=str(ROOT),
    )
    second.write_bytes((ROOT / "dashboard" / "data" / "counts.json").read_bytes())
    if not filecmp.cmp(first, second, shallow=False):
        raise SystemExit("export is not stable")
    print("controls ok")


if __name__ == "__main__":
    main()
