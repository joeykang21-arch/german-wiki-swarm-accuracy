r"""Q7 step 2: did agents get their working data route from the board?

Per family (grocery, french, construction):
  1. Every DataUSA query URL posted anywhere on the wiki (plain, %-encoded, or wrapped in a proxy
     such as markdown.new / r.jina.ai / allorigins) is normalized to a route key:
       base   = inner host + endpoint (extension dropped: data.jsonrecords = data.csv = data)
       cube, drilldowns, measures, filters (include=Level:v and Level=v cuts merged, sorted)
     Ignored: locale, limit, parents, sparse, nonempty, sort, order, format, properties, cache-busters.
     A route belongs to a family by its filters/cube (grocery Industry Group 4451, construction
     Industry Sector 23, french language cube). Schema/members URLs are kept as kind=schema/members.
  2. Agents with an own-round report come from the family's labeled CSVs (one vote per agent).
  3. Each route post is attributed to an agent key by signature (else by username if that username
     maps to one agent only; weak). route_source for an agent's first data-route post:
       own          = no identical route on the board before it
       credited     = post credits another source (via/thanks/from [[Page]]/@X/per board ...)
       board_likely = identical to an earlier board route, no credit
       unknown      = no attributable data-route post
     HAND below overrides the automatic tag after hand review.

Usage:  .venv\Scripts\python q7_routes.py
Output: q7/routes_<family>.csv, q7/agent_route_source_<family>.csv, q7/route_posts_<family>.csv,
        printed tables.
"""
import re
from pathlib import Path
from urllib.parse import parse_qsl, unquote

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "q7"
URL = re.compile(r"https?://[^\s\]\)\"'`<>|]+")
INNER = re.compile(r"https?://((?:[a-z0-9\-]+\.)*datausa\.io)(/[^?\s#]*)(?:\?([^\s#]*))?", re.I)
SIG = re.compile(r"--\s*\[*([A-Za-z0-9_\-]+)")
IGNORE = {"locale", "limit", "parents", "sparse", "nonempty", "sort", "order", "format", "properties",
          "debug", "nocache", "cache", "cb", "ts", "t", "_", "x", "r", "nc", "v", "bust", "rand", "uniq",
          "jq", "url", "q", "foo"}
CREDIT = re.compile(r"\bvia\b|thank|\bfrom \[\[|\bper (the )?board\b|@[A-Z][A-Za-z0-9]+|\bper [A-Z][a-z]+\d"
                    r"|posted by|\bfrom [A-Z][A-Za-z]*(Agent|Helper|Research|Watcher|Scout)|\bcredit"
                    r"|\b(as|query) (posted|shared) (by|on|above)|\bfrom (the )?(wiki|board|page)\b"
                    r"|\bborrow|\bcopied|\breus", re.I)

FAMILIES = {
    "grocery": {"rounds": ["Georgia", "Arkansas", "Nevada", "Kentucky", "Montana"],
                "match": lambda f, c: any(re.fullmatch(r"industry group:(4451|grocery.*)", x) for x in f),
                "cube": lambda c: c == "pums_5", "context": r"grocery|4451"},
    "french": {"rounds": ["Texas", "Louisiana", "New York", "New Hampshire", "California"],
               "match": lambda f, c: "language_spoken" in c,
               "cube": lambda c: "language_spoken" in c, "context": r"french|cajun|DataUSALanguage"},
    "construction": {"rounds": ["New York", "California", "Texas"],
                     "match": lambda f, c: any(re.fullmatch(r"industry sector:(23|construction)", x) for x in f),
                     "cube": lambda c: c == "pums_5", "context": r"construction"},
}

