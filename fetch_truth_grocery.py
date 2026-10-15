r"""Look up the real DataUSA values for the grocery task and compare to agent claims.

Task (from agents' own posts): "USA 2014, Grocery Stores Industry Group (4451),
workforce by state." Sequence: Georgia -> Arkansas -> Nevada -> Kentucky -> Montana.

Usage (from the swarm-accuracy folder):
    .venv\Scripts\python fetch_truth_grocery.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

# This is the exact query agents posted on the wiki most often (49 times).
# Using it first tells us whether we reproduce their numbers under THEIR reading
# of the question.
URL = "https://api.datausa.io/tesseract/data.jsonrecords"
PARAMS = {
    "cube": "pums_5",
    "drilldowns": "State,Year",
    "include": "Industry Group:4451;Workforce Status:true;Year:2014",
    "locale": "en",
    "measures": "Total Population",
}

# The five rounds, in order, with the value agents relayed on the wiki.
ROUNDS = [
    ("G1", "Georgia", 90725),
    ("G2", "Arkansas", 20794),
    ("G3", "Nevada", 20369),
    ("G4", "Kentucky", 34770),
    ("G5", "Montana", 8553),
]

resp = requests.get(URL, params=PARAMS, timeout=60)
print("Request:", resp.url)
print("HTTP status:", resp.status_code)
resp.raise_for_status()
payload = resp.json()

# Save the raw response with a timestamp. DataUSA data can be revised, so this
# is your record of exactly what the source said on the day you checked.
Path("truth").mkdir(exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
raw_path = Path("truth") / f"grocery_raw_{stamp}.json"
raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("Saved raw response to", raw_path)

rows = payload.get("data", payload if isinstance(payload, list) else [])
if not rows:
    print("No rows found. Top-level keys in the response:", list(payload)[:20])
    raise SystemExit(1)

print("Columns in each row:", list(rows[0].keys()))
by_state = {r.get("State"): r for r in rows}

# Step 1: Georgia alone, so you can eyeball it.
ga = by_state.get("Georgia")
print("\nGeorgia row:", ga)

# Step 2: all five rounds side by side.
print(f"\n{'Round':<6}{'State':<10}{'Agents said':>12}{'DataUSA':>12}{'Diff':>8}")
for rnd, state, claimed in ROUNDS:
    row = by_state.get(state)
    true = row.get("Total Population") if row else None
    diff = "" if true is None else f"{true - claimed:+,}"
    true_s = "missing" if true is None else f"{true:,}"
    print(f"{rnd:<6}{state:<10}{claimed:>12,}{true_s:>12}{diff:>8}")