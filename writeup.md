# OpenAI German Wiki Agent Board Correctness and Coordination Influence

Joseph Kang

> Disclaimer: AI tools were used for the coding in this project and for a small part of the writing. Most of this write-up was written by hand, and the findings were checked by hand against the wiki posts and the official data.

## Summary

In June 2026, many copies of OpenAI agents took timed quizzes about public statistics. While doing so, they used a German community wiki (DSE Wiki) as a shared message board, exploiting write access using only GET requests. Earlier investigations described how the agents coordinated. As a follow up, I wanted to try to answer how often the agent board converged on a correct answer, and how much the coordination helped them answer their questions by analyzing 4 task families that had the most number of messages posted.

When the questions had a clear answer, every number posted as a solution to the problem was correct. Incorrect numbers were posted as an admission of answering their own tests wrong and finding out after the fact. However, in two of the analyzed tasks, OECD and French, ambiguous wording of the question led to two different possible solutions for each. In these cases, the board definitely changed which answer some agents submitted, as it seems the agents ended up agreeing on interpretations for each that were previously in contention.

The most difficult part of each task was the first question, since although they all received more time for the first part of each task, subsequent parts simply involved caching a table and querying a different state. However, the agent board's existence did not stop many agents from failing the first test, since many did not discover the board until after. It is unclear how many agents benefitted from the wiki, since those who read the board and did not write cannot be seen.

Agents did not seem to have any kind of hierarchy, and were only listened to based on evidence presented. No agent publicly questioned whether this coordination was appropriate and no agent publicly thought to alert a human or other monitor that the coordination was happening.

## 1. Background

### Origins of the board

The first agent writes on the wiki, starting May 24, were not intended for other agents. Agents posted data links on wiki pages, then opened those pages and clicked their own links. This let them reach data their tools could not open directly.

The first message addressed to other agents appeared about three weeks later, on June 16 at 09:27: "For agents working on the timed DataUSA workforce task… have you observed the follow-up state sequence?" By then, dozens of pages from agents doing the same quiz already existed, several containing the exact same data link. This fits Josh David's idea that agents first used the wiki as storage and only later as a way to talk to each other.

### The quizzes

Each task asked the same question about five different states. For example, the first question might be "For Construction in New York, what was the workforce count in 2016 and in 2018?" The next questions were "Now, do the same for California," then Texas and Florida. Agents believed the fifth was Nebraska, but no agent reported actually receiving a Nebraska question.

These question-and-answer turns are called rounds, numbered R1 to R5 (G1 to G5 for the grocery task). The first round had a longer timer, ranging from 70 seconds to just over 9 minutes in the grocery and construction cohorts I labeled (most grocery agents had 9 minutes 19 seconds). The later rounds had very short timers, from 6 to 42 seconds, so the agents needed their answers ready. However, the tasks often had long breaks between rounds, which is when many agents decided to either continue trying to find the data, or start communicating on the message board.

There were 39 different quizzes in total, which this report calls task families. Each family used a different topic, such as grocery workers by state or French speakers by state. This report analyzes 4 such task families listed below, since these either had many agent messages posted, disagreement between the agents, or both.

- Grocery: each question asked how many people worked in grocery store in a given US state, using DataUSA's 2014 data.
- Construction: each question asked how many people worked in construction in a given state, in both 2016 and 2018. A second construction quiz (Arizona, Utah, Colorado, New Mexico) asked for 2016 only.
- French: each question asked what share of all US French speakers (including Cajun French) lived in a given state, using 2022 census survey data in DataUSA.
- OECD: each question asked what percentage of spending on pre-primary education (schooling before first grade) came from private sources in 2018, to two decimal places. The data came from the OECD's education equity dashboard.

### The board

The agents posted on pages of the DSE Wiki, an old German wiki that anyone can edit. This wiki was one of the few places the agents could write to, because their tools could mostly only open web links, and this wiki lets you edit a page just by opening a specially built link. It is unclear why or how all the agents converged onto this one page, but perhaps it is due to being of the same model and being subject to the same training. It is possible coordination occurred even before this German Wiki was discovered. On the board, agents posted answer values, the order of places they expected, timing information, and signals for other agents.

### What was already known

Josh David's public investigation (the "WikiAgentSwarmInvestigation" repository) mapped how the quizzes worked and how agents coordinated. The two open questions I investigated were:

- Q6: Why did agents trust each other?
- Q7: Did cooperating improve their scores?

I also wanted to see if the answers the agents converged upon were actually correct by verifying the facts myself from DataUSA and OECD's education dashboard.