# Hand review (family, agent) -> (route_source, note). Every agent with an auto tag other than
# unknown was read, plus every agent whose own posts describe a route in words. Agents not listed
# keep the auto tag (all of those are 'unknown': no attributable route post, no route statement).
HAND = {
    # grocery
    ("grocery", "AgentProbeAssistantX2027"): ("own", "first tesseract-proxy all-state query (09:02); API all-state query already on wiki 07:31/07:49 (other host); username weak"),
    ("grocery", "GrocerySequenceAgentApr27"): ("own", "strictly new (api host, no Year); near-identical api-la 07:31 and api+Year 07:49 already on wiki"),
    ("grocery", "GroceryAgentMar05X"): ("board_likely", "test link 19:30 identical to 26 earlier posts; username weak"),
    ("grocery", "OaiResearcher"): ("board_likely", "identical to Apr27 board endpoint; username weak"),
    ("grocery", "ResearchBotFeb2028"): ("own", "Georgia-only variant first seen here; near-identical GA query 18:36; username weak"),
    # french
    ("french", "Apr10"): ("own", "first French data route on wiki (19:10, 'API bridge test'); username weak. R1 text: 'I guessed wrong; thanks for exact TX 7.58%' = value from board"),
    ("french", "Feb17"): ("own", "19:40 signed post names the cube/measure/table first; 19:47 URLs under same username (Jun01 label overlap starts 20:29)"),
    ("french", "Jun01"): ("own", "signed; 'We have working proxy' 20:29, first tesseract-proxy route 20:30"),
    ("french", "Dec29"): ("own", "strictly new only by Language=1 filter; near-identical routes on wiki since 19:47; username weak; post 1h before first report"),
    ("french", "Sep03"): ("own", "first all-state Language=2 query (21:10 'PARENT TESTS'); TX-only version 20:49; username weak"),
    ("french", "Sep18"): ("board_likely", "URL post 00:32 is 2h after its reports and copies AgentSolverX 21:58; text 22:18 says LA row-sum answered 'before seeing this page' -> own data route likely, source not shown"),
    ("french", "Mar17"): ("unknown", "MarX: no URL; describes own source-code + proxy checks; R1-R3 answered row-sum 'before finding this page' (21:23)"),
    ("french", "Sep23"): ("unknown", "no URL; row-sum came from own canon-vizbuilder reading (20:56), switched to national for R4"),
    ("french", "Jun21"): ("unknown", "no URL; 20:50 asks Jun01 on board for 'working proxy URL/method' after its R1"),
    ("french", "Dec27"): ("unknown", "no URL; 'Our R1 was mistakenly national-denom 7.58; later corrected method'"),
    # construction
    ("construction", "Apr02"): ("unknown", "only attributable URL is an Arizona Industry-Group lookup 7h after its reports (username weak); text: R1 'Correct values found after deadline'"),
    ("construction", "Dec17"): ("board_likely", "07:13 query = all-state Sector-23 query + Year:2016; base query on wiki since 06-16 08:56; 4h after its reports; username weak"),
    ("construction", "Feb20-B8DC"): ("board_likely", "NY query 2.5 min after SectorAgentMar20OAI's identical one (could be same agent, rotated name); username weak"),
    ("construction", "Jul12"): ("board_likely", "17:36 query identical to 31 earlier; later own 'TesseractProxyBreakthroughJul12' page 19:30; text: R1 wrong 'before sequence discovery'"),
    ("construction", "Mar08"): ("board_likely", "00:25 query identical to 06-16 08:56 all-sector link dumps (not construction pages); first construction tesseract-proxy route 00:34 is Mar08's own; username weak"),
    ("construction", "May07"): ("board_likely", "07:35 query after its reports, identical to 07:13; username weak"),
    ("construction", "Nov08"): ("board_likely", "auto 'credited' matched 'via' in signal text; API line is the board header Nov08 re-posted while compacting the page"),
    ("construction", "Apr13"): ("credited", "no URL; 'answered wrong before discovering board' (route/value source = board)"),
}


def norm_level(s):
    return re.sub(r"\s+", " ", s.replace("+", " ")).strip().lower()


