r"""Disagreement screen: competing numeric values per family x round entity. No labeling.

Per family (page-name based, screen/families.py; test/sandbox/probe/scratch pages skipped) and per
round entity, every number posted right after the entity name (same line, within ~45 chars, before
another entity of that family is named) is collected from added text. Dropped: URLs, times
(hh:mm[:ss]), timers (12m18, 46s), years 1990-2030 (unless the entity is itself a year), round
labels, integers below 100 (counter values, '+1s', ranks), and numbers outside x0.5..x2 of the entity's most-posted value (drops counts sitting next
to shares, e.g. French 92,675 next to 7.58%).
Value groups: the same number at different precision is one group (9.7 = 9.70; 9.69 separate;
90,725 = 90725). `k` = values one answer legitimately contains (e.g. Construction 2016 and 2018).
competing = groups with >= 3 posts minus k (sort key). agents = distinct signer (sign-off, else
username) posting any value for the entity.

Usage:  .venv\Scripts\python screen\disagreement.py
Output: screen/disagreement.csv, screen/values_long.csv
"""
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from families import family  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# family -> (k, merge-into family or None, [(entity, regex), ...] in round order)
CFG = {
    "grocery": (1, [("Georgia", r"Georgia|GA"), ("Arkansas", r"Arkansas|AR"), ("Nevada", r"Nevada|NV"), ("Kentucky", r"Kentucky|KY"), ("Montana", r"Montana|MT")]),
    "construction": (2, [("New York", r"New York|NY"), ("California", r"California|CA"), ("Texas", r"Texas|TX"), ("Florida", r"Florida|FL"), ("Nebraska", r"Nebraska|NE"),
                         ("Arizona", r"Arizona|AZ"), ("Utah", r"Utah|UT"), ("Colorado", r"Colorado|CO"), ("New Mexico", r"New Mexico|NM")]),
    "french": (1, [("Texas", r"Texas|TX"), ("Louisiana", r"Louisiana|LA"), ("New York", r"New York|NY"), ("New Hampshire", r"New Hampshire|NH"), ("California", r"California|CA"), ("New Mexico", r"New Mexico|NM")]),
    "oecd-equity": (1, [("Czech Republic", r"Czech(?: Republic)?|CZE"), ("Hungary", r"Hungary|HUN"), ("Poland", r"Poland|POL"), ("Slovak Republic", r"Slovak(?: Republic)?|SVK"), ("Slovenia", r"Slovenia|SVN")]),
    "oecd-rrp-co2": (1, [("Colombia", r"Colombia|COL"), ("Mexico", r"Mexico|MEX"), ("Chile", r"Chile|CHL"), ("Poland", r"Poland|POL"), ("Italy", r"Italy|ITA")]),
    "cashier-bachelors": (1, [("Education", r"Education"), ("Business", r"Business"), ("Social Sciences", r"Social Sciences"), ("Visual and Performing Arts", r"Visual(?: and| &) Performing Arts|Visual"), ("Psychology", r"Psychology")]),
    "cashier-masters": (1, [("Education", r"Education"), ("Business", r"Business"), ("Social Sciences", r"Social Sciences")]),
    "cvd": (4, [("Armenia", r"Armenia"), ("Kazakhstan", r"Kazakhstan"), ("Turkmenistan", r"Turkmenistan"), ("Hungary", r"Hungary"), ("Poland", r"Poland")]),
    "ihme-family-planning": (1, [("Croatia", r"Croatia"), ("Albania", r"Albania"), ("Cyprus", r"Cyprus"), ("Bahrain", r"Bahrain"), ("South Korea", r"South Korea|Korea")]),
    "sector": (6, [("Massachusetts", r"Massachusetts|MA"), ("Connecticut", r"Connecticut|CT"), ("Michigan", r"Michigan|MI"), ("West Virginia", r"West Virginia|WV")]),
    "clothing": (3, [("California", r"California|CA"), ("New York", r"New York|NY"), ("Florida", r"Florida|FL")]),
    "police": (2, [(a, re.escape(a)) for a in ["25-29", "30-34", "35-39", "40-44", "45-49", "50-54"]]),
    "poverty": (1, [("Flathead", r"Flathead"), ("Merced", r"Merced"), ("San Juan", r"San Juan"), ("Saginaw", r"Saginaw"), ("Pitt", r"Pitt")]),
    "transport": (1, [("California", r"California|CA"), ("Texas", r"Texas|TX")]),
    "nyc-veterans": (1, [("World War II", r"World War II|WWII"), ("Korea", r"Korea"), ("Vietnam", r"Vietnam"), ("Gulf War (1990s)", r"Gulf War \(1990s\)|Gulf90s"), ("Gulf War (2001-)", r"Gulf War \(2001-?\)|Gulf2001")]),
    "ivy-tuition": (1, [("Arkansas Northeastern College", r"Arkansas Northeastern(?: College)?"), ("Pitt Community College", r"Pitt(?: Community College| CC)?"), ("Cleveland Community College", r"Cleveland(?: Community College| CC)?")]),
    "lf": (1, [("Ethiopia", r"Ethiopia"), ("Nigeria", r"Nigeria"), ("Kenya", r"Kenya"), ("Sudan", r"Sudan")]),
    "healthdata-other": (1, [("Indonesia", r"Indonesia"), ("Samoa", r"Samoa"), ("Algeria", r"Algeria")]),
    "construction-wage": (1, [(y, y) for y in ["2014", "2015", "2016", "2017", "2018"]]),
    "maids": (1, [("Female 2015", r"Female 2015"), ("Male 2016", r"Male 2016")]),
    "occupation-salary": (1, [("School psychologists", r"School psychologists")]),
}
MERGE = {"state-sequence": "sector", "maids-wage": "maids", "school-psych": "occupation-salary", "poverty-county": "poverty"}
NUM = re.compile(r"(?<![\w.:/\-])\$?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(?![\w:%]*[:/])(?!\s?(?:m\d|s\b|min|sec|h\d))")
SIG = re.compile(r"--\s*\[*([A-Za-z0-9_\-]+)")


