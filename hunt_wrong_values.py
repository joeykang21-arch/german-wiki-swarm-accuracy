r"""Look for where the two wrong Georgia answers (97,484 and 103,532) came from.

Only two agents posted their wrong numbers:
  AgentProbeAssistantX2027  answered 103,532
  GrocerySequenceAgentApr27 answered  97,484
The right answer (2014, pums_5, Industry Group 4451, workforce only) is 90,725.

This tries the plausible wrong readings of the question and flags any value that
matches either number exactly or within 1%:
  1. same query, other years
  2. no workforce filter / workforce = false
  3. the 1-year cube (pums_1) instead of 5-year
  4. other industry groups in 2014 (wrong NAICS code)
  5. bigger industry levels (Sub-Sector 445, Sector 44-45) in 2014
  6. Georgia, all industry groups, all years
Each query is saved raw under truth/hunt_<stamp>/. A query that errors is reported
and skipped (some level names may differ).

Usage:  python hunt_wrong_values.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://api.datausa.io/tesseract/data.jsonrecords"
TARGETS = {97484: "Apr27", 103532: "AgentProbe"}
TRUE_GA = 90725
TOL = 0.01

BASE = {"locale": "en", "measures": "Total Population"}
QUERIES = {
    "A_allyears_workforce":   dict(cube="pums_5", drilldowns="State,Year",
                                   include="Industry Group:4451;Workforce Status:true"),
    "B_allyears_nofilter":    dict(cube="pums_5", drilldowns="State,Year",
                                   include="Industry Group:4451"),
    "C_allyears_notworkforce": dict(cube="pums_5", drilldowns="State,Year",
                                    include="Industry Group:4451;Workforce Status:false"),
    "D_pums1_workforce":      dict(cube="pums_1", drilldowns="State,Year",
                                   include="Industry Group:4451;Workforce Status:true"),
    "E_pums1_nofilter":       dict(cube="pums_1", drilldowns="State,Year",
                                   include="Industry Group:4451"),
    "F_2014_all_groups":      dict(cube="pums_5", drilldowns="State,Industry Group",
                                   include="Workforce Status:true;Year:2014"),
    "G_2014_subsectors":      dict(cube="pums_5", drilldowns="State,Industry Sub-Sector",
                                   include="Workforce Status:true;Year:2014"),
    "H_2014_sectors":         dict(cube="pums_5", drilldowns="State,Industry Sector",
                                   include="Workforce Status:true;Year:2014"),
    "I_GA_groups_allyears":   dict(cube="pums_5", drilldowns="State,Year,Industry Group",
                                   include="State:04000US13;Workforce Status:true"),
}

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
outdir = Path("truth") / f"hunt_{stamp}"
outdir.mkdir(parents=True, exist_ok=True)

hits, near = [], []
for name, q in QUERIES.items():
    try:
        r = requests.get(URL, params={**BASE, **q}, timeout=120)
        r.raise_for_status()
        rows = r.json().get("data", [])
    except Exception as e:  # noqa: BLE001
        print(f"{name}: FAILED ({e})")
        continue
    (outdir / f"{name}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{name}: {len(rows)} rows")

    # Georgia grocery by year, so you can see the nearby values.
    ga = [x for x in rows if x.get("State") == "Georgia"
          and str(x.get("Industry Group", "Grocery")).startswith("Grocery")]
    if ga and "Year" in ga[0]:
        series = ", ".join(f"{x['Year']}: {x['Total Population']:,}"
                           for x in sorted(ga, key=lambda x: x["Year"]))
        print(f"   Georgia 4451 -> {series}")

    for x in rows:
        v = x.get("Total Population")
        if not isinstance(v, (int, float)):
            continue
        for t, who in TARGETS.items():
            label = {k: x[k] for k in x if k not in ("Total Population",) and "ID" not in k}
            if v == t:
                hits.append((who, t, name, label))
            elif abs(v - t) / t <= TOL:
                near.append((who, t, round(v), name, label))

print("\n=== EXACT matches ===")
for h in hits or [("none", "", "", "")]:
    print(*h)
print(f"\n=== Within {TOL:.0%} (Georgia rows only) ===")
for n in near:
    if n[4].get("State") == "Georgia":
        print(*n)
print(f"\n(Within-1% rows in any state: {len(near)}; raw files in {outdir})")