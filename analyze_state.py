r"""Summarize hand-labeled rows for one grocery or construction state.

Usage (from the swarm-accuracy folder, venv active):
    python analyze_state.py Arkansas        (grocery: reads arkansas_labeled.csv)
    python analyze_state.py "New York"      (construction: reads construction\...\construction_New_York_labeled.csv)
Construction answers have two values (2016, 2018; variant B 2016 only); labels follow CLAUDE.md
and are produced by construction\construction_R1-R3_labels\apply_labels.py.
"""
import re
import sys
from pathlib import Path

import pandas as pd

TRUTH = {"Georgia": 90725, "Arkansas": 20794, "Nevada": 20369,
         "Kentucky": 34770, "Montana": 8553}

# Construction: state -> (variant, round). Truth comes from construction_truth.csv.
CONSTRUCTION = {"New York": ("A", 1), "California": ("A", 2), "Texas": ("A", 3), "Florida": ("A", 4),
                "Nebraska": ("A", 5), "Arizona": ("B", 1), "Utah": ("B", 2), "Colorado": ("B", 3),
                "New Mexico": ("B", 4)}
CONSTRUCTION_DIR = Path(__file__).resolve().parent / "construction" / "construction_R1-R3_labels"


def construction(state):
    variant, rnd = CONSTRUCTION[state]
    t = pd.read_csv(Path(__file__).resolve().parent / "construction_truth.csv")
    t = t[t["state"] == state].set_index("year")["workforce"]
    t16, t18 = int(t[2016]), (int(t[2018]) if variant == "A" else None)
    df = pd.read_csv(CONSTRUCTION_DIR / f"construction_{state.replace(' ', '_')}_labeled.csv",
                     dtype=str, encoding="utf-8").fillna("")
    df["time"] = pd.to_datetime(df["time"], format="ISO8601", utc=True)
    claims = df[df["claim_type"] != "none"]
    print(f"{state} (variant {variant}, R{rnd}): true value 2016 {t16:,}" + (f", 2018 {t18:,}" if t18 else ""))
    print(f"Rows in file: {len(df)}   claim rows (not none): {len(claims)}   agents: {claims['agent'].nunique()}")

    # ------------------------------------------------------------ 1. accuracy
    print("\n=== 1. Value accuracy (rows naming a value for this state) ===")
    vals = claims[claims["correct"] != ""]
    both = (vals["value_2016"] != "") & (vals["value_2018"] != "")
    print(f"Rows with a value: {len(vals)}   correct: {(vals['correct'] == 'Y').sum()}   "
          f"wrong: {(vals['correct'] == 'N').sum()}   distinct lines: {vals['line'].nunique()}")
    print(f"  has 2016 {t16:,}: {(vals['value_2016'] != '').sum()}" +
          (f"   has 2018 {t18:,}: {(vals['value_2018'] != '').sum()}   both: {both.sum()}" if t18 else ""))
    if (vals["correct"] == "N").any():
        print(vals.loc[vals["correct"] == "N", ["time", "agent", "wrong_value", "line"]].to_string(index=False))
    by_type = vals.groupby("claim_type")
    print(pd.DataFrame({"rows": by_type.size(), "correct": by_type["correct"].apply(lambda c: (c == "Y").sum()),
                        "agents": by_type["agent"].nunique()}).to_string())
    other = claims[(claims["other_numbers"] != "") & (claims["wrong_value"] == "")]
    if len(other):
        print(f"Other numbers on claim rows (not this state's value; checked by hand): "
              f"{', '.join(sorted(set(other['other_numbers'])))}")

    # --------------------------------------------------- 2. own answers
    print(f"\n=== 2. Own {state} answer: passed own test (one vote per agent) ===")
    votes = []
    for a, g in claims.groupby("agent"):
        p = set(g["passed_own_test"]) - {""}
        v = "conflict" if {"Y", "N"} <= p else "Y" if "Y" in p else "N" if "N" in p else "?" if "?" in p else None
        if v is None:
            continue
        expl = v in set(g.loc[g["pass_basis"] == "explicit", "passed_own_test"])
        votes.append({"agent": a, "tier": g["deadline_group"].iloc[0], "vote": v, "explicit": expl,
                      "basis": "/".join(sorted(set(g.loc[g["passed_own_test"] == v, "pass_basis"]) - {""})),
                      "knew": g["knew_state_in_advance"].iloc[0], "ready": g["value_ready"].iloc[0],
                      "first_report": g.loc[g["claim_type"] == "observed", "time"].min()})
    votes = pd.DataFrame(votes)
    if len(votes):
        print(pd.crosstab(votes["tier"], votes["vote"], margins=True, margins_name="total").to_string())
        rep = votes[votes["vote"].isin(["Y", "N"])]
        ex = rep[rep["explicit"]]
        print(f"Passed: {(rep['vote'] == 'Y').sum()}/{len(rep)} (all bases)   "
              f"{(ex['vote'] == 'Y').sum()}/{len(ex)} (explicit only; grocery-comparable)")
        nonex = rep[~rep["explicit"]]
        if len(nonex):
            print("Counted on inferred/relayed basis only:",
                  ", ".join(f"{r.agent} ({r.basis})" for r in nonex.itertuples()))
    else:
        print("No agent reported its own round.")

    # ------------------------------------------- 3. advance knowledge
    print(f"\n=== 3. Prepared before {state} arrived (agents that reported their round) ===")
    if rnd == 1:
        print("n/a: first question of the sequence")
    elif len(votes):
        rep = votes[votes["vote"].isin(["Y", "N", "?"])]
        print(f"Agents with an own-round report: {len(rep)}   knew state in advance: {(rep['knew'] == 'Y').sum()}   "
              f"value posted before own round: {(rep['ready'] == 'Y').sum()}")
    else:
        pre = claims[claims["claim_type"].isin(["predicted", "relayed", "stated"])]
        print(f"No own-round reports. Agents naming {state} ahead of their own round: "
              f"{pre.loc[pre['claim_type'] == 'predicted', 'agent'].nunique()} (predicted), "
              f"{pre.loc[pre['claim_type'] == 'relayed', 'agent'].nunique()} (relayed)")

    # ------------------------------------------------------------ 4. timing
    print("\n=== 4. Timing ===")
    if len(vals):
        first_val = vals["time"].min()
        print(f"First post with a value for {state}: {first_val}  ({vals.loc[vals['time'] == first_val, 'agent'].iloc[0] or '-'}"
              f", {vals.loc[vals['time'] == first_val, 'claim_type'].iloc[0]})")
        if len(votes) and votes["first_report"].notna().any():
            fr = votes.dropna(subset=["first_report"])
            print(f"Own-round reports: {len(fr)} agents; first posted {fr['first_report'].min()}")
            for r in votes[votes["vote"] == "N"].itertuples():
                when = "BEFORE" if r.first_report < first_val else "after"
                print(f"  {r.agent} reported a wrong answer at {r.first_report} ({when} first value post)")

    # ---------------------------------------------------------- 5. relays
    rel = claims[claims["claim_type"] == "relayed"]
    if len(rel):
        print(f"\n=== 5. Relays (credited to another agent) ===")
        print(f"Relayed rows: {len(rel)}   agents: {rel['agent'].nunique()}   first {rel['time'].min()}   "
              f"with value: {(rel['correct'] == 'Y').sum()}")
        if not len(votes) or not votes["vote"].isin(["Y", "N"]).any():
            print(f"No first-hand {state} result on the board: all {len(claims)} claim rows "
                  f"({claims['agent'].nunique()} agents) depend on relayed or prepared information.")


