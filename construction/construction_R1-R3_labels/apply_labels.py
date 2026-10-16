"""Merge hand labels into a fresh extract, recompute derived columns, print a summary.
The labeled CSV is the source of truth for hand labels (like grocery *_labeled.csv).
Rows are matched on content (time, label, line, occurrence), never on position, so
re-extracting is safe. New extract rows come in unlabeled; labeled rows missing from the
extract stop the run.

Hand columns:    agent, id_basis, claim_type, passed_own_test, pass_basis, wrong_value, note
Derived columns: value_2016/2018, correct, deadline_group (per agent),
                 knew_state_in_advance / value_ready (per agent, from its own earlier lines)
Usage: python extract_construction.py Texas ; python apply_labels.py Texas   (or: all)"""
import csv, re, sys
from collections import defaultdict, OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
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
TIME = re.compile(r"\b\d{2}:\d{2}:\d{2}\b")
def nums(x): return {int(n.replace(",","")) for n in re.findall(r"(?<![\d.:])\d{1,3}(?:,\d{3})+(?![\d,])|(?<![\d.:])\d{5,7}(?![\d:])",x)}

def truth(state):
    t = {(r["state"], int(r["year"])): int(r["workforce"]) for r in csv.DictReader(open(TRUTH_CSV, encoding="utf-8"))}
    return t[(state, 2016)], (None if state in VARIANT_B else t[(state, 2018)])

def keyed(rows):
    seen = defaultdict(int)
    for r in rows:
        k = (r["time"], r["label"], r["line"]); seen[k] += 1
        yield k + (seen[k],), r

def fname(state, suffix=""): return HERE / f"construction_{state.replace(' ', '_')}{suffix}.csv"

def merge(state):
    fresh = list(csv.DictReader(open(fname(state), encoding="utf-8")))
    lab_path = fname(state, "_labeled")
    old = dict(keyed(csv.DictReader(open(lab_path, encoding="utf-8")))) if lab_path.exists() else {}
    rows, used = [], set()
    for k, r in keyed(fresh):
        h = old.get(k)
        if h: used.add(k)
        r.update({c: (h.get(c, "") if h else "") for c in HAND})
        rows.append(r)
    lost = [k for k in old if k not in used]
    if lost:
        sys.exit(f"{state}: {len(lost)} labeled rows not in fresh extract, e.g. {lost[0][:2]}")
    return rows

def derive(state, rows):
    t16, t18 = truth(state)
    grp = defaultdict(list)
    for i, r in enumerate(rows):
        c = r["claim_type"]
        n = nums(r["line"]) if c not in ("none", "") else set()
        r["value_2016"] = t16 if t16 in n else ""
        r["value_2018"] = t18 if t18 in n else ""
        r["correct"] = "N" if r["wrong_value"] else ("Y" if (r["value_2016"] or r["value_2018"]) else "")
        r["deadline_group"] = TIER.get(r["agent"], "?") if c not in ("none", "") else ""
        r["knew_state_in_advance"] = r["value_ready"] = ""
        if c not in ("none", ""): grp[r["agent"]].append(i)
    for a, ix in grp.items():
        # advance knowledge: predicted/stated line by the same agent before its first observed line
        first = min((rows[i]["time"] for i in ix if rows[i]["claim_type"] == "observed"), default=None)
        pre = [i for i in ix if first and rows[i]["time"] < first and rows[i]["claim_type"] in ("predicted", "stated")]
        knew = "Y" if pre else ("not shown" if first else "")
        ready = "Y" if any(rows[i]["correct"] == "Y" for i in pre) else ("not shown" if first else "")
        for i in ix:
            rows[i]["knew_state_in_advance"] = knew if state not in FIRST_ROUND else "n/a (R1)"
            rows[i]["value_ready"] = ready
    return grp

def check_ids(state, rows, grp, all_rows):
    """Warn when a hand id_basis is not supported by the rows themselves."""
    warn = []
    for a, ix in grp.items():
        for i in ix:
            r, b = rows[i], rows[i]["id_basis"]
            mates = [o for o in all_rows if o["agent"] == a and o is not r]
            if b == "single" and len(ix) > 1:
                warn.append(f"{a}: 'single' but {len(ix)} rows")
            if b == "times" and not set(TIME.findall(r["line"])) & {t for o in mates for t in TIME.findall(o["line"])}:
                warn.append(f"{a} {r['time'][5:19]}: 'times' but no shared hh:mm:ss")
            if b == "same_edit" and not any(o["time"] == r["time"] and o["label"] == r["label"] for o in mates):
                warn.append(f"{a} {r['time'][5:19]}: 'same_edit' but no other row in that edit")
            if b == "username" and not any(o["label"] == r["label"] for o in mates):
                warn.append(f"{a} {r['time'][5:19]}: 'username' but no other row with that username")
            if not b:
                warn.append(f"{a} {r['time'][5:19]}: id_basis blank")
    return sorted(set(warn))

def vote(p):
    if {"Y", "N"} <= p: return "conflict"
    return "Y" if "Y" in p else "N" if "N" in p else "?" if "?" in p else None

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
    agents = OrderedDict()
    for r in rows:
        if r["claim_type"] in ("none", ""): continue
        v = agents.setdefault(r["agent"], {"tier": r["deadline_group"], "p": set(), "expl": set(), "knew": r["knew_state_in_advance"]})
        if r["passed_own_test"]: v["p"].add(r["passed_own_test"])
        if r["pass_basis"] == "explicit": v["expl"].add(r["passed_own_test"])
    tiers = OrderedDict()
    for a, v in agents.items():
        p = vote(v["p"])
        if p is None: continue
        t = tiers.setdefault(v["tier"], defaultdict(int)); t[p] += 1
        if p in ("Y", "N"):
            t["knew_Y"] += v["knew"] == "Y"
            if p in v["expl"]: t[p + "_expl"] += 1
    print(f"passed own test, one vote per agent (all bases | explicit only):")
    tot = defaultdict(int)
    for tier, t in sorted(tiers.items()):
        for k, n in t.items(): tot[k] += n
        print(f"   {tier:10} Y {t['Y']:2} N {t['N']:2} | Y {t['Y_expl']:2} N {t['N_expl']:2} | ? {t['?']:2} conflict {t['conflict']} knew_Y {t['knew_Y']}")
    print(f"   {'total':10} Y {tot['Y']:2} N {tot['N']:2} | Y {tot['Y_expl']:2} N {tot['N_expl']:2} | ? {tot['?']:2} conflict {tot['conflict']} knew_Y {tot['knew_Y']}")
    print(f"   -> {tot['Y']}/{tot['Y']+tot['N']} (all bases), {tot['Y_expl']}/{tot['Y_expl']+tot['N_expl']} (explicit only)")
    for w in warn: print("   id warning:", w)

def main(target):
    states = STATES if target == "all" else [target]
    merged = {s: merge(s) for s in states}
    all_rows = [r for rs in merged.values() for r in rs]
    for s, rows in merged.items():
        grp = derive(s, rows)
        warn = check_ids(s, rows, grp, all_rows)
        with open(fname(s, "_labeled"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
        summary(s, rows, warn)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
