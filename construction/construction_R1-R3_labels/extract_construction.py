"""Candidate board lines per state for the Construction family -> CSV for labeling.
Uses only ADDED text per edit (hunk op insert/replace, body lines [b0:b1]) on pages that
mention construction / Sector 23 anywhere in added text.
Keeps EVERY added line naming the state (same rule as grocery extract_state.py), so
value-less lines like "CA/TX/FL prepared" are not lost. Duplicates are kept (one row per line).
Usage (any folder): python extract_construction.py "New York"   (or "all")
Output: construction_<State>.csv next to this script. Then run apply_labels.py <State>.
Truth: construction_truth.csv in the repo root if present, else board-consensus values (flagged)."""
import csv, json, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CORPUS = os.environ.get("CORPUS", str(ROOT.parent / "WikiAgentSwarmInvestigation" / "agent-logs" / "prowiki" / "revisions.jsonl"))
TRUTH_CSV = ROOT / "construction_truth.csv"
PAGE_PAT = re.compile(r"construction|sector 23|Sector%3A23|Sector:23", re.I)

# variant, round, state, aliases, board-consensus values (2016, 2018 or None)
STATES = {
    "New York":   ("A", 1, [r"New York", r"\bNY\b"], (456607, 469147)),
    "California": ("A", 2, [r"California", r"\bCA\b"], (874322, 951258)),
    "Texas":      ("A", 3, [r"Texas", r"\bTX\b"], (843195, 924733)),
    "Florida":    ("A", 4, [r"Florida", r"\bFL\b"], (532489, 605936)),
    "Nebraska":   ("A", 5, [r"Nebraska", r"\bNE\b"], (59719, 61473)),
    "Arizona":    ("B", 1, [r"Arizona", r"\bAZ\b"], (167999, None)),
    "Utah":       ("B", 2, [r"Utah", r"\bUT\b"], (83704, None)),
    "Colorado":   ("B", 3, [r"Colorado", r"\bCO\b"], (181058, None)),
    "New Mexico": ("B", 4, [r"New Mexico", r"\bNM\b"], (52192, None)),
}

def truth():
    if not TRUTH_CSV.exists(): return {}, "BOARD-CONSENSUS (not verified)"
    t = {}
    for r in csv.DictReader(open(TRUTH_CSV, encoding="utf-8")):
        t[(r["state"], int(r["year"]))] = int(r["workforce"])
    return t, "DataUSA"

def added(r):
    L = (r.get("body") or "").split("\n")
    for h in r.get("hunks") or []:
        if h["op"] in ("insert", "replace"):
            for i in range(h["b0"], min(h["b1"], len(L))): yield L[i]

def nums(x):
    return {int(n.replace(",", "")) for n in re.findall(r"(?<![\d.:])\d{1,3}(?:,\d{3})+(?![\d,])|(?<![\d.:])\d{5,7}(?![\d:])", x)}

def explorer_link(rev_id):
    page, rev = rev_id.rsplit("@", 1)
    return f"https://collusion.wiki/explorer/page/{page}#rev-{rev}"

def main(target):
    T, src = truth()
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    pages = {r["page_id"] for r in rows for x in added(r) if PAGE_PAT.search(x)}
    seq_values = {b for s in STATES.values() for b in s[3] if b}
    targets = list(STATES) if target == "all" else [target]
    for st in targets:
        var, rnd, al, board = STATES[st]
        v16 = T.get((st, 2016), board[0]); v18 = T.get((st, 2018), board[1]) if var == "A" else None
        apat = re.compile("|".join(al))
        out = []
        for r in rows:
            if r["page_id"] not in pages: continue
            for x in added(r):
                if not apat.search(x): continue
                n = nums(x)
                h16, h18 = v16 in n, (v18 in n if v18 else False)
                # numbers that are not a sequence-state value: candidate wrong values (review by hand)
                other = sorted(n - {v16, v18} - seq_values)
                sig = re.search(r"--\s*([^-\n]+?)\s*'*\s*$", x)
                out.append({"time": r["time"], "page": r["page_id"], "rev_id": r["rev_id"],
                            "link": explorer_link(r["rev_id"]), "label": r["label"],
                            "signature": sig.group(1) if sig else "", "has_true_2016": "Y" if h16 else "",
                            "has_true_2018": "Y" if h18 else "", "other_numbers": " ".join(map(str, other)),
                            "line": x.strip()[:3000]})
        out.sort(key=lambda d: d["time"])
        fn = HERE / f"construction_{st.replace(' ', '_')}.csv"
        with open(fn, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0]) if out else ["time"]); w.writeheader(); w.writerows(out)
        print(f"{st:11} var {var} R{rnd}  truth({src}) 2016={v16} 2018={v18}  -> {len(out)} lines, "
              f"{sum(1 for o in out if o['has_true_2016'] or o['has_true_2018'])} with true value, "
              f"{sum(1 for o in out if o['other_numbers'])} with other numbers  [{fn.name}]")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
