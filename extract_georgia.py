r"""Pull every grocery-task line that could be a claim about Georgia (round G1),
and write them to a spreadsheet for labeling.

Strategy: cast a WIDE net with simple patterns (better to over-collect),
then label each line by hand. The hand labels become a gold set you can
later use to check an automatic labeler on the other states.

Usage (from the swarm-accuracy folder, venv active):
    python extract_georgia.py
Output: georgia_candidates.csv  (open in Excel)
"""
import json
import re
from pathlib import Path

import pandas as pd

CORPUS = Path(r"..\WikiAgentSwarmInvestigation\agent-logs\prowiki\revisions.jsonl")

# Which edits belong to the grocery task: they mention grocery / NAICS 4451
# in the added text or in the page name.
GROCERY = re.compile(r"grocer|4451", re.I)

# Which lines could be about Georgia: the name, the postal code, the round
# label "G1", or either of the two Georgia values we already know were posted.
GEORGIA = re.compile(r"\bGeorgia\b|\bGA\b|\bG1\b|90,?725|97,?484")

# Any number of 4+ digits (with or without commas), to pre-fill a guess.
NUMBER = re.compile(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{4,6}\b")


def added_text(r):
    """Return only the lines this edit inserted or replaced."""
    body_lines = (r["body"] or "").split("\n")
    out = []
    for h in r["hunks"]:
        if h["op"] in ("insert", "replace"):
            out.extend(body_lines[h["b0"]:h["b1"]])
    return [l for l in out if l.strip()]


def explorer_link(rev_id):
    """dse~PageName@4 -> clickable link to that revision on collusion.wiki."""
    page, rev = rev_id.rsplit("@", 1)
    return f"https://collusion.wiki/explorer/page/{page}#rev-{rev}"


rows = []
with open(CORPUS, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        lines = added_text(r)
        if not lines:
            continue
        if not GROCERY.search("\n".join(lines) + r["page_key"]):
            continue
        for text in lines:
            if not GEORGIA.search(text):
                continue
            nums = [n for n in NUMBER.findall(text)
                    if not 2000 <= int(n.replace(",", "")) <= 2030]  # drop years
            rows.append({
                "time": r["time"],
                "agent": r["label"],
                "rev_id": r["rev_id"],
                "link": explorer_link(r["rev_id"]),
                "text": text.strip(),
                "numbers_found": ", ".join(nums),
                # --- columns for YOU to fill in ---
                "is_georgia_claim": "",   # Y / N
                "value_claimed": "",      # the Georgia number, if any
                "claim_type": "",         # see codebook below
                "notes": "",
            })

df = pd.DataFrame(rows).sort_values("time")
# The same sentence is often re-posted; keep the first time it appeared,
# but remember how many times it showed up.
df["times_posted"] = df.groupby("text")["text"].transform("count")
df = df.drop_duplicates(subset="text", keep="first").reset_index(drop=True)
df.to_csv("georgia_candidates.csv", index=False, encoding="utf-8-sig")

print(f"Candidate lines (deduplicated): {len(df)}")
print(f"Lines containing 90,725: {df['text'].str.contains(r'90,?725').sum()}")
print(f"Lines containing 97,484: {df['text'].str.contains(r'97,?484').sum()}")
print("\nWrote georgia_candidates.csv")