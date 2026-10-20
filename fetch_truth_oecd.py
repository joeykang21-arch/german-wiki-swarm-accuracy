r"""Look up the raw OECD values behind the Education Equity task (Czech 9.69 vs 9.70 dispute).

Task (from agents' own posts): "share of private expenditure in the early years of education
(2018) ... value (to two decimal places) for Pre-Primary education." Sequence starts
Czech Republic -> Hungary -> Poland -> Slovak Republic.
Data route agents posted: the dashboard workbook (no OECD API / SDMX query was ever posted).

Usage (from the swarm-accuracy folder):
    .venv\Scripts\python fetch_truth_oecd.py
Output: truth/oecd_<stamp>/Data-Education-equity-dashboard.xlsx and oecd_truth.csv
Reads the xlsx with zipfile + xml only (raw stored doubles, plus each cell's number format).
"""
import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

# Exact URL OECDJun26PrecisionScout posted (06-20 03:41:17), double slash included.
URL = ("https://www.oecd.org//content/dam/oecd/en/about/projects/edu/"
       "education-for-inclusive-societies/Data-Education-equity-dashboard.xlsx")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) swarm-accuracy research"}
INDICATOR = "Share of private expenditure in the early years of education (2018)"
COUNTRIES = ["CZE", "HUN", "POL", "SVK"]
# Values agents posted: (ISO3, swarm consensus, raw-reading alternative)
BOARD = {"CZE": ("9.70", "9.69"), "HUN": ("9.90", "9.91"), "POL": ("16.40", "16.38"), "SVK": ("14.60", "14.59")}
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
out_dir = Path("truth") / f"oecd_{stamp}"
out_dir.mkdir(parents=True)
resp = requests.get(URL, headers=HEADERS, timeout=120)
print(f"HTTP {resp.status_code}  {len(resp.content):,} bytes")
resp.raise_for_status()
xlsx = out_dir / "Data-Education-equity-dashboard.xlsx"
xlsx.write_bytes(resp.content)

z = zipfile.ZipFile(xlsx)
strings = ["".join(t.text or "" for t in si.iter(M + "t"))
           for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(M + "si")]
styles = z.read("xl/styles.xml").decode()
xfs = re.findall(r"<xf [^>]*>", re.search(r"<cellXfs[^>]*>(.*?)</cellXfs>", styles, re.S).group(1))
fmts = dict(re.findall(r'<numFmt numFmtId="(\d+)" formatCode="([^"]*)"', styles))
updated = None
out = []
for name in sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet")):
    for row in ET.fromstring(z.read(name)).iter(M + "row"):
        cells = {}
        for c in row.findall(M + "c"):
            v = c.find(M + "v")
            if v is None:
                continue
            col = re.match(r"[A-Z]+", c.get("r")).group()
            cells[col] = (strings[int(v.text)] if c.get("t") == "s" else v.text, c.get("s"))
        txt = {k: v[0] for k, v in cells.items()}
        if txt.get("A", "").startswith("Updated"):
            updated = txt["A"]
        if (txt.get("D", "").strip() == INDICATOR and txt.get("H") in COUNTRIES
                and txt.get("M") == "Pre-primary education"):
            raw, style = cells["N"]
            fid = re.search(r'numFmtId="(\d+)"', xfs[int(style or 0)]).group(1)
            iso = txt["H"]
            out.append({"iso3": iso, "country": txt["I"], "raw": raw, "cell_format": fmts.get(fid, f"builtin {fid}"),
                        "round_2dp": f"{float(raw):.2f}", "board_consensus": BOARD[iso][0],
                        "board_alternative": BOARD[iso][1]})

print("Workbook:", updated)
for r in out:
    print(f"{r['iso3']}  raw {r['raw']:<20} format {r['cell_format']:<5} 2dp {r['round_2dp']:<6} "
          f"board {r['board_consensus']} / alt {r['board_alternative']}")
with open("oecd_truth.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print("Wrote oecd_truth.csv")
