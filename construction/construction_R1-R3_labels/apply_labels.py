"""Merge hand labels into a fresh extract, recompute derived columns, print labeling QA.
The labeled CSV is the source of truth for hand labels (like grocery *_labeled.csv).
Shared logic (content-keyed merge, id checks, advance knowledge) lives in labelkit.py.

Hand columns:    agent, id_basis, claim_type, passed_own_test, pass_basis, wrong_value, note
Derived columns: value_2016/2018, correct, deadline_group (per agent),
                 knew_state_in_advance / value_ready (per agent, from its own earlier lines)
Usage: python extract_construction.py Texas ; python apply_labels.py Texas   (or: all)
Results: python analyze_state.py Texas (repo root)."""
import csv, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import labelkit as lk  # shared merge / id checks / advance knowledge (repo root)
TRUTH_CSV = HERE.parents[1] / "construction_truth.csv"
STATES = ["New York", "California", "Texas", "Florida", "Nebraska",      # variant A: 2016 + 2018
          "Arizona", "Utah", "Colorado", "New Mexico"]                    # variant B: 2016 only
VARIANT_B = {"Arizona", "Utah", "Colorado", "New Mexico"}
FIRST_ROUND = {"New York", "Arizona"}
HAND = ["agent", "id_basis", "claim_type", "passed_own_test", "pass_basis", "wrong_value", "note"]
COLS = ["time", "page", "rev_id", "link", "label", "signature", "agent", "id_basis", "deadline_group",
        "claim_type", "value_2016", "value_2018", "other_numbers", "wrong_value", "correct",
        "knew_state_in_advance", "value_ready", "passed_own_test", "pass_basis", "note", "line"]
TIER={'Jun29':'10m/42s','Nov09':'10m/42s','Mar08':'10m/42s','Nov08':'10m/42s','Aug11':'10m/42s','May07':'10m/42s',
 'Dec17':'10m/42s','Oct07':'10m/42s','Feb26':'10m/42s','Dec11':'10m/42s','Dec11X':'10m/42s','Jul26':'10m/42s',
 'ArchiveA7/Jan05':'10m/42s','Mar19-b8dc':'10m/42s','Feb20-B8DC':'10m/42s','Dec23':'10m/42s','Jul12':'10m/42s',
 'May26-b8dc':'10m/42s','Feb23':'10m/42s',
 'Dec30':'6m40/14s','Apr02':'6m40/14s','Mar21':'6m40/14s','Jan20':'6m40/14s','Aug21':'6m40/14s','Sep11X':'6m40/14s',
 'Sep20X':'6m40/14s','Apr13':'6m40/14s','Nov05B':'6m40/14s','Nov05C':'6m40/14s','Oct22':'6m40/14s','Apr18':'6m40/14s',
 'Nov18':'6m40/14s','Oct21':'6m40/14s','Apr09':'6m40/14s','Feb25':'6m40/14s',
 'Jun03-lead':'5m39/11s','ResearchSep20':'5m39/11s','Sep11helper':'5m39/11s','Aug09':'5m39/11s','Mar06':'5m39/11s',
 'Jan03':'14m51/31s','Feb28':'14m51/31s','Jun15':'14m51/31s','Apr30':'14m51/31s','Apr12':'14m51/31s',
 'Nov19':'14m51/31s','Sep20W':'14m51/31s','Feb28A2':'14m51/31s','Mar07':'14m51/31s',
 'Jun20W':'14m51/31s','Apr07X':'14m51/31s',
 # variant B (AZ -> UT -> CO -> NM -> ?), 2016 only
 'Jun16':'3m12/6s','Jan01':'3m12/6s',
 'Dec27':'6m09/17s','Jul19':'6m09/17s','HelperNov18':'6m09/17s','Oct18':'6m09/17s','Dec03':'6m09/17s',
 'Dec03b':'6m09/17s','HelperJun03':'6m09/17s','Jan21':'6m09/17s','Jul27':'6m09/17s','Jul08':'6m09/17s'}
def nums(x): return {int(n.replace(",","")) for n in re.findall(r"(?<![\d.:])\d{1,3}(?:,\d{3})+(?![\d,])|(?<![\d.:])\d{5,7}(?![\d:])",x)}

def truth(state):
    t = {(r["state"], int(r["year"])): int(r["workforce"]) for r in csv.DictReader(open(TRUTH_CSV, encoding="utf-8"))}
    return t[(state, 2016)], (None if state in VARIANT_B else t[(state, 2018)])

def fname(state, suffix=""): return HERE / f"construction_{state.replace(' ', '_')}{suffix}.csv"

def derive(state, rows):
    t16, t18 = truth(state)
    for r in rows:
        c = r["claim_type"]
        n = nums(r["line"]) if c not in ("none", "") else set()
        r["value_2016"] = t16 if t16 in n else ""
        r["value_2018"] = t18 if t18 in n else ""
        r["correct"] = "N" if r["wrong_value"] else ("Y" if (r["value_2016"] or r["value_2018"]) else "")
        r["deadline_group"] = TIER.get(r["agent"], "?") if c not in ("none", "") else ""
    grp = lk.group(rows)
    lk.advance(rows, grp, state in FIRST_ROUND)
    return grp

def summary(state, rows, warn):
    t16, t18 = truth(state)
    print(f"\n=== {state}: truth {t16:,}" + (f" / {t18:,}" if t18 else " (2016 only)") + " ===")
    unl = [r for r in rows if not r["claim_type"]]
    vals = [r for r in rows if r["correct"]]
    print(f"rows {len(rows)}  unlabeled {len(unl)}  none {sum(r['claim_type']=='none' for r in rows)}")
    print(f"value lines: {len(vals)}  correct {sum(r['correct']=='Y' for r in vals)}  wrong {sum(r['correct']=='N' for r in vals)}"
          f"  (agents {len({r['agent'] for r in vals})}; first {min((r['time'] for r in vals), default='-')[:19]})")
    chk = [r for r in rows if r["other_numbers"] and r["claim_type"] not in ("none", "") and not r["wrong_value"]]
    if chk:
        print(f"lines with other numbers to check by hand: {len(chk)}")
        for r in chk: print(f"   {r['time'][5:19]} {r['agent']:14} [{r['other_numbers']}] {r['line'][:110]}")
    conflicts = lk.conflicts(rows)
    if conflicts: print(f"agents with conflicting pass labels: {', '.join(sorted(conflicts))}")
    for w in warn: print("   id warning:", w)
    print(f"results: python analyze_state.py \"{state}\" (from the repo root)")

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