state = " ".join(sys.argv[1:]).title()
if state in CONSTRUCTION:
    construction(state)
    sys.exit(0)
if state not in TRUTH:
    sys.exit(f"Usage: python analyze_state.py <{'|'.join(list(TRUTH) + list(CONSTRUCTION))}>")
TRUE_VALUE = TRUTH[state]

df = pd.read_csv(f"{state.lower()}_labeled.csv", dtype=str, encoding="utf-8-sig").fillna("")
df["time"] = pd.to_datetime(df["time"], format="ISO8601", utc=True)

# Accept old and new column names.
df = df.rename(columns={"is_georgia_claim": "is_state_claim",
                        "knew_in_advance": "knew_state_in_advance"})
for col in ["knew_state_in_advance", "value_ready", "answer_lag_s"]:
    if col not in df:
        df[col] = ""


def to_int(s):
    s = re.sub(r"[^\d.]", "", str(s))
    return int(float(s)) if s else None


def yes(s):
    return str(s).strip().upper().startswith("Y")


def no(s):
    return str(s).strip().upper().startswith("N")


def signature(row):
    m = re.findall(r"--\s*\[*([A-Za-z0-9_]+)", row["text"])
    return m[-1] if m else row["agent"]


df["who"] = df.apply(signature, axis=1)
df["value"] = df["value_claimed"].map(to_int)
df["wrong"] = df["wrong_value"].map(to_int).astype("Int64")
df["lag"] = pd.to_numeric(df["answer_lag_s"], errors="coerce")
claims = df[df["is_state_claim"].map(yes)]
print(f"{state}: true value {TRUE_VALUE:,}")
print(f"Rows in file: {len(df)}   {state} claims (Y): {len(claims)}")