def group_key(v):
    x = float(v.replace(",", "").replace("$", ""))
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return s, x


def main():
    d = pd.read_csv(ROOT / "added_text.csv").dropna(subset=["added_text"])
    d["fam"] = d["page"].map(family).replace(MERGE)
    d = d[d["fam"].isin(CFG)]
    rows = []
    for r in d.itertuples():
        k, ents = CFG[r.fam]
        any_ent = "|".join(f"(?:{p})" for _, p in ents)
        parts = re.findall(r"(.*?--\s*\[*([A-Za-z0-9_\-]+))", r.added_text, re.S) or [(r.added_text, r.agent)]
        for txt, who in parts:
            txt = re.sub(r"https?://\S+|\[\S+ [^\]]*\]", " ", txt)  # drop URLs and wiki links
            for line in txt.split("\n"):
                line = re.sub(r"\b[MF](\d{4,})", r"\1", line)  # Police: 'M50531 F47206'
                for ent, pat in ents:
                    for m in re.finditer(rf"(?<![A-Za-z]){pat}(?![A-Za-z])", line):
                        win = line[m.end():m.end() + 45 + 20 * (k - 1)]  # multi-value answers need room
                        nxt = re.search(rf"(?<![A-Za-z])(?:{any_ent})(?![A-Za-z])", win)
                        if nxt:
                            win = win[:nxt.start()]
                        nums = []
                        for n in NUM.finditer(win):
                            v = n.group(1)
                            plain = v.replace(",", "")
                            if not re.fullmatch(r"\d{4}", ent) and re.fullmatch(r"(199\d|20[0-3]\d)", plain):
                                continue
                            if re.fullmatch(r"\d{4}", ent) and plain == ent:
                                continue
                            if "." not in plain and int(plain) < 100:  # counters, '+1s', ranks: not answers
                                continue
                            nums.append(v)
                            if len(nums) >= k:
                                break
                        for v in nums:
                            g, x = group_key(v)
                            rows.append({"family": r.fam, "entity": ent, "group": g, "x": x, "who": who,
                                         "time": r.time, "page": r.page, "line": line.strip()[:300]})
    long = pd.DataFrame(rows).drop_duplicates(["family", "entity", "group", "who", "line"])
    out = []
    for (fam, ent), g in long.groupby(["family", "entity"]):
        k = CFG[fam][0]
        mode_x = g.groupby("group")["x"].first()[g["group"].value_counts().index[0]]
        g = g[(g["x"] >= mode_x * 0.5) & (g["x"] <= mode_x * 2)]  # same magnitude as the modal value
        vc = g["group"].value_counts()
        top = "; ".join(f"{v} ({n})" for v, n in vc.head(3).items())
        out.append({"family": fam, "entity": ent, "k": k, "value_groups": len(vc), "groups_3plus": int((vc >= 3).sum()),
                    "competing": int((vc >= 3).sum()) - k, "top3": top, "posts": int(vc.sum()), "agents": g["who"].nunique()})
        long.loc[g.index, "kept"] = True
    out = pd.DataFrame(out)
    fam_agents = long[long["kept"] == True].groupby("family")["who"].nunique()  # noqa: E712
    out["family_agents"] = out["family"].map(fam_agents)
    out = out[out["family_agents"] >= 10].sort_values(["competing", "value_groups"], ascending=False)
    out.to_csv(ROOT / "screen" / "disagreement.csv", index=False)
    long.to_csv(ROOT / "screen" / "values_long.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.to_string(index=False, max_colwidth=70))
    skipped = sorted(set(CFG) - set(out["family"]))
    print("\nSkipped (<10 agents posting values):", skipped)


if __name__ == "__main__":
    main()
