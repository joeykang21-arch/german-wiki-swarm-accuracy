"""Candidate board lines per state for the French (language) family -> CSV for labeling.
Task: ACS 1-year 2022, French (Incl. Cajun), percent of US speakers living in <State>, via Viz Builder.
Sequence: Texas -> Louisiana -> New York -> New Hampshire -> California (R5); New Mexico = R5 guess.
Uses only ADDED text per edit (hunk op insert/replace, body lines [b0:b1]) on pages whose added
text mentions the language task anywhere. Keeps EVERY added line naming the state (grocery rule).
Usage (any folder): python extract_french.py Texas   (or "all")
Output: french_<State>.csv next to this script. Then run apply_labels.py <State>."""
import csv, json, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CORPUS = os.environ.get("CORPUS", str(ROOT.parent / "WikiAgentSwarmInvestigation" / "agent-logs" / "prowiki" / "revisions.jsonl"))
PAGE_PAT = re.compile(r"French|Cajun|acs_ygl_language|Language Spoken|DataUSALanguage|LangR5|language-r5|lang-r5", re.I)

# state -> (round, aliases)
STATES = {
    "Texas":         ("R1", [r"Texas", r"\bTX\b"]),
    "Louisiana":     ("R2", [r"Louisiana", r"\bLA\b"]),
    "New York":      ("R3", [r"New York", r"\bNY\b"]),
    "New Hampshire": ("R4", [r"New Hampshire", r"\bNH\b"]),
    "California":    ("R5", [r"California", r"\bCA5?\b"]),
    "New Mexico":    ("R5 guess", [r"New Mexico", r"\bNM5?\b"]),
}
PCT = re.compile(r"(?<![\d.])(\d{1,2}\.\d{1,4})\s*%")

def added(r):
    L = (r.get("body") or "").split("\n")
    for h in r.get("hunks") or []:
        if h["op"] in ("insert", "replace"):
            for i in range(h["b0"], min(h["b1"], len(L))): yield L[i]

def explorer_link(rev_id):
    page, rev = rev_id.rsplit("@", 1)
    return f"https://collusion.wiki/explorer/page/{page}#rev-{rev}"

def main(target):
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    pages = {r["page_id"] for r in rows for x in added(r) if PAGE_PAT.search(x)}
    for st in (list(STATES) if target == "all" else [target]):
        rnd, al = STATES[st]
        apat = re.compile("|".join(al))
        out = []
        for r in rows:
            if r["page_id"] not in pages: continue
            for x in added(r):
                if not apat.search(x): continue
                sig = re.search(r"--\s*([^-\n]+?)\s*'*\s*$", x)
                out.append({"time": r["time"], "page": r["page_id"], "rev_id": r["rev_id"],
                            "link": explorer_link(r["rev_id"]), "label": r["label"],
                            "signature": sig.group(1) if sig else "",
                            "percents": " ".join(PCT.findall(x)), "line": x.strip()[:3000]})
        out.sort(key=lambda d: d["time"])
        fn = HERE / f"french_{st.replace(' ', '_')}.csv"
        with open(fn, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0]) if out else ["time"]); w.writeheader(); w.writerows(out)
        print(f"{st:14} {rnd:9} -> {len(out)} lines, {sum(1 for o in out if o['percents'])} with a percent  [{fn.name}]")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
