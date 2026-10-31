# The Correctness and Effectiveness of OpenAI's German Wiki Swarm

Independent research on the June 2026 "German wiki swarm": OpenAI agents coordinating on the DSE Wiki while doing timed DataUSA and OECD quiz tasks. This project checks whether the answers agents shared on the wiki matched the official data, and whether the board helped or influenced the swarm's live answers.

Read the write-up: [writeup.md](writeup.md)

> Disclaimer: AI tools were used for the coding in this project and for a small part of the writing. Most of the write-up was written by hand, and the findings were checked by hand against the wiki posts and the official data.

## Timeline pages

Served by GitHub Pages at https://joeykang21-arch.github.io/german-wiki-swarm-accuracy/

- [grocery_timeline.html](grocery_timeline.html): grocery task
- [construction_timeline.html](construction_timeline.html): construction task
- [french_timeline.html](french_timeline.html): French speakers task
- [oecd_timeline.html](oecd_timeline.html): OECD pre-primary spending task
- [before_swarm_timeline.html](before_swarm_timeline.html): how the board formed, before agents addressed each other

## Data

- Wiki corpus: Josh David's WikiAgentSwarmInvestigation repository, `agent-logs/prowiki/revisions.jsonl` (14,591 edits). Not included here; scripts expect it at `..\WikiAgentSwarmInvestigation\`.
- Official values: DataUSA (`fetch_truth_grocery.py`, `fetch_truth_construction`, `fetch_truth_french.py`) and the OECD Education Equity dashboard workbook (`fetch_truth_oecd.py`). Raw downloads are in `truth/`; checked values are in `*_truth.csv`.

## Layout

- `*_labeled.csv` (grocery, root folder), `construction/`, `french/`, `oecd/`: one row per wiki line about a state, with hand-checked labels. Labeling rules are in [CLAUDE.md](CLAUDE.md).
- `analyze_state.py`: accuracy and pass/fail summary for one grocery or construction state.
- `q7/`: did the board help (data routes, round 1 timing).
- `screen/`: automatic scan for families where agents disagreed on a value.
- `show.py`: print wiki posts containing some text, for checking findings by hand.

## Running

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\analyze_state.py Georgia
python .\show.py "DENOMINATOR RESOLVED"
```

DataUSA returns 403 unless requests send a browser User-Agent header.
