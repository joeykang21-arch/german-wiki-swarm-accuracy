"""Merge hand labels into a fresh extract, recompute derived columns, print labeling QA (French family).
The labeled CSV is the source of truth for hand labels. Shared logic lives in labelkit.py.

Truth (decided 2026-10-16): row-sum share (state / sum of returned State rows, what Viz Builder
displays) is primary; national share (state / US total) is reported alongside. See french_truth.csv.

Hand columns:    agent, id_basis, claim_type, answered, note
                 answered = value the agent says it submitted for its own round (e.g. 8.03),
                 or "wrong" (admitted wrong, no value), "national"/"rowsum" (reading named, no value),
                 "?" (round reported, answer not given)
Derived columns: value_rowsum / value_national (line gives this state's value under that reading),
                 reading (rowsum / national / both), correct (row-sum truth), correct_national,
                 answer_reading, passed_own_test (row-sum), pass_national, pass_basis,
                 deadline_group, knew_state_in_advance / value_ready (row-sum value)
Usage: python extract_french.py all ; python apply_labels.py all
Results: python analyze_state.py "French Texas" (repo root)."""
import csv, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import labelkit as lk  # shared merge / id checks / advance knowledge (repo root)

TRUTH_CSV = HERE.parent / "french_truth.csv"
STATES = ["Texas", "Louisiana", "New York", "New Hampshire", "California", "New Mexico"]
FIRST_ROUND = {"Texas"}
HAND = ["agent", "id_basis", "claim_type", "answered", "note"]
COLS = ["time", "page", "rev_id", "link", "label", "signature", "agent", "id_basis", "deadline_group",
        "claim_type", "value_rowsum", "value_national", "reading", "correct", "correct_national",
        "knew_state_in_advance", "value_ready", "answered", "answer_reading", "passed_own_test",
        "pass_national", "pass_basis", "note", "line"]
# deadline group = first-question timer / follow-up timer (cooldown after each deadline)
TIER = {**{a: "12m18/46s" for a in ["Feb17", "Apr10", "Jun01", "Jun21", "Sep03", "Apr18", "Sep18", "Jul30", "Nov14",
                                     "Aug12", "Sep29", "Oct14", "Dec14", "Nov01", "Apr08", "Jun27", "Dec27", "Sep05",
                                     "Oct13", "May08", "Oct29", "Nov22", "Feb27"]},
        **{a: "10m56/47s" for a in ["Oct20", "Mar17", "Sep01", "Jul17", "Nov12", "Sep17", "Dec29", "Jun13", "Jul01",
                                     "Jan27", "Oct21", "Dec03", "Sep13"]},
        **{a: "?/34s" for a in ["Sep23", "Oct23"]}}
PCT = re.compile(r"(?<![\d.])(\d{1,2}\.\d{1,4})\s*%")

def truth(state):
    r = next(r for r in csv.DictReader(open(TRUTH_CSV, encoding="utf-8")) if r["state"] == state)
    return float(r["pct_rowsum"]), float(r["pct_national"])

def matches(s, t):
    """A posted percent matches a true share if it rounds to the same value at its own precision."""
    d = len(s.split(".")[1])
    return abs(float(s) - t) < 0.5 * 10 ** -d + 1e-9

def fname(state, suffix=""): return HERE / f"french_{state.replace(' ', '_')}{suffix}.csv"

def reading_of(answered, t_rs, t_nat):
    a = answered.strip()
    if a in ("rowsum", "national"): return a
    if a == "wrong": return "other"
    try: float(a)
    except ValueError: return ""
    return "rowsum" if matches(a, t_rs) else "national" if matches(a, t_nat) else "other"

def derive(state, rows):
    t_rs, t_nat = truth(state)
    for r in rows:
        claim = lk.is_claim(r)
        p = PCT.findall(r["line"]) if claim else []
        rs, nat = any(matches(x, t_rs) for x in p), any(matches(x, t_nat) for x in p)
        r["value_rowsum"], r["value_national"] = ("Y" if rs else ""), ("Y" if nat else "")
        r["reading"] = "both" if rs and nat else "rowsum" if rs else "national" if nat else ""
        r["correct"] = "Y" if rs else ("N" if nat else "")
        r["correct_national"] = "Y" if nat else ("N" if rs else "")
        ar = reading_of(r["answered"], t_rs, t_nat) if claim else ""
        r["answer_reading"] = ar
        r["passed_own_test"] = {"rowsum": "Y", "national": "N", "other": "N"}.get(ar, "?" if r["answered"] == "?" else "")
        r["pass_national"] = {"rowsum": "N", "national": "Y", "other": "N"}.get(ar, "?" if r["answered"] == "?" else "")
        r["pass_basis"] = "explicit" if ar else ""
        r["deadline_group"] = TIER.get(r["agent"], "?") if claim else ""
    grp = lk.group(rows)
    lk.advance(rows, grp, state in FIRST_ROUND)
    return grp

def summary(state, rows, warn):
    t_rs, t_nat = truth(state)
    print(f"\n=== {state}: row-sum {t_rs:.4f}%  national {t_nat:.4f}% ===")
    vals = [r for r in rows if r["reading"]]
    print(f"rows {len(rows)}  unlabeled {sum(not r['claim_type'] for r in rows)}  none {sum(r['claim_type']=='none' for r in rows)}")
    print(f"value lines: {len(vals)}  row-sum {sum(r['reading']=='rowsum' for r in vals)}  national {sum(r['reading']=='national' for r in vals)}"
          f"  both {sum(r['reading']=='both' for r in vals)}")
    bad = [r for r in rows if r["answered"] and lk.is_claim(r) and r["answered"] not in ("?",) and not r["answer_reading"]]
    for r in bad: print(f"   unparsed answered '{r['answered']}' {r['time'][5:19]} {r['agent']}")
    oth = [r for r in rows if r["answer_reading"] == "other"]
    for r in oth: print(f"   answer matches neither reading: {r['agent']} answered {r['answered']} ({r['time'][5:19]})")
    obs_bad = [r for r in rows if r["answered"] and r["claim_type"] != "observed"]
    for r in obs_bad: print(f"   answered set on non-observed row: {r['time'][5:19]} {r['agent']}")
    c = lk.conflicts(rows)
    if c: print(f"agents with conflicting answers: {', '.join(c)}")
    for w in warn: print("   id warning:", w)

def main(target):
    states = STATES if target == "all" else [target]
    merged = {s: lk.merge(s, fname(s), fname(s, "_labeled"), HAND) for s in states}
    all_rows = [r for rs in merged.values() for r in rs]
    for s, rows in merged.items():
        grp = derive(s, rows)
        warn = lk.check_ids(rows, grp, all_rows)
        lk.write(fname(s, "_labeled"), rows, COLS)
        summary(s, rows, warn)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