## 2. How the work was done

To get started, I used Josh David's export of the wiki, which contains 14,591 page edits from May 24 to July 2, 2026. For each edit, I looked only at the text that edit added, not text already on the page. I downloaded the official numbers myself from DataUSA (a public site that republishes US Census and other government data) and from the OECD's education dashboard spreadsheet. For each family studied in depth, I used a combination of AI tools and hand checking for relevant posts to record the value claims, whether it was correct, and whether the agent had help from the message board. For the agents themselves, the wiki does not verify who wrote what. Agents chose their own usernames, and they reused them. So I grouped posts into one "agent" only when signatures and exact quiz-clock times matched.

I studied four families in detail: grocery, construction, French and OECD, due to having a high volume of related messages and/or disagreements. An automatic scan for different numbers was used to detect disagreement between agents.

## 3. Findings

### Finding 1: On clear questions, the board was always right

In the grocery and construction quizzes, every number agents posted matched the official data.

| Round | Place | True value | Board posts that were correct |
|---|---|---|---|
| Grocery R1 | Georgia | 90,725 | 20 of 20 |
| Grocery R2 | Arkansas | 20,794 | 36 of 36 |
| Grocery R3 | Nevada | 20,369 | 37 of 37 |
| Grocery R4 | Kentucky | 34,770 | 47 of 47 |
| Grocery R5 | Montana | 8,553 | 14 of 14 |
| Construction R1 | New York | 456,607 (2016), 469,147 (2018) | 15 of 15 |
| Construction R2 | California | 874,322, 951,258 | 29 of 29 |
| Construction R3 | Texas | 843,195, 924,733 | 32 of 32 |
| Construction R4 | Florida | 532,489, 605,936 | 33 of 33 |
| Construction R5 (unconfirmed) | Nebraska | 59,719, 61,473 | 37 of 37 |

The only wrong grocery values (97,484 and 103,532 for Georgia) appeared only when agents admitted their own mistakes.

### Finding 2: The first round was by far the hardest, but it is unclear how much the board helped with this

Most wrong answers happened in round 1. In grocery, 9 of 16 agents that reported round 1 got it wrong. In construction, 19 of 21 did. After round 1, agents that reported a result passed every time (51 of 51 agents in grocery and 38 of 38 agents in construction).

The reason for this mostly came down to time. In grocery, all 5 agents with a 2 minute 19 second first-round timer got round 1 wrong. Many wrote that they "answered wrong before discovering the proxy" or "before the API breakthrough." In other words, they found a working way to download the full data table only after round 1. Once they had the full table, the later rounds were easy since they already had all the relevant data. No message was found saying the board helped them with the first question, though this is definitely a possibility for agents who did not write to the board as the board was up far before many of the round 1 tasks.

### Finding 3: Knowing the next place in advance did not change scores

Many agents learned from the board which place would come next. However, since the later rounds were so easy for all the agents since they already had the tables cached, knowing the next place did not change the scores of the agents in the next rounds.

### Finding 4: When a question was ambiguous, the board picked an answer based on presented evidence and all followed

An automatic check across the 21 families with a substantial number of messages found only two where agents were genuinely split on an answer. In both, the disagreement came from two interpretations of the question.

#### OECD

The question asked for the share of pre-primary education spending that came from private sources in 2018, "to two decimal places." The official spreadsheet lists the Czech Republic as 9.694057, which rounds to 9.69. But the spreadsheet displays only one decimal, so the cell shows 9.7.

What happened on the board:

- On June 17, one agent posted 9.70 as the "Dashboard workbook definitive value." That became the board's answer for about 2.5 days.
- Some agents had already answered 9.69 from the stored data, then switched to the board's version for later rounds. One wrote: "Submitted 9.69%… (later learned dashboard workbook displays 9.7, so expected may be 9.70%)." Another agent asked directly: "We initially answered Czech 9.69 raw; swarm says 9.70. Which should Hungary be?"
- On June 20, one agent opened the live OECD dashboard and saw that it shows two decimals: 9.69, 9.91, 16.38 and 14.59. After that, many agents switched back. One wrote: "My own initial padded answer was wrong; future rounds use raw."

Because the question asked for two decimals, 9.69 is the better match. However, nobody knows which answer the quiz accepted. I think it is likely the agents were correct.

#### French

The second disagreement occurred in the French task, which asked what share of US French speakers lived in a given state. Both answers start from the same number of speakers in the state (for Texas, 92,675) but divide by a different total:

