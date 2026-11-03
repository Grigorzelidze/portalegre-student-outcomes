#!/usr/bin/env python3
"""Second calculation. Reads the CSV itself and requires the same counts as SQL."""

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "src" / "data.csv"
COUNTS_PATH = ROOT / "dashboard" / "data" / "counts.json"

COLUMNS = [
    "Marital status",
    "Application mode",
    "Application order",
    "Course",
    "Daytime/evening attendance",
    "Previous qualification",
    "Previous qualification (grade)",
    "Nacionality",
    "Mother's qualification",
    "Father's qualification",
    "Mother's occupation",
    "Father's occupation",
    "Admission grade",
    "Displaced",
    "Educational special needs",
    "Debtor",
    "Tuition fees up to date",
    "Gender",
    "Scholarship holder",
    "Age at enrollment",
    "International",
    "Curricular units 1st sem (credited)",
    "Curricular units 1st sem (enrolled)",
    "Curricular units 1st sem (evaluations)",
    "Curricular units 1st sem (approved)",
    "Curricular units 1st sem (grade)",
    "Curricular units 1st sem (without evaluations)",
    "Curricular units 2nd sem (credited)",
    "Curricular units 2nd sem (enrolled)",
    "Curricular units 2nd sem (evaluations)",
    "Curricular units 2nd sem (approved)",
    "Curricular units 2nd sem (grade)",
    "Curricular units 2nd sem (without evaluations)",
    "Unemployment rate",
    "Inflation rate",
    "GDP",
    "Target",
]


def age_band(age):
    if age <= 20:
        return "<=20"
    if age <= 23:
        return "21-23"
    if age <= 26:
        return "24-26"
    return "27+"


def load_frame(path):
    raw = path.read_bytes()
    if not raw.startswith(b"\xef\xbb\xbf"):
        raise SystemExit("expected a UTF-8 BOM at the start of data.csv")
    if b"attendance\t" not in raw.splitlines()[0]:
        raise SystemExit("expected a tab inside the daytime column name")
    frame = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    frame.columns = [name.replace("\t", "").strip() for name in frame.columns]
    if list(frame.columns) != COLUMNS:
        raise SystemExit("column names do not match the pinned file")
    if len(frame) != 4424:
        raise SystemExit("row count is %s, expected 4424" % len(frame))
    return frame


def group_rates(frame, column):
    rows = []
    for level, part in frame.groupby(column, sort=True):
        resolved = part[part["Target"].isin(["Graduate", "Dropout"])]
        rows.append(
            {
                "level": str(int(level)),
                "n": int(len(part)),
                "n_resolved": int(len(resolved)),
                "n_graduate": int((resolved["Target"] == "Graduate").sum()),
                "n_dropout": int((resolved["Target"] == "Dropout").sum()),
            }
        )
    return rows


def facts_from_frame(frame):
    resolved = frame[frame["Target"].isin(["Graduate", "Dropout"])]
    sem = resolved[resolved["Curricular units 1st sem (enrolled)"] > 0]
    zero = sem[sem["Curricular units 1st sem (approved)"] == 0]
    some = sem[sem["Curricular units 1st sem (approved)"] > 0]
    age_rows = []
    tmp = resolved.copy()
    tmp["age_band"] = tmp["Age at enrollment"].map(age_band)
    for (band, scholarship), part in tmp.groupby(
        ["age_band", "Scholarship holder"], sort=True
    ):
        age_rows.append(
            {
                "age_band": band,
                "scholarship": str(int(scholarship)),
                "n_resolved": int(len(part)),
                "n_graduate": int((part["Target"] == "Graduate").sum()),
            }
        )
    courses = []
    for course, part in frame.groupby("Course", sort=True):
        done = part[part["Target"].isin(["Graduate", "Dropout"])]
        courses.append(
            {
                "course": str(int(course)),
                "n": int(len(part)),
                "n_resolved": int(len(done)),
                "n_graduate": int((done["Target"] == "Graduate").sum()),
                "n_dropout": int((done["Target"] == "Dropout").sum()),
            }
        )
    courses.sort(key=lambda row: (-row["n"], int(row["course"])))
    admission = {}
    for level, part in frame.groupby("Scholarship holder", sort=True):
        admission[str(int(level))] = {
            "n": int(len(part)),
            "mean_grade": float(part["Admission grade"].mean()),
        }
    return {
        "n": int(len(frame)),
        "n_graduate": int((frame["Target"] == "Graduate").sum()),
        "n_dropout": int((frame["Target"] == "Dropout").sum()),
        "n_enrolled": int((frame["Target"] == "Enrolled").sum()),
        "n_resolved": int(len(resolved)),
        "tuition": group_rates(frame, "Tuition fees up to date"),
        "scholarship": group_rates(frame, "Scholarship holder"),
        "age_scholarship": age_rows,
        "sem1": {
            "zero": {
                "n_resolved": int(len(zero)),
                "n_graduate": int((zero["Target"] == "Graduate").sum()),
                "n_dropout": int((zero["Target"] == "Dropout").sum()),
            },
            "some": {
                "n_resolved": int(len(some)),
                "n_graduate": int((some["Target"] == "Graduate").sum()),
                "n_dropout": int((some["Target"] == "Dropout").sum()),
            },
            "not_enrolled": int((frame["Curricular units 1st sem (enrolled)"] == 0).sum()),
        },
        "courses": courses,
        "admission": admission,
    }