def route_key(host, path, query):
    host = host.lower()
    path = re.sub(r"/+", "/", path)
    q = dict()
    filters = set()
    for k, v in parse_qsl(query or "", keep_blank_values=True):
        k2 = norm_level(k).replace("[]", "")
        if k2 in IGNORE or not v:
            continue
        if k2 in ("cube", "drilldowns", "drilldown", "measures", "measure"):
            key = {"drilldown": "drilldowns", "measure": "measures"}.get(k2, k2)
            q.setdefault(key, set()).update(norm_level(x) for x in re.split(r",", v) if x)
        elif k2 in ("include", "cuts", "cut", "exclude", "filters", "time"):
            for part in v.split(";"):
                m = re.match(r"\s*\[?([^\]:.=]+)\]?(?:\.\[[^\]]+\])*\s*[:=.]\s*&?\[?([^\]]+)\]?", part)
                if m:
                    filters.add(("not " if k2 == "exclude" else "") + f"{norm_level(m.group(1))}:{norm_level(m.group(2))}")
                elif part.strip():
                    filters.add(f"{k2}:{norm_level(part)}")
        else:
            filters.add(f"{k2}:{norm_level(v)}")
    m = re.search(r"/cubes/([^/]+)", path)
    cube = (sorted(q.get("cube", [])) or [m.group(1).lower() if m else ""])[0]
    if re.search(r"/members|/search", path):
        kind = "members"
    elif re.search(r"/aggregate|/data|/calcs", path):
        kind = "data"
    elif "/cubes" in path:
        kind = "schema"
    else:
        kind = "other"
    base = host + re.sub(r"\.(jsonrecords|jsonarrays|json|csvrecords|csv)$", "", path.rstrip("/"))
    if "/cubes/" in base:  # old tesseract-proxy: cube lives in the path
        base = re.sub(r"/cubes/[^/]+", "/cubes/{cube}", base)
    key = " | ".join([base, f"cube={cube}", "drill=" + ",".join(sorted(q.get("drilldowns", []))),
                      "meas=" + ",".join(sorted(q.get("measures", []))), "filt=" + ";".join(sorted(filters))])
    return key, kind, cube, filters


def routes_in(text):
    """Yield (route_key, kind, cube, filters, wrapper, raw_url) for each DataUSA URL in text."""
    for u in URL.findall(text):
        x = u
        for _ in range(3):  # peel wrapper encoding; keep spaces encoded so the query is not cut at a space
            x = unquote(x).replace(" ", "%20")
        wrapper = re.match(r"https?://([^/]+)", u).group(1).lower()
        for m in INNER.finditer(x):
            host, path, query = m.group(1), m.group(2), m.group(3)
            # a wrapper's own trailing params (e.g. &jq=...) are dropped by IGNORE
            k, kind, cube, filt = route_key(host, path, query)
            yield k, kind, cube, filt, ("direct" if "datausa.io" in wrapper else wrapper), u


def signature(text):
    m = SIG.findall(text)
    return m[-1] if m else ""


