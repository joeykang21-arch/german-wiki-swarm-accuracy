r"""Summarize hand-labeled rows for one grocery state.

Usage (from the swarm-accuracy folder, venv active):
    python analyze_state.py Arkansas
Reads arkansas_labeled.csv (or georgia_labeled.csv, etc.).
"""
import re
import sys

import pandas as pd

TRUTH = {"Georgia": 90725, "Arkansas": 20794, "Nevada": 20369,
         "Kentucky": 34770, "Montana": 8553}

state = sys.argv[1].title() if len(sys.argv) == 2 else ""
if state not in TRUTH:
    sys.exit(f"Usage: python analyze_state.py <{'|'.join(TRUTH)}>")
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