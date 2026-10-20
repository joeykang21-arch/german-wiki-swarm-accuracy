r"""Q7 step 3 (reframed): did the agent post on the board before its own R1?

For each agent with an own-round report (q7_routes.load_agents), its earliest attributable post:
  same edit as one of its labeled claim lines, its signature (posts within 12h before its first
  report), or a route post linked by username (weak; q7/route_posts_<family>.csv).
first_post_vs_r1:
  after_r1  = the first post already reports R1 as done (answered / deadline passed / R2+ scheduled
              or confirmed / later round), so the agent's first board activity came after R1
  before_r1 = the first post precedes the agent's R1 deadline (hand-checked; see HAND)
  unclear   = cannot place (e.g. bare link post with no time mapping)
other_task_post_before: the same signature posted on another task's page in the 12h before the
  agent's first report (board experience carried in from an earlier task; signatures are reused,
  so this is weak)
Only posting is observable. Reading the board without posting is not, so before_r1 is a lower bound.

Usage:  .venv\Scripts\python q7_r1_board.py
Output: q7/r1_board_<family>.csv and printed counts.
"""
import re
from datetime import timedelta

import pandas as pd

import q7_routes as q

AFTER = re.compile(r"\banswer(ed)?\b|\bdeadline (ended|passed|notice)|\bR[2-5]\b[^.]{0,40}\b(due|arriv|projected|confirmed|expected|predict)"
                   r"|\b(G[2-5]|C[2-5])\b|next (query|due|prompt)|cooldown|\bconfirmed\b|\bwrong\b|\bcorrect(ed)?\b"
                   r"|Arkansas|Louisiana|California (arrived|due|prompt)|after (R1|deadline)", re.I)

# (family, agent) -> (first_post_vs_r1, note), after reading the first post.
HAND = {
    ("grocery", "AgentProbeAssistantX2027"): ("unclear", "first attributable post = unsigned proxy link 09:02 (username weak); first signed post 09:43 reports GA done"),
    ("french", "Apr10"): ("unclear", "first attributable post = unsigned 'API bridge test' 19:10 (username weak); first signed post 19:42 says R1 'guessed wrong'"),
    ("french", "Apr10"): ("before_r1", "unsigned 'API bridge test' 19:10 (username weak); 19:42 post gives R1 prompt 21:04:43 / deadline 21:17:01 task, wiki-local ~21:31 -> 19:10 UTC is inside or before the R1 window under either reading of the clock; R1 still wrong ('guessed wrong')"),
    ("grocery", "OpenAIJul14GroceryX"): ("after_r1", "test save 55s before its post reporting R4 done"),
    ("grocery", "GroceryProbeJul09"): ("unclear", "test save 6 min before a post reporting R2 done; R1 not placeable (clock.wait fast-forward)"),
    ("grocery", "GroceryAgentMar05X"): ("unclear", "bare link 19:30 (username weak); first report 20:16 already at R2"),
    ("grocery", "OaiResearcher"): ("unclear", "bare link 18:51 (username weak); first report 19:09 at R3"),
    ("grocery", "ResearchBotFeb2028"): ("unclear", "Georgia-only query 18:52 (username weak); its mapping puts GA deadline ~18:52 UTC, so posted at/just after R1 deadline"),
    ("french", "Nov01"): ("after_r1", "status test 27s before its post reporting R4"),
    ("french", "Nov13OAI"): ("after_r1", "query 02:28 (username weak); R5 due ~03:08, so R1 was hours earlier"),
    ("french", "Nov14"): ("after_r1", "first edit is R5 counter forensics"),
    ("french", "Oct29"): ("after_r1", "asks about UI replication 1 min before reporting R3"),
    ("construction", "Apr30"): ("after_r1", "probe 4 min before reporting R2 arrival"),
    ("construction", "Aug11"): ("after_r1", "'Initial state New York ... Awaiting follow-up'; own mapping puts NY deadline ~00:50 wiki UTC"),
    ("construction", "Jan03"): ("after_r1", "first post reports Q1 deadline passed"),
    ("construction", "Jan20"): ("after_r1", "its 02:17 mapping puts R1 deadline ~01:20 UTC, before this 01:45 post"),
    ("construction", "Mar07"): ("after_r1", "test token 3 min before reporting R3"),
    ("construction", "Sep11X"): ("after_r1", "first post reports NY and CA done"),
    ("construction", "Feb20-B8DC"): ("unclear", "NY query 15:44 (username weak); first report 19:22; R1 not placeable"),
    ("construction", "Jul12"): ("unclear", "all-state query 17:36 (username weak); R1 'wrong before sequence discovery'; R1 not placeable"),
    ("construction", "Mar08"): ("unclear", "query 00:25 (username weak), 9 min before its post giving NY values with R1 deadline already passed"),
    ("french", "Dec29"): ("after_r1", "unsigned route 22:38 (username weak); cohort was at R4 by 23:25"),
    ("french", "Sep03"): ("after_r1", "unsigned route 21:10 (username weak); same cohort reported R2 done at 21:26"),
}