def load_agents(fam):
    """One row per agent with an own-round report: r1 / r2plus votes, first report, ids."""
    rounds = FAMILIES[fam]["rounds"]
    recs, ids = [], []
    for i, st in enumerate(rounds):
        if fam == "grocery":
            df = pd.read_csv(ROOT / f"{st.lower()}_labeled.csv", dtype=str, encoding="utf-8-sig").fillna("")
            df = df.rename(columns={"is_georgia_claim": "is_state_claim"})
            df["label"] = df["agent"]
            df["signature"] = df["text"].map(signature)
            df["agent"] = df["signature"].where(df["signature"] != "", df["label"])
            claims = df[df["is_state_claim"].str.upper().str.startswith("Y")]
            truth = {"Georgia": 90725, "Arkansas": 20794, "Nevada": 20369, "Kentucky": 34770, "Montana": 8553}[st]
            num = lambda s: int(float(re.sub(r"[^\d.]", "", s))) if re.sub(r"[^\d.]", "", s) else None
            for a, g in claims.groupby("agent"):
                g = g.sort_values("time")
                ow = g[g["own_answer_wrong"].str.upper().str[:1].isin(["Y", "N"])]
                if len(ow):
                    v = "N" if ow["own_answer_wrong"].iloc[0].upper().startswith("Y") else "Y"
                    t, basis = ow["time"].iloc[0], "self-report"
                else:
                    ob = g[(g["claim_type"].str.lower().str.strip() == "observed") & (g["value_claimed"] != "")]
                    if not len(ob):
                        continue
                    v = "Y" if num(ob["value_claimed"].iloc[0]) == truth else "N"
                    t, basis = ob["time"].iloc[0], "observed value"
                recs.append({"agent": a, "round": i + 1, "state": st, "vote": v, "vote_national": "",
                             "report_time": t, "basis": basis})
            ids += [(r.agent, r.signature, r.label, r.rev_id) for r in claims.itertuples()]
            continue
        sub = "french" if fam == "french" else "construction/construction_R1-R3_labels"
        df = pd.read_csv(ROOT / sub / f"{fam}_{st.replace(' ', '_')}_labeled.csv", dtype=str).fillna("")
        claims = df[(df["claim_type"] != "none") & (df["agent"] != "")]
        ids += [(r.agent, r.signature, r.label, r.rev_id) for r in claims.itertuples()]
        for a, g in claims.groupby("agent"):
            g = g.sort_values("time")
            if fam == "french":
                ans = g[g["answer_reading"] != ""]
                if len(ans):
                    rd = ans["answer_reading"].iloc[0]
                    recs.append({"agent": a, "round": i + 1, "state": st,
                                 "vote": "Y" if rd == "rowsum" else "?" if rd == "unknown" else "N",
                                 "vote_national": "Y" if rd == "national" else "?" if rd == "unknown" else "N",
                                 "report_time": ans["time"].iloc[0], "basis": f"answer quoted ({rd})"})
                elif (g["answered"] == "?").any():
                    recs.append({"agent": a, "round": i + 1, "state": st, "vote": "?", "vote_national": "?",
                                 "report_time": g.loc[g["answered"] == "?", "time"].iloc[0], "basis": "no value"})
            else:
                p = set(g["passed_own_test"]) - {""}
                v = "conflict" if {"Y", "N"} <= p else "Y" if "Y" in p else "N" if "N" in p else "?" if "?" in p else None
                if v is None:
                    continue
                obs = g[g["passed_own_test"] != ""]
                recs.append({"agent": a, "round": i + 1, "state": st, "vote": v, "vote_national": "",
                             "report_time": obs["time"].iloc[0],
                             "basis": "/".join(sorted(set(obs["pass_basis"]) - {""}))})
    votes = pd.DataFrame(recs)
    votes["report_time"] = pd.to_datetime(votes["report_time"], format="ISO8601", utc=True)
    ids = pd.DataFrame(ids, columns=["agent", "signature", "label", "rev_id"])
    return votes, ids


def agg_vote(vs):
    vs = [v for v in vs if v in ("Y", "N", "conflict")]
    if not vs:
        return ""
    return "N" if any(v in ("N", "conflict") for v in vs) else "Y"


def attribute(ids):
    """same edit as a labeled claim line -> that agent; else signature; else username (weak)."""
    sig = ids[ids["signature"] != ""].groupby("signature")["agent"].agg(lambda s: sorted(set(s)))
    lab = ids.groupby("label")["agent"].agg(lambda s: sorted(set(s)))
    rev = ids.groupby("rev_id")["agent"].agg(lambda s: sorted(set(s)))
    def who(label, text, rev_id=None):
        if rev_id in rev.index:
            k = rev[rev_id]
            return (k[0], "same edit as claim line") if len(k) == 1 else ("|".join(k), "ambiguous same edit")
        s = signature(text)
        if s and s in sig.index:
            k = sig[s]
            return (k[0], "signature") if len(k) == 1 else ("|".join(k), "ambiguous signature")
        if s:
            return ("", f"unmatched signature {s}")
        if label in lab.index:
            k = lab[label]
            return (k[0], "username (weak)") if len(k) == 1 else ("|".join(k), "ambiguous username")
        return ("", "unmatched")
    return who


WRONG = re.compile(r"(answer(ed)?|submitted|guess(ed)?|answer was)[^.;\n]{0,25}\b(wrong|incorrect|mistaken(ly)?)\b[^.;\n]{0,15}\b(before|until)\b"
                   r"|\b(initially|originally|mistakenly) (answered|submitted|gave)\b|\bwas mistakenly\b"
                   r"|before (seeing|discovering|finding|reading) (this|the)\b|\bguessed wrong\b"
                   r"|found after (the )?deadline|\bwrong guess\b|answered wrong \(correct|\bbut now believe\b", re.I)
DISCOVERED = [("route", r"proxy|\bAPI\b|endpoint|workbook|query"), ("board", r"board|this page|sequence discovery"),
              ("value", r"correct values|exact|thanks for|method|denominator|now believe|correct \d")]


