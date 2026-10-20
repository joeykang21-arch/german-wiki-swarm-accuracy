r"""Counts behind oecd.html (OECD Education Equity, pre-primary private expenditure share 2018).

Two readings of "value (to two decimal places)":
  padded = workbook cell display (format 0.0) padded with a zero: 9.70 / 9.90 / 16.40 / 14.60
  raw    = stored value rounded to 2 dp (also the live Power BI tooltip): 9.69 / 9.91 / 16.38 / 14.59
Board lines: distinct added lines that give a value for the country (one row per distinct line).
Answers: one per signer per round: the first "answered/submitted <value>" on the board, assigned
to the country named between the verb and the value, else the last country or round marker
(R1..R4) before the verb. Automatic, not hand-labeled; spot-checked.
Signers are split per signed chunk so relayed text counts for its signer.

Usage (from the swarm-accuracy folder):  .venv\Scripts\python oecd\oecd_counts.py
Output: oecd/oecd_lines.csv, oecd/oecd_answers.csv, printed tables (hourly counts used in oecd.html).
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
C = {  # iso: round, country regex, raw, padded
    "CZE": (1, r"Czech(?: Republic)?|CZE", "9.69", "9.70"),
    "HUN": (2, r"Hungary|HUN", "9.91", "9.90"),
    "POL": (3, r"Poland|POL", "16.38", "16.40"),
    "SVK": (4, r"Slovak(?: Republic)?|SVK", "14.59", "14.60"),
}
NUM = r"(\d{1,2}\.\d{1,2})"
ANS = re.compile(r"\b(answered|submitted|answer was)\b", re.I)
TOOLTIP = "2026-06-20 04:56:50"  # first post of live Power BI tooltip values (Mar30TooltipVerifier)


def chunks(text, label):
    parts = re.findall(r"(.*?--\s*\[*([A-Za-z0-9_\-]+))", text, re.S)
    out = list(parts)
    rest = text[sum(len(p[0]) for p in parts):]
    if rest.strip():
        out.append((rest, label))
    return out


def reading(iso, v):
    _, _, raw, pad = C[iso]
    return "raw" if v == raw else "padded" if v in (pad, pad[:-1]) else "other"


def answers_in(line):
    for m in ANS.finditer(line):
        pre = line[max(0, m.start() - 200):m.start()]
        post = line[m.end():m.end() + 60]
        mm = re.match(r"[^\d\n]{0,40}?" + NUM + r"(?!\d)", post)
        if not mm:
            continue
        between = post[:mm.start(1)]
        v = mm.group(1)
        # the four countries' raw/padded values never overlap, so a known value decides the country
        iso = next((k for k, c in C.items() if v in (c[2], c[3], c[3][:-1])), None)
        iso = iso or next((k for k, c in C.items() if re.search(c[1], between)), None)
        if not iso:
            best = -1
            for k, c in C.items():
                for x in re.finditer(rf"{c[1]}|\bR{c[0]}\b", pre):
                    if x.start() > best:
                        best, iso = x.start(), k
        if iso and abs(float(mm.group(1)) - float(C[iso][2])) <= 1.5:
            yield iso, mm.group(1)


def main():
    d = pd.read_csv(ROOT / "added_text.csv").dropna(subset=["added_text"]).sort_values("time")
    d = d[(d["time"] >= "2026-06-17") & (d["time"] < "2026-06-21")]
    d = d[d["page"].str.contains("OECD|Equity", case=False) | d["added_text"].str.contains("OECD|pre-primary", case=False)]
    lines, answers = [], []
    for r in d.itertuples():
        for txt, who in chunks(r.added_text, r.agent):
            for line in txt.split("\n"):
                for iso, (rnd, nm, raw, pad) in C.items():
                    vals = [m.group(1) for m in re.finditer(rf"(?:{nm})[^\d\n]{{0,40}}?{NUM}(?!\d)", line)]
                    vals = [v for v in vals if abs(float(v) - float(raw)) <= 1.5]
                    if vals:
                        kinds = {reading(iso, v) for v in vals}
                        kind = "both" if {"raw", "padded"} <= kinds else next(k for k in ("raw", "padded", "other") if k in kinds)
                        lines.append({"time": r.time, "who": who, "iso": iso, "round": rnd, "kind": kind, "line": line.strip()})
                for iso, v in answers_in(line):
                    answers.append({"time": r.time, "who": who, "iso": iso, "round": C[iso][0], "value": v,
                                    "reading": reading(iso, v), "line": line.strip()[:400]})
    L = pd.DataFrame(lines).drop_duplicates(["iso", "line"])
    A = pd.DataFrame(answers).sort_values("time").drop_duplicates(["who", "iso"])
    L.to_csv(ROOT / "oecd" / "oecd_lines.csv", index=False)
    A.to_csv(ROOT / "oecd" / "oecd_answers.csv", index=False)
    print("Board lines per round (distinct):")
    print(pd.crosstab(L["iso"], L["kind"], margins=True).to_string())
    print("\nAnswers per round (one per signer):")
    print(pd.crosstab(A["iso"], A["reading"], margins=True).to_string())
    print("\nHourly distinct lines by kind:")
    print(pd.crosstab(L["time"].str[5:13], L["kind"]).to_string())
    print(f"\nAnswers reported before / after first live-tooltip post ({TOOLTIP}):")
    print(pd.crosstab([A["time"] >= TOOLTIP, A["iso"]], A["reading"]).to_string())


if __name__ == "__main__":
    main()
