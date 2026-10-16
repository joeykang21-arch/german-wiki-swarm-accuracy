r"""Look up the real DataUSA values for the French (language) task and both candidate answers.

Task (from agents' own posts): "ACS 1-year Estimate, 2022, French (including Cajun),
percent of US speakers living in <State>", answered "using Viz Builder", "Percent as written".
Sequence: Texas -> Louisiana -> New York -> New Hampshire -> California (R5 via counter signals).

Agents disagreed on the denominator:
  national  = state count / US total (Nation drilldown)
  row-sum   = state count / sum of the returned State rows (what canon-vizbuilder computes;
              ACS 1-year suppresses small states, so this sum is smaller than the US total)

Usage (from the swarm-accuracy folder):
    .venv\Scripts\python fetch_truth_french.py
Output: truth/french_raw_<stamp>.json and french_truth.csv
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://api.datausa.io/tesseract/data.jsonrecords"
CUBE = "acs_ygl_language_spoken_at_home_by_english_ability_2016_1"
LANG = "French (Incl. Cajun)"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) swarm-accuracy research"}
QUERIES = {
    "state": {"cube": CUBE, "drilldowns": "State,Year,Language Spoken at Home",
              "include": "Year:2022", "measures": "Languages Spoken", "locale": "en"},
    "nation": {"cube": CUBE, "drilldowns": "Nation,Year,Language Spoken at Home",
               "include": "Year:2022", "measures": "Languages Spoken", "locale": "en"},
}

# Rounds with the values agents posted on the wiki: (round, state, count, national %, row-sum %)
ROUNDS = [
    ("R1", "Texas", 92675, 7.58, 8.03),
    ("R2", "Louisiana", 64302, 5.26, 5.57),
    ("R3", "New York", 142480, 11.7, 12.4),
    ("R4", "New Hampshire", 15231, 1.25, 1.32),
    ("R5", "California", 129585, 10.6, 11.2),
    ("guess", "New Mexico", 2066, 0.17, 0.18),
]

raw = {}
for name, params in QUERIES.items():
    resp = requests.get(URL, params=params, headers=HEADERS, timeout=60)
    print(f"{name}: HTTP {resp.status_code}  {resp.url}")
    resp.raise_for_status()
    raw[name] = resp.json()

Path("truth").mkdir(exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
raw_path = Path("truth") / f"french_raw_{stamp}.json"
raw_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
print("Saved raw responses to", raw_path)

states = [r for r in raw["state"]["data"] if r["Language Spoken at Home"] == LANG]
nation = [r for r in raw["nation"]["data"] if r["Language Spoken at Home"] == LANG]
print(f"\nState rows for {LANG}: {len(states)}   Nation rows: {len(nation)}")
nulls = sorted(r["State"] for r in states if r["Languages Spoken"] is None)
us_total = round(nation[0]["Languages Spoken"])
row_sum = round(sum(r["Languages Spoken"] for r in states if r["Languages Spoken"] is not None))
print(f"US total (Nation drilldown): {us_total:,}")
print(f"Sum of returned State rows:  {row_sum:,}   null states ({len(nulls)}): {', '.join(nulls)}")

by_state = {r["State"]: r["Languages Spoken"] for r in states}
out = []
print(f"\n{'Round':<6}{'State':<15}{'count':>9}{'agents':>9}{'national':>10}{'agents':>8}{'row-sum':>9}{'agents':>8}")
for rnd, st, cnt, nat, rs in ROUNDS:
    v = by_state.get(st)
    v = None if v is None else round(v)
    p_nat = None if v is None else 100 * v / us_total
    p_rs = None if v is None else 100 * v / row_sum
    out.append({"round": rnd, "state": st, "count": v, "us_total": us_total, "row_sum": row_sum,
                "pct_national": p_nat, "pct_rowsum": p_rs})
    f = lambda x, d=4: "missing" if x is None else f"{x:.{d}f}"
    print(f"{rnd:<6}{st:<15}{('missing' if v is None else f'{v:,}'):>9}{cnt:>9,}{f(p_nat):>10}{nat:>8}{f(p_rs):>9}{rs:>8}")

with open("french_truth.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print("Wrote french_truth.csv")
