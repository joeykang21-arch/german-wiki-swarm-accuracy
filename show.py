r"""Show wiki posts that contain some text. Read-only helper for checking findings by hand.

Usage (PowerShell, from the swarm-accuracy folder):
  python .\show.py "swarm says"
  python .\show.py "definitive" 2026-06-17
  python .\show.py "Mar30TooltipVerifier" 2026-06-20T04:5

Arguments:
  1st: text to find (not case-sensitive). Matches the post's text, its username, or its page name.
  2nd (optional): only show posts whose time starts with this (e.g. 2026-06-20 or 2026-06-20T04:5).
Shows only text the edit ADDED (not text already on the page).
"""
import json, sys, os

CORPUS = os.environ.get("CORPUS", r"..\WikiAgentSwarmInvestigation\agent-logs\prowiki\revisions.jsonl")

def added(r):
    lines = (r.get("body") or "").split("\n")
    for h in r.get("hunks") or []:
        if h["op"] in ("insert", "replace"):
            for i in range(h["b0"], min(h["b1"], len(lines))):
                if lines[i].strip():
                    yield lines[i].strip()

def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    text = sys.argv[1].lower()
    when = sys.argv[2] if len(sys.argv) > 2 else ""
    rows = []
    with open(CORPUS, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if when and not r["time"].startswith(when):
                continue
            meta = (r["label"] + " " + r["page_id"]).lower()
            for x in added(r):
                if text in x.lower() or text in meta:
                    rows.append((r["time"], r["label"], r["page_id"], x))
    rows.sort()
    for t, user, page, x in rows[:40]:
        print(f"{t}  user={user}  page={page}")
        print(f"    {x[:600]}\n")
    print(f"{len(rows)} matching lines" + (" (showing first 40)" if len(rows) > 40 else ""))

if __name__ == "__main__":
    main()