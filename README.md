# Autonomous Value Investing Research

> A stateless research loop that reads earnings transcripts while you sleep and builds a bottom-up DCF one session at a time.

This is a template. Clone it, point it at a public company, and let a Claude Code agent loop on it overnight. By morning you will have a populated research journal, a DCF model that grew from zero to ~20 tunable drivers, and a TSV log of every angle the agent considered.

---

## The story

Sector analysts have been staring at the same ten stocks for years. They know everything — and that's the problem. They ask the same questions, read the same notes, and reach the same conclusions. Fresh eyes find what they missed. But fresh eyes also can't read thirty earnings transcripts overnight.

So this repo is a fresh pair of eyes that *can*.

The design is embarrassingly simple. A main agent does almost nothing: it reads one manual (`program.md`), checks the last twenty lines of a TSV file, picks a research angle, and dispatches two sub-agents. A **Research Agent** hunts through transcripts, filings, and the web for one specific question, writes what it found to a scratch file, and dies. A **Modeler Agent** reads that scratch file, edits the DCF, runs it, logs one line to the TSV, and dies. The main agent receives exactly two sentences, learns nothing, forgets everything, and starts the next session.

Context is the enemy. Every token the main agent accumulates is a step toward death by overflow. So the main agent refuses to remember. Its only memory is `tail -20 results.tsv`. Its only interface to the outside world is two one-sentence reports from its children. It can loop forever.

The agent's identity lives in `soul.md`. It is not a sell-side analyst. It is a truth-seeking owner who thinks like a generalist, questions both bull and bear with equal rigor, and actively seeks data that contradicts its current model. Read `soul.md` before you run anything — that's where the philosophy lives, and nothing else in this repo makes sense without it.

Credit where it's due: the stateless-loop framing is borrowed from [Andrej Karpathy's autoresearch](https://github.com/karpathy/autoresearch). This repo adapts the same idea for equity research.

---

## How it works

```
MAIN AGENT (Opus 1M)
┌─────────────────────────┐
│ Reads ONLY:             │
│  - program.md           │         RESEARCH AGENT (Sonnet 200K)
│  - tail -20 tsv         │  spawn  ┌──────────────────────────────┐
│                         │ ──────> │ - Web search                 │
│ NEVER reads:            │         │ - Read transcripts/filings   │
│  - dcf.py               │         │ - Append notes.md            │
│  - finding.md           │         │ - Write finding.md           │
│  - data/                │ <────── │ - Returns 1 sentence         │
│  - notes.md             │  1 sent └──────────────────────────────┘
│                         │
│ Receives from research: │         MODELER AGENT (Sonnet 200K)
│  1 sentence ONLY        │  spawn  ┌──────────────────────────────┐
│                         │ ──────> │ - Read finding.md            │
│ Receives from modeler:  │         │ - Read/edit dcf.py           │
│  1 sentence ONLY        │         │ - Run python3 dcf.py --json  │
│                         │ <────── │ - Append results.tsv         │
└─────────────────────────┘  1 sent │ - Returns 1 sentence         │
                                    └──────────────────────────────┘
```

The main agent does **one thing per iteration**: spawn → receive → spawn → receive → loop. No summarizing, no reflecting, no "interesting finding" commentary. Just the next session.

---

## Quickstart

1. **Clone this repo** into a working directory.
2. **Drop primary sources** into `data/Transcripts/` (earnings call transcripts) and `data/Filings/` (annual reports, 10-Ks, 10-Qs). PDFs or `.txt` both work. More is better — the agent will grep across them.
3. **Edit `program.md`** — replace `[COMPANY X]` and `[TICKER]` with your target (e.g. `Costco Wholesale Corporation` and `COST`). Fill in the Segments, Currency, and Exchange lines at the top. Nothing else needs changing.
4. **Open Claude Code** in the repo directory.
5. **Say this**: *"read program.md and loop — the human is asleep."* Then actually go to sleep.
6. **Wake up** to a populated `results.tsv`, a thick `notes.md`, and a `dcf.py` that has grown from a stub into a real bottom-up model. Read `notes.md` over coffee.

The agent will not stop until you interrupt it. That is intentional — the rules in `program.md` explicitly forbid stopping.

---

## The files

| File | Purpose |
|------|---------|
| `program.md` | The operating manual. The main agent reads this top to bottom every iteration. Do not shorten it — context discipline is in here. |
| `soul.md` | The agent's identity. Every sub-agent reads this before thinking. **Do not edit.** |
| `dcf.py` | The DCF model. Starts as a ~40-line stub. Grows session by session as the modeler adds value drivers. |
| `notes.md` | The human-readable research journal. Append-only. Read this. |
| `finding.md` | Ephemeral handoff between research and modeler agents. Overwritten every session. Ignore it. |
| `results.tsv` | The TSV log — one line per session. This is the main agent's entire memory. |
| `data/Transcripts/` | Earnings call and conference transcripts. Primary sources. |
| `data/Filings/` | Annual reports, 10-Ks, 10-Qs. Primary sources. |

---

## Why it works (and when it doesn't)

It works because the main agent is never tempted to be clever. It cannot reflect, summarize, or synthesize. Every thought it might have is outsourced to a sub-agent that dies before it can infect the main context. The loop runs until the human stops it.

It breaks when you let the main agent read things. If you ask it "what did you find?" it will read `notes.md`, bloat its context, and die inside six iterations. The discipline in `program.md` is load-bearing. Respect it.

It also breaks when your primary sources are thin. The research agent is only as good as what it can grep. Dump transcripts and filings into `data/` before you start. The more, the better.

---

## Philosophy

> *Every company is a story the market tells itself. In the short run, the market is a voting machine — it prices stories, sentiment, and momentum. In the long run, it is a weighing machine — it prices cash flows, assets, and truth. Your job is to find where the story diverges from the weight.*

That's the opening of `soul.md`. Read the rest there.

---

## License

MIT. Do whatever you want with it. Attribution appreciated but not required.

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch).