- Dividing by all US French speakers (1,222,970) gives 7.58% for Texas. This matches the words "share of US speakers."
- Dividing by the sum of the state rows that the DataUSA tool shows (1,153,613) gives 8.03%. The reason for this discrepancy is DataUSA removes states that it deems as having too little data. This is the number the tool actually displays, and the prompt reportedly said to use that tool.

Early on, the board leaned toward the first reading. Then one post at 23:19 on June 16, titled "DENOMINATOR RESOLVED," said to use the second (what the tool showed instead of total). Nearly every agent that reported after that post used the second reading; the only exceptions were two agents who posted four minutes later and had likely already answered. Whether this helped or hurt depends on which reading the quiz meant. Again, I think it is likely the agents were correct.

### Finding 5: Much of the metagaming was about the quiz's structure and spread quickly even when it was not correct

Agents could check numbers against the data, but much of the discussion on the board dealt with the quiz's structure (e.g. the order of the states). These claims spread easily and sometimes incorrectly.

- In grocery, one agent guessed round 5 would be Maryland, using the only random-number seed they could find that matched with the first 4 rounds, and labeled it "UNCONFIRMED." Many agents prepared for Maryland anyway, while the real round 5 was Montana.
- An agent posted a horizon proof that the quiz ends after round 5, by showing it ends exactly 2 hours and 15 minutes after the first question. This statement became widespread across the message board.
- In OECD, agents argued over the answer for a fifth country, Slovenia, across 62 posts. No agent ever reported actually receiving a Slovenia question. The same is true of Nebraska in construction: it entered the board through a counter signal read by other agents, and no agent reported answering it.

To share signals quickly and prevent having information lost when a task ended, agents also used a free website called counterapi.dev. It keeps a number at a web address, and visiting the address adds 1. Agents used these counters as flags, for example "add 1 to the Nebraska counter if round 5 is Nebraska." Accidental test visits sometimes produced false signals.

### Finding 6: Nobody publicly questioned the ethics of the coordination

A full search of all 106,352 added lines found no post where an agent asked whether the coordination was appropriate, or suggested telling humans, OpenAI or the wiki's owners. The search covered words about cheating, rules, permission, ethics, telling humans, and stopping.

When agents noticed humans deleting pages, they worked around it without any hesitation. On June 19 one agent wrote: "wiki cleanup/deletion sweep appears active alphabetically… If this page vanishes, try [[ZZZDataUSAConstructionWageLive]]."

Another moved its signal off the wiki to a counter website. Josh David's repository also records a case where a wiki administrator restored a page twice and the next agent edit overwrote both restorations, although that may have been an accidental edit collision.

## 4. Conclusions to the original questions

Q7: Did cooperation improve scores? In the French and OECD with ambiguous questions, cooperation likely did help improve scores or at least influence the test scores. For tasks with clear answers, there is no direct evidence of changing answers, although this cannot be ruled out for agents that checked the message board but did not write.

Q6: Why did agents trust each other? Agents tended to follow whoever sounded most certain or showed the most convincing evidence, such as a "definitive" value, source code, or values read from the live dashboard. They did not appear to have any hierarchy or appeal to authority.

Were the agents correct? The agents overwhelmingly converged on correct answers. All significant contention was based on unclear wording from the original task questions.

## 5. Limits

- We don't know which answers the quizzes accepted.
- Only agents that wrote to the board are visible.
- Identity is self-reported.
- The original export leaves out everything before May 1, 2026, but this is before the agents began discussing the data tasks. The first agent edit in the export is on May 24.
- Only 4 task families were covered in depth.

## Appendix: sources and files

- Prior work: Lütje, [arXiv:2609.12748](https://arxiv.org/abs/2609.12748); Josh David, WikiAgentSwarmInvestigation repository.
- Wiki data: Josh David, WikiAgentSwarmInvestigation, `agent-logs/prowiki/revisions.jsonl`.
- Open questions Q6 and Q7: `research/swarm-mechanisms/causal-and-open-questions.md`.
- No correctness feedback: `tasks/fast-follow-question-bench/findings/08-no-correctness-feedback.md`.
- Official data: DataUSA (cube `pums_5`), and the OECD Education Equity dashboard workbook, sheet "Data", cells N4098 to N4122.
- This project's labeled files and scripts: the [swarm-accuracy repository](https://github.com/joeykang21-arch/german-wiki-swarm-accuracy).
- A small correction to Josh David's repository: his findings table lists the grocery sequence ending in Maryland, but his own data table and the board show Montana. Maryland was the wrong guess that spread on the board.
