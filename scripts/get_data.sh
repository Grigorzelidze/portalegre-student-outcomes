#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p data/src
curl -fsSL -o data/src/uci697.zip \
    "https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip"
rm -f data/src/data.csv
unzip -o -j data/src/uci697.zip data.csv -d data/src
python3 - <<'PY'
import hashlib
from pathlib import Path
root = Path("data")
expected = {}
for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    digest, name = line.split()
    expected[name] = digest
src = root / "src"
for name in ("uci697.zip", "data.csv"):
    got = hashlib.sha256((src / name).read_bytes()).hexdigest()
    if got != expected[name]:
        raise SystemExit("hash mismatch for %s: %s" % (name, got))
raw = (src / "data.csv").read_bytes()
stripped = raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw
(src / "for_copy.csv").write_bytes(stripped)
print("data ok")
PY
