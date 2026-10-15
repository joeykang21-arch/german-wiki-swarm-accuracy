r"""Pull every grocery-task line that could be a claim about one state,
and write them to a spreadsheet for labeling.

Usage (from the swarm-accuracy folder, venv active):
    python extract_state.py Arkansas
Output: arkansas_candidates.csv  (open in Excel)
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

CORPUS = Path(r"..\WikiAgentSwarmInvestigation\agent-logs\prowiki\revisions.jsonl")

# Grocery sequence: state -> (postal code, round label, true DataUSA value)
STATES = {
    "Georgia":  ("GA", "G1", 90725),
    "Arkansas": ("AR", "G2", 20794),
    "Nevada":   ("NV", "G3", 20369),
    "Kentucky": ("KY", "G4", 34770),
    "Montana":  ("MT", "G5", 8553),
}

if len(sys.argv) != 2 or sys.argv[1].title() not in STATES:
    sys.exit(f"Usage: python extract_state.py <{'|'.join(STATES)}>")
state = sys.argv[1].title()
code, rnd, true_value = STATES[state]
true_re = f"{true_value:,}".replace(",", ",?")      # 20,794 or 20794

GROCERY = re.compile(r"grocer|4451", re.I)
STATE = re.compile(rf"\b{state}\b|\b{code}\b|\b{rnd}\b|{true_re}")
NUMBER = re.compile(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{4,6}\b")


def added_text(r):
    body_lines = (r["body"] or "").split("\n")
    out = []
    for h in r["hunks"]:
        if h["op"] in ("insert", "replace"):
            out.extend(body_lines[h["b0"]:h["b1"]])
    return [l for l in out if l.strip()]


def explorer_link(rev_id):
    page, rev = rev_id.rsplit("@", 1)
    return f"https://collusion.wiki/explorer/page/{page}#rev-{rev}"


rows = []
with open(CORPUS, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        lines = added_text(r)
        if not lines or not GROCERY.search("\n".join(lines) + r["page_key"]):
            continue
        for text in lines:
            if not STATE.search(text):
                continue
            nums = [n for n in NUMBER.findall(text)
                    if not 2000 <= int(n.replace(",", "")) <= 2030]
            rows.append({
                "time": r["time"], "agent": r["label"], "rev_id": r["rev_id"],
                "link": explorer_link(r["rev_id"]), "text": text.strip(),
                "numbers_found": ", ".join(nums),
                # --- your labels (same scheme as Georgia, plus one) ---
                "is_state_claim": "", "value_claimed": "", "claim_type": "",
                "own_answer_wrong": "", "wrong_value": "",
                "knew_in_advance": "", "notes": "",
            })

df = pd.DataFrame(rows).sort_values("time")
df["times_posted"] = df.groupby("text")["text"].transform("count")
df = df.drop_duplicates(subset="text", keep="first").reset_index(drop=True)
out = f"{state.lower()}_candidates.csv"
df.to_csv(out, index=False, encoding="utf-8-sig")

print(f"{state} ({code}, round {rnd}, true value {true_value:,})")
print(f"Candidate lines (deduplicated): {len(df)}")
print(f"Lines containing {true_value:,}: {df['text'].str.contains(true_re).sum()}")
print(f"Wrote {out}")