def query_sql():
    def run(sql):
        proc = subprocess.run(
            ["psql", "-v", "ON_ERROR_STOP=1", "--csv", "-c", sql],
            check=True,
            text=True,
            capture_output=True,
        )
        return list(csv.DictReader(proc.stdout.splitlines()))

    headline = run(
        "SELECT n, n_graduate, n_dropout, n_enrolled, n_resolved FROM mart.headline"
    )[0]
    tuition = run(
        "SELECT level, n, n_resolved, n_graduate, n_dropout "
        "FROM mart.by_tuition ORDER BY level"
    )
    scholarship = run(
        "SELECT level, n, n_resolved, n_graduate, n_dropout "
        "FROM mart.by_scholarship ORDER BY level"
    )
    age = run(
        "SELECT age_band, scholarship, n_resolved, n_graduate "
        "FROM mart.by_age_scholarship ORDER BY age_band, scholarship"
    )
    sem = run("SELECT grp, n_resolved, n_graduate, n_dropout FROM mart.sem1 ORDER BY grp")
    not_enrolled = run("SELECT n FROM mart.sem1_not_enrolled")[0]
    courses = run(
        "SELECT course, n, n_resolved, n_graduate, n_dropout "
        "FROM mart.by_course ORDER BY n DESC, course::integer"
    )
    admission = run(
        "SELECT scholarship, mean_grade, n FROM mart.admission ORDER BY scholarship"
    )
    sem_map = {row["grp"]: row for row in sem}
    return {
        "n": int(headline["n"]),
        "n_graduate": int(headline["n_graduate"]),
        "n_dropout": int(headline["n_dropout"]),
        "n_enrolled": int(headline["n_enrolled"]),
        "n_resolved": int(headline["n_resolved"]),
        "tuition": [ints(row, "level") for row in tuition],
        "scholarship": [ints(row, "level") for row in scholarship],
        "age_scholarship": [ints(row, "age_band", "scholarship") for row in age],
        "sem1": {
            "zero": ints(sem_map["zero"]),
            "some": ints(sem_map["some"]),
            "not_enrolled": int(not_enrolled["n"]),
        },
        "courses": [ints(row, "course") for row in courses],
        "admission": {
            row["scholarship"]: {
                "n": int(row["n"]),
                "mean_grade": float(row["mean_grade"]),
            }
            for row in admission
        },
    }


def ints(row, *keep):
    out = {}
    for key, value in row.items():
        if key == "grp":
            continue
        if key in keep:
            out[key] = value
        else:
            out[key] = int(value)
    return out


def compare(sql_facts, py_facts):
    keys = [
        "n",
        "n_graduate",
        "n_dropout",
        "n_enrolled",
        "n_resolved",
        "tuition",
        "scholarship",
        "age_scholarship",
        "sem1",
        "courses",
    ]
    for key in keys:
        if sql_facts[key] != py_facts[key]:
            raise SystemExit("SQL and pandas disagree on %s" % key)
    for level in ("0", "1"):
        if sql_facts["admission"][level]["n"] != py_facts["admission"][level]["n"]:
            raise SystemExit("admission count disagrees for scholarship %s" % level)
        if not math.isclose(
            sql_facts["admission"][level]["mean_grade"],
            py_facts["admission"][level]["mean_grade"],
            abs_tol=1e-4,
        ):
            raise SystemExit("admission mean disagrees for scholarship %s" % level)


def dump(facts):
    stored = json.loads(json.dumps(facts))
    for level in ("0", "1"):
        stored["admission"][level]["mean_grade"] = round(
            stored["admission"][level]["mean_grade"], 4
        )
    COUNTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    COUNTS_PATH.write_text(
        json.dumps(stored, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main():
    frame = load_frame(CSV_PATH)
    sql_facts = query_sql()
    compare(sql_facts, facts_from_frame(frame))
    dump(sql_facts)
    print("recompute ok", COUNTS_PATH)


if __name__ == "__main__":
    sys.exit(main())