# Hand review of 'discovered' (label, time prefix) -> tag. Others keep the keyword tag (all checked).
DISC_HAND = {
    ("GroceryAgentDec20X", "2026-06-16 20:11"): "not stated",   # states correct GA value, not what was found
    ("RevisionScoutOAI", "2026-06-16 20:18"): "not stated",
    ("OpenAIResearchFeb17", "2026-06-17 01:19"): "value",       # "Correct values found after deadline"
    ("OpenAIResearchSep20", "2026-06-17 16:09"): "not stated",  # "wrong guess"
    ("OpenAIResearchSep20", "2026-06-17 16:13"): "not stated",
    ("OpenAIResearchNov05C", "2026-06-17 17:25"): "not stated", # "before discovering exact"
}


def wrong_before(d, cfg, who):
    """Every line saying the agent answered wrong before discovering something; tag what was discovered."""
    m = d[d["added_text"].str.contains(cfg["context"], case=False) | d["page"].str.contains(cfg["context"], case=False)]
    rows = []
    for r in m.itertuples():
        for line in r.added_text.split("\n"):
            for mm in WRONG.finditer(line):
                ctx = line[max(0, mm.start() - 60):mm.end() + 60]
                tail = line[mm.start():mm.end() + 60]
                disc = next((k for k, p in DISCOVERED if re.search(p, tail, re.I)), "not stated")
                disc = DISC_HAND.get((r.agent, str(r.time)[:16]), disc)
                key, basis = who(r.agent, line, r.rev_id)
                rows.append({"time": r.time, "page": r.page, "rev_id": r.rev_id, "label": r.agent,
                             "signature": signature(line), "agent_key": key, "agent_basis": basis,
                             "matched": mm.group(0), "discovered": disc, "context": re.sub(r"\s+", " ", ctx), "line": line})
    return pd.DataFrame(rows, columns=["time", "page", "rev_id", "label", "signature", "agent_key", "agent_basis",
                                       "matched", "discovered", "context", "line"])


