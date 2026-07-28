#!/usr/bin/env bash
# Fetch S&P 500 constituents and print company name, location, and founding year,
# sorted by founding year (ascending).

set -euo pipefail

CSV_URL="${1:-https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv}"

curl -fsSL "$CSV_URL" | python3 -c '
import csv
import re
import signal
import sys

signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def founding_year(raw: str) -> int:
    match = re.search(r"\d{4}", raw)
    if not match:
        raise ValueError(f"no year found in Founded field: {raw!r}")
    return int(match.group())

rows = []
for row in csv.DictReader(sys.stdin):
    rows.append(
        (
            founding_year(row["Founded"]),
            row["Security"],
            row["Headquarters Location"],
            row["Founded"],
        )
    )

rows.sort(key=lambda r: (r[0], r[1].lower()))

print("Year    Company                                   Location")
print("----    -------                                   --------")
for year, company, location, founded_raw in rows:
    print(f"{year:<6}  {company:<40}  {location}")
'
