# Autonomous Value Investing Research

> A stateless research loop that reads earnings transcripts while you sleep and builds a bottom-up DCF one session at a time.

This is a template. Clone it, point it at a public company, and let a Claude Code agent loop on it overnight. By morning you will have a populated **LLM wiki**, a DCF model that grew from zero to as many tunable drivers as the business actually has, and a TSV log of every angle the agent considered.

---

## The story

Sector analysts have been staring at the same ten stocks for years. They know everything — and that's the problem. They ask the same questions, read the same notes, and reach the same conclusions. Fresh eyes find what they missed. But fresh eyes also can't read thirty earnings transcripts overnight.

So this repo is a fresh pair of eyes that *can*.

The design is embarrassingly simple. A main agent does almost nothing: it reads one manual (`program.md`), checks the last twenty lines of a TSV file, picks a research angle, and dispatches two sub-agents. A **Research Agent** hunts through transcripts, filings, and the web for one specific question, writes what it found to a scratch file, and dies. A **Modeler Agent** reads that scratch file, edits the DCF, runs it, logs one line to the TSV, and dies. The main agent receives exactly two sentences, learns nothing, forgets everything, and starts the next session.

Context is the enemy. Every token the main agent accumulates is a step toward death by overflow. So the main agent refuses to remember. Its only memory is `tail -20 results.tsv`. Its only interface to the outside world is two one-sentence reports from its children. It can loop forever.

The agent's identity lives in `soul.md`. It is not a sell-side analyst. It is a truth-seeking owner who thinks like a generalist, questions both bull and bear with equal rigor, and actively seeks data that contradicts its current model. Read `soul.md` before you run anything — that's where the philosophy lives, and nothing else in this repo makes sense without it.

The **librarian** sub-sub-agent has a *different* soul (`soul_librarian.md`). It is a smart curator, not a passive archivist. It has **editorial authority over form** and **absolute neutrality over content**: it decides where a claim lives, which page it belongs on, how it connects to other topics, but it never revises a quantified number and never picks a winner when two sources disagree on a fact. The researcher owns truth; the librarian owns structure. This is how a good Wikipedia editor works.

Credit where it's due: the stateless-loop framing is borrowed from [Andrej Karpathy's autoresearch](https://github.com/karpathy/autoresearch), and the wiki-as-memory pattern is adapted from [Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). This repo stitches them together for equity research.

---

## How it works

```
MAIN AGENT (Opus 1M — stateless orchestrator)
┌─────────────────────────┐
│ Reads ONLY:             │        RESEARCH AGENT (Sonnet — soul.md)
│  - program.md           │ spawn  ┌────────────────────────────┐
│  - tail -20 tsv         │ ─────> │ 1. spawn LIBRARIAN         │
│                         │        │ 2. read primary sources    │
│ NEVER reads:            │        │ 3. INGEST into wiki/       │
│  - dcf.py               │        │ 4. write finding.md        │
│  - finding.md           │ <───── │ 5. return 1 sentence       │
│  - wiki/                │ 1 sent └──────────┬─────────────────┘
│  - data/                │                   │ spawn
│                         │                   ▼
│ Receives 2 sentences:   │        LIBRARIAN (Sonnet — soul_librarian.md)
│  - 1 from research      │        ┌────────────────────────────┐
│  - 1 from modeler       │        │ - Reads wiki/ only         │
│  - (+1 from lint, rare) │        │ - Anti-interpretive soul   │
│                         │        │ - Returns compressed answer│
│                         │        └────────────────────────────┘
│                         │
│                         │        MODELER AGENT (Sonnet — soul.md)
│                         │ spawn  ┌────────────────────────────┐
│                         │ ─────> │ 1. spawn LIBRARIAN         │
│                         │        │ 2. read finding.md + dcf.py│
│                         │        │ 3. edit dcf.py (80-char    │
│                         │        │    comments, REPLACE rule) │
│                         │        │ 4. run dcf.py --json       │
│                         │        │ 5. append results.tsv      │
│                         │ <───── │ 6. return 1 sentence       │
└─────────────────────────┘ 1 sent └────────────────────────────┘
```

The main agent does **one thing per iteration**: spawn → receive → spawn → receive → loop. No summarizing, no reflecting, no "interesting finding" commentary. Just the next session. Each sub-agent spawns its own librarian sub-sub-agent to query the wiki without polluting its own context.

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
| `soul.md` | The agent's identity. Research, modeler, and lint agents read this. **Do not edit.** |
| `soul_librarian.md` | The librarian's distinct soul — smart curator with editorial authority over form, absolute neutrality over content. Read only by the librarian sub-sub-agent. **Do not edit.** |
| `dcf.py` | The DCF model. Starts as a ~40-line stub. Grows session by session as the modeler adds value drivers. Parameter comments are capped at 80 characters — rationale lives in `wiki/drivers/`. |
| `finding.md` | Ephemeral handoff between research and modeler agents. Overwritten every session. Ignore it. |
| `results.tsv` | The TSV log — one line per session. This is the main agent's entire memory. |
| `wiki/` | **The LLM-maintained knowledge base.** This is the durable memory of the system. |
| `wiki/index.md` | Catalog of every wiki page, one-line summaries. The librarian reads this on every spawn. |
| `wiki/conventions.md` | The librarian's Manual of Style — accumulated taxonomy, cross-reference, and supersession rules. The librarian reads this FIRST on every spawn; this is how its taste persists across sessions. |
| `wiki/log.md` | Append-only chronological record of every wiki ingest, contradiction flag, and lint pass. |
| `wiki/segments/` | One page per business segment. |
| `wiki/drivers/` | One page per value driver parameter. This is where the rationale for each DCF parameter lives. |
| `wiki/risks/` | One page per identified risk (regulatory, geographic, competitive, etc.). |
| `wiki/people/` | One page per key executive. |
| `wiki/themes/` | Cross-cutting themes that span multiple segments or drivers. |
| `data/Transcripts/` | Earnings call and conference transcripts. Primary sources. |
| `data/Filings/` | Annual reports, 10-Ks, 10-Qs. Primary sources. |

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