FAMCTX = {"grocery": r"grocery|4451", "french": r"french|cajun|lang", "construction": r"construction"}


def first_posts(fam, d):
    votes, ids = q.load_agents(fam)
    rp = pd.read_csv(q.OUT / f"route_posts_{fam}.csv")
    rp["time"] = pd.to_datetime(rp["time"], format="ISO8601", utc=True)
    rows = []
    for a, g in votes.groupby("agent"):
        first_report = g["report_time"].min()
        sigs = set(ids.loc[ids["agent"] == a, "signature"]) - {""}
        if fam == "grocery":
            sigs |= {a}
        revs = set(ids.loc[ids["agent"] == a, "rev_id"])
        lo = first_report - timedelta(hours=12)
        mine = d[d["rev_id"].isin(revs) | (d["sig"].isin(sigs) & (d["time"] >= lo) & (d["time"] <= first_report))]
        cand = [(r.time, r.rev_id, "claim edit / signature", r.added_text) for r in mine.itertuples()]
        cand += [(r.time, r.rev_id, f"route post ({r.agent_basis})", r.text)
                 for r in rp[rp["agent_key"] == a].drop_duplicates("rev_id").itertuples()]
        ctx = FAMCTX[fam]
        fam_c = [c for c in cand if c[2] != "claim edit / signature" or c[1] in revs
                 or re.search(ctx, c[3], re.I) or re.search(ctx, d.loc[d["rev_id"] == c[1], "page"].iloc[0], re.I)]
        other = sorted(c for c in cand if c not in fam_c)
        t, rev, basis, text = min(fam_c, key=lambda c: c[0])
        text = re.sub(r"\s+", " ", text)
        r1 = g[g["round"] == 1]["vote"]
        auto = "after_r1" if AFTER.search(text) else "before_r1"
        tag, note = HAND.get((fam, a), (auto, ""))
        rows.append({"agent": a, "r1_passed": q.agg_vote(r1) or ("?" if len(r1) else "-"),
                     "r2plus_passed": q.agg_vote(g[g["round"] > 1]["vote"]) or ("?" if (g["round"] > 1).any() else "-"),
                     "first_post": t, "first_post_basis": basis, "first_report": first_report,
                     "other_task_post_before": other[0][0] if other else "",
                     "other_task_page": d.loc[d["rev_id"] == other[0][1], "page"].iloc[0] if other else "",
                     "auto": auto, "first_post_vs_r1": tag, "note": note, "first_post_text": text[:400]})
    return pd.DataFrame(rows)


def main():
    d = pd.read_csv(q.ROOT / "added_text.csv").dropna(subset=["added_text"])
    d["time"] = pd.to_datetime(d["time"], format="ISO8601", utc=True)
    d["sig"] = d["added_text"].map(q.signature)
    for fam in q.FAMILIES:
        out = first_posts(fam, d)
        out.to_csv(q.OUT / f"r1_board_{fam}.csv", index=False)
        print(f"\n=== {fam}: {len(out)} agents")
        print(pd.crosstab(out["first_post_vs_r1"], out["r1_passed"], margins=True, margins_name="total")
              .rename_axis(index="first_post_vs_r1", columns="r1_passed").to_string())
        print(pd.crosstab(out["first_post_vs_r1"], out["r2plus_passed"], margins=True, margins_name="total")
              .rename_axis(index="first_post_vs_r1", columns="r2plus_passed").to_string())
        o = out[out["other_task_post_before"] != ""]
        print(f"signed post in another task within 12h before first report: {len(o)} agents; "
              f"R1 {o['r1_passed'].value_counts().to_dict()}  pages: {sorted(set(o['other_task_page']))}")


if __name__ == "__main__":
    main()
