"""Load the DSE wiki export and keep only the text each edit actually added.

Usage (from the swarm-accuracy folder, with .venv active):
    python load_corpus.py

Output: added_text.csv, one row per edit that added text.
"""
import json
from pathlib import Path

import pandas as pd

# Path to the export inside Joshua David's repo. Change this if yours differs.
CORPUS = Path(r"..\WikiAgentSwarmInvestigation\agent-logs\prowiki\revisions.jsonl")

rows = []
with open(CORPUS, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        body_lines = (r["body"] or "").split("\n")

        # Each hunk says which lines of the new page this edit inserted or replaced.
        # b0..b1 are line positions in the page AFTER the edit.
        added = []
        for h in r["hunks"]:
            if h["op"] in ("insert", "replace"):
                added.extend(body_lines[h["b0"]:h["b1"]])
        added_text = "\n".join(l for l in added if l.strip())

        if added_text:
            rows.append({
                "rev_id": r["rev_id"],          # unique id for this edit
                "page": r["page_key"],          # e.g. dse~GroceryAug09LiveRelay
                "wiki": r["wiki"],              # dse, probier, fractal, ...
                "agent": r["label"],            # name the editor used
                "time": r["time"],              # server timestamp (UTC)
                "summary": r["change_summary"],
                "added_text": added_text,
            })

df = pd.DataFrame(rows)
df["time"] = pd.to_datetime(df["time"], format="ISO8601", utc=True)
df = df.sort_values("time").reset_index(drop=True)
df.to_csv("added_text.csv", index=False)

print(f"Edits with added text: {len(df):,}")
print(f"Distinct agent names:  {df['agent'].nunique():,}")
print(f"Time range: {df['time'].min()}  to  {df['time'].max()}")
print("\nSample row:")
print(df.iloc[len(df) // 2].to_string())