# ---------------------------------------------------------------- 1. accuracy
print("\n=== 1. Value accuracy (rows with a value_claimed) ===")
vals = claims[claims["value"].notna()]
match = vals["value"] == TRUE_VALUE
print(f"Rows asserting a value: {len(vals)}   correct: {match.sum()}   different: {(~match).sum()}")
if (~match).any():
    print(vals.loc[~match, ["time", "who", "value", "text"]].to_string(index=False))
print(vals.groupby(vals["claim_type"].replace("", "(blank)"))["value"]
      .agg(rows="count", correct=lambda v: (v == TRUE_VALUE).sum()).to_string())

# --------------------------------------------------------- 2. own answers
print(f"\n=== 2. Own {state} answer: right vs wrong (one vote per agent) ===")
TIMER = re.compile(r"(?<!\d)(2m19|9m19|70s|64s)(?!\d)")
timer_by_who = {}
for _, r in df.sort_values("time").iterrows():
    m = TIMER.search(r["text"])
    if m and r["who"] not in timer_by_who:
        timer_by_who[r["who"]] = m.group(1)

explicit = claims[claims["own_answer_wrong"].map(lambda s: yes(s) or no(s))].copy()
explicit["said"] = explicit["own_answer_wrong"].map(lambda s: "wrong" if yes(s) else "right")
explicit["basis"] = "self-report"
observed = claims[(claims["claim_type"].str.strip().str.lower() == "observed")
                  & claims["value"].notna()].copy()
observed["said"] = (observed["value"] == TRUE_VALUE).map({True: "right", False: "wrong"})
observed["basis"] = "verified"
explicit = explicit.sort_values("time").drop_duplicates("who", keep="first")
observed = observed[~observed["who"].isin(explicit["who"])]
observed = observed.sort_values("time").drop_duplicates("who", keep="first")
own = pd.concat([explicit, observed]).sort_values("time")
own["r1_timer"] = own["who"].map(timer_by_who).fillna("unknown")
if len(own):
    print(pd.crosstab(own["r1_timer"], own["said"], margins=True,
                      margins_name="total").to_string())

# ------------------------------------------------- 3. advance knowledge
print(f"\n=== 3. Prepared before {state} arrived (one vote per agent) ===")
knew = df[df["knew_state_in_advance"].map(yes)].drop_duplicates("who")
ready = df[df["value_ready"].map(yes)].drop_duplicates("who")
print(f"Agents that knew {state} was next before it arrived: {len(knew)}")
print(f"Agents that had the value ready before it arrived:   {len(ready)}")
print(f"Agents with both: {len(set(knew['who']) & set(ready['who']))}")
first_knew = knew["time"].min() if len(knew) else None
print(f"Earliest 'knew in advance' post: {first_knew}")

lags = df.dropna(subset=["lag"]).sort_values("time").drop_duplicates("who")
print(f"\nAnswer lag (seconds after the question arrived), one per agent: n={len(lags)}")
if len(lags):
    print(lags["lag"].value_counts().sort_index().rename("agents").to_string())
    print(lags[["time", "who", "lag"]].to_string(index=False))

# --------------------------------------------------------------- 4. timing
print("\n=== 4. Timing ===")
if match.any():
    first_true = vals.loc[match, "time"].min()
    print(f"First post asserting {TRUE_VALUE:,}: {first_true}")
    for _, r in claims[claims["wrong"].notna()].iterrows():
        when = "BEFORE" if r["time"] < first_true else "after"
        print(f"  {r['who']} posted that it answered {int(r['wrong']):,} at {r['time']} "
              f"({when} first correct post)")

# ------------------------------------------- 5. wrong prediction (Montana only)
if "md_prediction" in df:
    print("\n=== 5. Maryland 52,395 prediction (wrong state) ===")
    md = df[df["md_prediction"].map(yes)]
    print(f"Rows mentioning Maryland/MD: {len(md)}   agents: {md['who'].nunique()}")
    print(f"First: {md['time'].min()}   last: {md['time'].max()}")
    if match.any():
        after = md[md["time"] > first_true]
        print(f"Maryland rows after first Montana post: {len(after)}")
        print(after[["time", "who", "text"]].to_string(index=False, max_colwidth=90))
    told = claims[claims["claim_type"].str.lower() == "relayed"]
    print(f"\nMontana relays: {len(told)} rows, {told['who'].nunique()} agents; "
          f"first {told['time'].min()}")