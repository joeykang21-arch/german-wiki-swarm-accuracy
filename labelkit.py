"""Shared hand-label pipeline for the timed-sequence families (construction, french, ...).

The labeled CSV is the source of truth for hand labels. Rows are matched to a fresh extract on
content (time, label, line, occurrence), never on position, so re-extracting is safe. New extract
rows come in unlabeled; labeled rows missing from the extract stop the run.
Each family's apply_labels.py supplies its own value columns and truth; everything here is shared.
"""
import csv, re, sys
from collections import defaultdict

TIME = re.compile(r"\b\d{2}:\d{2}:\d{2}\b")


def keyed(rows):
    seen = defaultdict(int)
    for r in rows:
        k = (r["time"], r["label"], r["line"]); seen[k] += 1
        yield k + (seen[k],), r


def merge(state, fresh_path, labeled_path, hand):
    fresh = list(csv.DictReader(open(fresh_path, encoding="utf-8")))
    old = dict(keyed(csv.DictReader(open(labeled_path, encoding="utf-8")))) if labeled_path.exists() else {}
    rows, used = [], set()
    for k, r in keyed(fresh):
        h = old.get(k)
        if h: used.add(k)
        r.update({c: (h.get(c, "") if h else "") for c in hand})
        rows.append(r)
    lost = [k for k in old if k not in used]
    if lost:
        sys.exit(f"{state}: {len(lost)} labeled rows not in fresh extract, e.g. {lost[0][:2]}")
    return rows


def is_claim(r): return r["claim_type"] not in ("none", "")


def group(rows):
    grp = defaultdict(list)
    for i, r in enumerate(rows):
        if is_claim(r): grp[r["agent"]].append(i)
    return grp


def advance(rows, grp, first_round, correct_col="correct"):
    """knew_state_in_advance / value_ready: predicted/stated line by the same agent before its first observed line."""
    for r in rows: r["knew_state_in_advance"] = r["value_ready"] = ""
    for a, ix in grp.items():
        first = min((rows[i]["time"] for i in ix if rows[i]["claim_type"] == "observed"), default=None)
        pre = [i for i in ix if first and rows[i]["time"] < first and rows[i]["claim_type"] in ("predicted", "stated")]
        knew = "Y" if pre else ("not shown" if first else "")
        ready = "Y" if any(rows[i][correct_col] == "Y" for i in pre) else ("not shown" if first else "")
        for i in ix:
            rows[i]["knew_state_in_advance"] = knew if not first_round else "n/a (R1)"
            rows[i]["value_ready"] = ready


def check_ids(rows, grp, all_rows):
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


def conflicts(rows, col="passed_own_test"):
    return sorted(a for a in {r["agent"] for r in rows if is_claim(r)}
                  if vote({r[col] for r in rows if r["agent"] == a and r[col]}) == "conflict")


def write(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