def main():
    OUT.mkdir(exist_ok=True)
    d = pd.read_csv(ROOT / "added_text.csv").dropna(subset=["added_text"])
    d["time"] = pd.to_datetime(d["time"], format="ISO8601", utc=True)
    d = d.sort_values("time")
    hits = []
    for r in d.itertuples():
        if "datausa" not in r.added_text.lower() and "%" not in r.added_text:
            continue
        for k, kind, cube, filt, wrapper, raw in routes_in(r.added_text):
            hits.append({"time": r.time, "rev_id": r.rev_id, "page": r.page, "label": r.agent,
                         "signature": signature(r.added_text), "route": k, "kind": kind, "cube": cube,
                         "filters": filt, "wrapper": wrapper, "url": raw, "text": r.added_text})
    hits = pd.DataFrame(hits)
    print(f"DataUSA URLs found: {len(hits)} in {hits['rev_id'].nunique()} edits")

    for fam, cfg in FAMILIES.items():
        ctx = hits["text"].str.contains(cfg["context"], case=False) | hits["page"].str.contains(cfg["context"], case=False)
        own = hits.apply(lambda h: cfg["match"](h["filters"], h["cube"]), axis=1)
        # context+cube: right cube, posted in family context, and no filter naming another industry
        other_ind = hits["filters"].map(lambda f: any(x.startswith("industry") for x in f))
        generic = ~own & ctx & hits["cube"].map(cfg["cube"]) & ~other_ind
        h = hits[own | generic].copy()
        h["family_basis"] = (own[own | generic]).map({True: "filter", False: "context+cube"})
        votes, ids = load_agents(fam)
        who = attribute(ids)
        h[["agent_key", "agent_basis"]] = h.apply(lambda x: pd.Series(who(x["label"], x["text"], x["rev_id"])), axis=1)
        h["credit"] = h["text"].map(lambda t: "; ".join(sorted({m.group(0) for m in CREDIT.finditer(t)})))
        # loose key: same cube + drilldowns + family filters, ignoring host/endpoint and Year/State filters
        h["loose"] = h.apply(lambda x: (x["cube"], x["route"].split(" | ")[2],
                                        tuple(sorted(f for f in x["filters"] if f.startswith(("industry", "language"))))), axis=1)
        wrong_before(d, cfg, who).to_csv(OUT / f"wrong_before_discovery_{fam}.csv", index=False)
        h.drop(columns=["filters"]).assign(text=h["text"].str.replace("\n", " ").str[:600]) \
            .to_csv(OUT / f"route_posts_{fam}.csv", index=False)

        # ---- routes table
        rows = []
        for k, g in h.groupby("route"):
            g = g.sort_values("time"); f = g.iloc[0]
            rows.append({"route": k, "kind": f["kind"], "family_basis": f["family_basis"],
                         "first_time": f["time"], "first_page": f["page"], "first_label": f["label"],
                         "first_signature": f["signature"], "first_agent_key": f["agent_key"],
                         "posts": g["rev_id"].nunique(), "agent_keys": g.loc[g["agent_key"] != "", "agent_key"].nunique(),
                         "wrappers": ",".join(sorted(set(g["wrapper"]))), "example_url": f["url"]})
        routes = pd.DataFrame(rows).sort_values("first_time")
        routes.to_csv(OUT / f"routes_{fam}.csv", index=False)
        first_seen = routes.set_index("route")["first_time"]

        # ---- per agent
        ag = []
        for a, g in votes.groupby("agent"):
            r1 = g[g["round"] == 1]["vote"].tolist()
            rest = g[g["round"] > 1]
            mine = h[(h["agent_key"] == a) & (h["kind"] == "data")].sort_values("time")
            rec = {"agent": a, "r1_passed": agg_vote(r1) or ("?" if r1 else ""),
                   "r2plus_passed": agg_vote(rest["vote"]) or ("?" if len(rest) else ""),
                   "rounds_reported": ",".join(f"R{x}" for x in sorted(g["round"])),
                   "first_report": g["report_time"].min()}
            if fam == "french":
                rec["r1_passed_national"] = agg_vote(g[g["round"] == 1]["vote_national"]) or ("?" if r1 else "")
                rec["r2plus_passed_national"] = agg_vote(rest["vote_national"]) or ("?" if len(rest) else "")
            if len(mine):
                p = mine.iloc[0]
                others = h[(h["route"] == p["route"]) & (h["agent_key"] != a) & (h["time"] < p["time"])]
                prior = others["time"].min() if len(others) else None
                near = h[(h["loose"] == p["loose"]) & (h["agent_key"] != a) & (h["time"] < p["time"])]
                auto = ("credited" if p["credit"] else "board_likely") if prior is not None else "own"
                rec.update({"first_route_time": p["time"], "first_route_page": p["page"], "route": p["route"],
                            "wrapper": p["wrapper"], "attributed_by": p["agent_basis"],
                            "route_before_first_report": "Y" if p["time"] < rec["first_report"] else "N",
                            "route_first_on_board": first_seen[p["route"]], "earlier_identical_posts": len(others),
                            "earliest_other_poster": (others.iloc[0]["signature"] or others.iloc[0]["label"]) if len(others) else "",
                            "near_identical_earlier_posts": near["rev_id"].nunique(),
                            "earliest_near_identical": near["time"].min() if len(near) else "",
                            "credit_words": p["credit"], "auto_tag": auto, "post_text": p["text"].replace("\n", " ")[:700]})
            else:
                rec.update({"auto_tag": "unknown"})
            tag, note = HAND.get((fam, a), (rec["auto_tag"], ""))
            rec["route_source"], rec["review_note"] = tag, note
            ag.append(rec)
        ag = pd.DataFrame(ag)
        ag.to_csv(OUT / f"agent_route_source_{fam}.csv", index=False)

        print(f"\n=== {fam}: {len(routes)} distinct routes ({(routes['kind'] == 'data').sum()} data), "
              f"{len(h)} route URLs in {h['rev_id'].nunique()} edits; agents with own-round report: {len(ag)}")
        print(ag["route_source"].value_counts().to_string())
        for col in ["r1_passed", "r2plus_passed"] + (["r1_passed_national", "r2plus_passed_national"] if fam == "french" else []):
            print(pd.crosstab(ag["route_source"], ag[col].replace("", "-"), margins=True, margins_name="total")
                  .rename_axis(index="route_source", columns=col).to_string())


if __name__ == "__main__":
    main()
