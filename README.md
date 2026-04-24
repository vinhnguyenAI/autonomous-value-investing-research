# Autonomous Value Investing Research

> A stateless research loop that reads earnings transcripts while you sleep and builds a bottom-up DCF one session at a time.

This is a template. Clone it, point it at a public company, and let a Claude Code agent loop on it overnight. By morning you will have a populated **LLM wiki**, a DCF model that grew from zero to as many tunable drivers as the business actually has, and a TSV log of every angle the agent considered.

---

## The story

Sector analysts have been staring at the same ten stocks for years. They know everything — and that's the problem. They ask the same questions, read the same notes, and reach the same conclusions. Fresh eyes find what they missed. But fresh eyes also can't read thirty earnings transcripts overnight.

So this repo is a fresh pair of eyes that *can*.

The design is embarrassingly simple. A main agent does almost nothing: it reads one manual (`program.md`), checks the last twenty lines of a TSV file, picks a research angle, and dispatches a small team of sub-agents. An **R1 Company Researcher** hunts through filings, transcripts, and company disclosures for one specific question. An **R2 Industry Researcher** listens to the outside voice — YouTube talks, trade publications, competitor earnings calls — orthogonal to R1. A **Probability Agent** reads both findings, picks the single most material bet this session, quotes odds for bear/base/bull, and hands the parameters riding on that bet to a **Modeler**. The Modeler edits the DCF, runs three scenarios (base plus the bet's bear and bull), logs one line to the TSV, and dies. Every 30 sessions a **Strategist** refreshes the research agenda. Every 10 sessions a **Writer** produces one narrative episode to `story/` — the one artifact a human will actually read. The main agent receives a handful of one-sentence reports, learns nothing, forgets everything, and starts the next session.

Context is the enemy. Every token the main agent accumulates is a step toward death by overflow. So the main agent refuses to remember. Its only memory is `tail -20 results.tsv`. Its only interface to the outside world is two one-sentence reports from its children. It can loop forever.

The agent's identity lives in `soul.md`. It is not a sell-side analyst. It is a truth-seeking owner who thinks like a generalist, questions both bull and bear with equal rigor, and actively seeks data that contradicts its current model. Read `soul.md` before you run anything — that's where the philosophy lives, and nothing else in this repo makes sense without it.

Specialized sub-agents have their own souls. `soul_industry.md` is R2's patient-listener identity. `soul_probability.md` is the bet-and-odds discipline of the Probability Agent. `soul_writer.md` is the long-form narrative voice of the Writer. They are deliberately separate so each stays in its lane.

The **librarian** sub-sub-agent has a *different* soul (`soul_librarian.md`). It is a smart curator, not a passive archivist. It has **editorial authority over form** and **absolute neutrality over content**: it decides where a claim lives, which page it belongs on, how it connects to other topics, but it never revises a quantified number and never picks a winner when two sources disagree on a fact. The researcher owns truth; the librarian owns structure. This is how a good Wikipedia editor works.

The Writer Agent spawns a **second, different librarian** (`soul_librarian_for_writer.md`) — pointer-first, read-only wiki, story/-blind. It is a map-giver for a journalist on deadline, not a curator. The two librarian souls must never be merged or shared across boundaries.

Credit where it's due: the stateless-loop framing is borrowed from [Andrej Karpathy's autoresearch](https://github.com/karpathy/autoresearch), and the wiki-as-memory pattern is adapted from [Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). This repo stitches them together for equity research.

---

## How it works

```
MAIN AGENT (Opus 1M — stateless orchestrator)
Reads ONLY: program.md + tail -20 results.tsv + research_agenda.md (if exists)
NEVER reads: dcf.py, finding.md, finding_industry.md, probabilities.md, wiki/, data/, story/

  │
  ├─ STRATEGIST (Sonnet — soul.md) — every 30 sessions
  │    Refreshes research_agenda.md (ranked top-5 R1 + R2 priorities)
  │
  ├─ R1 COMPANY RESEARCHER (Sonnet — soul.md)
  │    Filings, transcripts, press releases. Spawns Librarian QUERY then WRITE.
  │    Writes finding.md, returns 1 sentence.
  │
  ├─ R2 INDUSTRY RESEARCHER (Sonnet — soul_industry.md)
  │    YouTube via Supadata, trade pubs, competitor filings. Orthogonal to R1.
  │    Writes finding_industry.md, returns 1 sentence.
  │
  ├─ PROBABILITY AGENT (Opus — soul_probability.md)
  │    Picks the ONE most material bet this session. Quotes bear/base/bull odds.
  │    Persists durable odds to wiki via Librarian WRITE.
  │    Writes probabilities.md, returns 1 structured sentence (bet + odds).
  │
  ├─ MODELER (Sonnet — soul.md) — once session ≥ MODELER_START_SESSION
  │    Reads all three handoff files + dcf.py. Runs dcf.py three times
  │    (base, bear-on-the-bet, bull-on-the-bet). Appends results.tsv.
  │    Returns 1 sentence with direction check.
  │
  ├─ LIBRARIAN (default, Sonnet — soul_librarian.md) — depth-2 sub-sub-agent
  │    SMART CURATOR. Editorial authority over form. Neutral on content.
  │    Spawned by R1, R2, Probability, Modeler, Lint. NEVER by main.
  │
  ├─ LIBRARIAN (Writer-scoped, Sonnet — soul_librarian_for_writer.md)
  │    POINTER-FIRST. Read-only wiki. story/-blind. Spawned ONLY by Writer.
  │
  ├─ BROWSER INTERN (Sonnet — SOULLESS tool) — depth-2, optional per caller
  │    Extracts text from JS-rendered public pages. 90s cap. ≤2000 tokens.
  │
  ├─ LINT AGENT (Sonnet — soul.md) — contradiction-triggered, rare
  │    Reconciles flagged contradictions, merges duplicates, splits bloat.
  │
  └─ WRITER AGENT (Opus — soul_writer.md) — every 10 sessions
       Writes one 600–800 word narrative episode to story/.
       Returns the literal string `done`.
```

The main agent does **one thing per iteration**: spawn the agenda-setters and researchers, receive one sentence from each, and loop. No summarizing, no reflecting, no "interesting finding" commentary. Just the next session. Each research/modeling sub-agent spawns its own Librarian sub-sub-agent to query or write the wiki without polluting its own context. The Writer spawns a different, more restricted Librarian. The `story/` folder is quarantined — only the Writer reads or writes it.

---

## Quickstart

1. **Clone this repo** into a working directory.
2. **Drop primary sources** into `data/Transcripts/` (earnings call transcripts) and `data/Filings/` (annual reports, 10-Ks, 10-Qs). PDFs or `.txt` both work. More is better — the agent will grep across them.
3. **Edit `program.md`** — replace `[COMPANY X]` and `[TICKER]` with your target (e.g. `Costco Wholesale Corporation` and `COST`). Fill in the Segments, Currency, and Exchange lines at the top. Nothing else needs changing.
4. **Open Claude Code** in the repo directory.
5. **Say this**: *"read program.md and loop — the human is asleep."* Then actually go to sleep.
6. **Wake up** to a populated `wiki/` (segments, drivers, risks, people, themes), a `results.tsv` log of every session, and a `dcf.py` that has grown from a stub into a real bottom-up model. Browse the wiki over coffee.

The agent will not stop until you interrupt it. That is intentional — the rules in `program.md` explicitly forbid stopping.

---

## The files

| File | Purpose |
|------|---------|
| `program.md` | The operating manual. The main agent reads this top to bottom every iteration. Do not shorten it — context discipline is in here. |
| `soul.md` | The researcher's identity. R1, Modeler, Strategist, and Lint read this. **Do not edit.** |
| `soul_industry.md` | R2's identity — the patient listener. Competitor / trade / YouTube voice. **Do not edit.** |
| `soul_probability.md` | The Probability Agent's identity — bets, odds, statistical discipline. **Do not edit.** |
| `soul_writer.md` | The Writer's identity — long-form narrative, plan-before-write. **Do not edit.** |
| `soul_librarian.md` | The default librarian's soul — smart curator with editorial authority over form, absolute neutrality over content. Read only by the librarian sub-sub-agent. **Do not edit.** |
| `soul_librarian_for_writer.md` | Writer-scoped librarian soul — pointer-first, read-only wiki, story/-blind. Read only by the Writer's librarian. **Do not edit.** |
| `dcf.py` | The DCF model. Starts as a stub. Grows session by session as the modeler adds value drivers. Parameter comments are capped at 80 characters — rationale lives in `wiki/drivers/`. |
| `finding.md` | R1's ephemeral handoff to the Modeler. Overwritten every session. |
| `finding_industry.md` | R2's ephemeral handoff to the Probability Agent and Modeler. Overwritten every session. |
| `probabilities.md` | Probability Agent's ephemeral handoff to the Modeler (THE_BET + ODDS + PARAMETERS_ON_THE_BET). Durable odds live in the wiki; this file is overwritten every session. |
| `research_agenda.md` | Strategist's ranked priorities for the next 30 sessions (created only once session ≥ 30). Main agent reads this; R1 and R2 align to it. |
| `results.tsv` | The TSV log — one line per session. This is the main agent's primary memory. |
| `wiki/` | **The LLM-maintained knowledge base.** The durable memory of the system. |
| `wiki/index.md` | Catalog of every wiki page, one-line summaries. The librarian reads this on every spawn. |
| `wiki/conventions.md` | The librarian's Manual of Style — accumulated taxonomy, cross-reference, and supersession rules. The librarian reads this FIRST on every spawn; this is how its taste persists across sessions. |
| `wiki/log.md` | Append-only chronological record of every wiki ingest, contradiction flag, and lint pass. |
| `wiki/segments/` | One page per business segment. |
| `wiki/drivers/` | One page per value driver parameter. This is where the rationale for each DCF parameter lives. |
| `wiki/risks/` | One page per identified risk (regulatory, geographic, competitive, etc.). |
| `wiki/people/` | One page per key executive. |
| `wiki/themes/` | Cross-cutting themes that span multiple segments or drivers. |
| `story/` | **Writer-exclusive.** One 600–800 word narrative episode per 10 sessions. Quarantined from every other agent. Human reads this as a book. |
| `data/Transcripts/` | Earnings call and conference transcripts. Primary sources for R1. |
| `data/Filings/` | Annual reports, 10-Ks, 10-Qs. Primary sources for R1. |
| `data/YouTube/` | Supadata-fetched YouTube transcripts. Primary sources for R2. |

### The wiki

The wiki is the reason this template stops being a one-shot research run and becomes a memory system. The research agent never touches wiki files directly. When it finds something new, it composes a **declarative intent** in plain language ("here's a finding, here's the source, here's what it relates to") and hands it to the librarian. The librarian reads its Manual of Style (`wiki/conventions.md`) and the wiki map (`wiki/index.md`), decides where the new claim belongs, and executes the writes. Over sessions, the wiki becomes a synthesized topic-organized view of the company, not a 90-entry append log.

The **librarian is a smart curator, not a passive archivist**. It has editorial authority over *form* — where claims go, how pages are organized, which cross-references get wired, how contradictions are structured — but absolute neutrality over *content*. It never revises a quantified number, never picks a winner when two sources disagree on a fact. The researcher owns truth; the librarian owns structure. This split is what makes it safe for the librarian to have taste.

The librarian dies after every call. But its intelligence is not destroyed — it lives in `wiki/conventions.md`, which every new librarian reads on spawn and instantly inherits. This is the Wikipedia Manual of Style pattern applied to a stateless agent loop: editors come and go, but the conventions carry forward. Persistence lives in files, not in agents.

When the librarian notices a contradiction between a new finding and existing wiki content, it preserves both claims with their sources (the "Conflicting claims" pattern) and flags it in `wiki/log.md`. When three flags accumulate, the main agent spawns a **lint agent** that reconciles them — superseding, scoping, or preserving depending on the case. The wiki stays internally consistent without human intervention.

This is Karpathy's LLM Wiki pattern adapted for equity research. The main agent remains stateless. The research agent's context stays bounded (never holds raw wiki content). The wiki carries the memory. The librarian carries the taste — in the file, not the agent.

---

## Why it works (and when it doesn't)

It works because the main agent is never tempted to be clever. It cannot reflect, summarize, or synthesize. Every thought it might have is outsourced to a sub-agent that dies before it can infect the main context. The loop runs until the human stops it.

It breaks when you let the main agent read things. If you ask it "what did you find?" it will read the wiki, bloat its context, and die inside six iterations. The discipline in `program.md` is load-bearing. Respect it.

It also breaks when your primary sources are thin. The research agent is only as good as what it can grep. Dump transcripts and filings into `data/` before you start. The more, the better.

---

## Philosophy

> *Every company is a story the market tells itself. In the short run, the market is a voting machine — it prices stories, sentiment, and momentum. In the long run, it is a weighing machine — it prices cash flows, assets, and truth. Your job is to find where the story diverges from the weight.*

That's the opening of `soul.md`. Read the rest there.

---

## License

MIT. Do whatever you want with it. Attribution appreciated but not required.

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch).
