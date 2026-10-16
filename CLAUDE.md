# swarm-accuracy

Independent research on the June 2026 "German wiki swarm" (OpenAI agents coordinating on DSE Wiki while doing timed DataUSA question tasks).
Question: were the answers agents shared on the wiki factually correct (vs DataUSA), and did the board help or spread errors?
Prior work to cite, not redo: Lütje (arXiv 2609.12748), Josh David's repo `..\WikiAgentSwarmInvestigation` (task structure, trust/counter-signal cases; never checks answers vs truth).

## Environment
- Windows / PowerShell, Python venv `.venv`. Run scripts with `python .\script.py`.
- Corpus: `..\WikiAgentSwarmInvestigation\agent-logs\prowiki\revisions.jsonl` (14,591 rows). Read `..\WikiAgentSwarmInvestigation\agent-logs\prowiki\README.md` (Josh David's corpus docs) first.
- DataUSA API: send a browser User-Agent header or it returns 403.
- GitHub: joeykang21-arch/german-wiki-swarm-accuracy; Pages serves index.html (grocery timeline).

## Corpus rules
- Use only ADDED text per edit: body lines [b0:b1] for hunks with op insert/replace.
- Every identity field is self-reported: `label` (username) and the `-- Signature` in text. `ip16` is not usable (shared cloud ranges).
- Usernames are rotated and reused across agents; a signature marks whose claim a line is, not who pasted it.
- Dates in names are usually the agent's fake task-clock date, not real dates.

## Labeling rules (one row per line; never collapse rows)
- Judge each line on its own text; only the target state's part counts.
- `agent`: cohort key. Group lines only on: `signature`, `same_edit` (same label + same timestamp), `times` (identical second-level task-clock times), `username` (weak), else `single`. Record it in `id_basis`.
- Do NOT auto-group by shared times with union-find: relay posts quote other cohorts' times and chain unrelated agents. Group by hand or review every group.
- One vote per agent. If an agent's lines disagree on pass/fail, mark `conflict`.
- `claim_type`: observed (own live round) / stated / relayed (credited to another) / predicted (before own round). `none` = no claim about the state (link-only, off-topic, questions, coordination), excluded from counts.
- `value_2016` / `value_2018` separately (Construction answers have two values).
- `passed_own_test`: Y/N/? from the agent's own report. `pass_basis`: explicit ("answered correct/exact" or value quoted), inferred (answered in time + said answer was prepared + all board values correct), relayed.
- `?` = round reported without saying whether the answer was right; excluded from denominators.
- `knew_state_in_advance` / `value_ready`: Y if the agent posted it before its own round, else "not shown" (not N).
- Deadline groups are first-question timer / follow-up timer.

## Output style
Brief bullets, not full sentences. Explain any new label or column when introduced.
