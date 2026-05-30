"""Generate test_cases.json from 人工优化/ CSV exports."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPT_DIR = ROOT / "人工优化"
OUT = Path(__file__).parent / "test_cases.json"


def main() -> None:
    cases = []
    for path in sorted(OPT_DIR.glob("LR-*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                cases.append(row)
    OUT.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(cases)} cases from {len(list(OPT_DIR.glob('LR-*.csv')))} requirement files to {OUT}")


if __name__ == "__main__":
    main()
