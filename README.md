# Autonomous Value Investing Research

> A stateless research loop that reads earnings transcripts while you sleep and builds a sourced, audited DCF of a public company — one driver at a time.

Clone this template. Point it at a ticker. Drop in transcripts and filings. Tell Claude Code to loop. Go to sleep.

By morning you have two things that didn't exist when you went to bed.

---

## What you get

### 1. A DCF that knows every parameter that drives the business

Most DCFs you'll see have eight knobs: revenue growth, EBIT margin, tax rate, WACC, terminal growth, capex, working capital, share count. Eight. For a business with five segments, a thousand SKUs, regulatory exposure across six jurisdictions, and a treasury float that earns interest.

Eight knobs is theatre.

This loop produces a DCF whose parameter count is bounded by the business itself, not by what fits on an Excel tab. The Modeler agent adds **exactly one new driver per session**, each tied to a primary source (a 10-K page, an earnings call transcript, a published rate). Mature models hold **dozens of driver cells, often well past a hundred**. Every cell carries an inline `# data/...` citation pointing to the file the number came from. Rationale lives in the wiki, not the comment.

The metric the loop optimises is **`driver_count`** — the number of parameters that (a) carry a sourced citation AND (b) actually move intrinsic value when perturbed. It's computed by an external auditor (`dcf_score.py`) that runs after every commit. If `driver_count` didn't grow, the main agent runs `git reset --hard HEAD~1` and the bad commit disappears. Karpathy's ratchet. The model can only get bigger and more honest. It cannot drift.

The output isn't a single IV figure. It's an instrumented model: you can wiggle any one of the 134 knobs, see exactly which line of which filing justified that knob, and watch IV move. The DCF is a tool for **understanding the business**, not for confirming a price target.

### 2. A wiki of the company that synthesises itself

Research output normally rots. You read a transcript, scribble a note, file it under the company name. Six months later the note is unfindable, the transcript is forgotten, and you're rereading the same page.

This loop builds a **wiki** instead. Every finding the research agents surface is handed to a Librarian sub-agent — a smart curator with editorial authority over *form* (where claims go, how pages connect, how contradictions are structured) and absolute neutrality over *content* (never revises a number, never picks a winner). Over sessions, the wiki grows topic-organised pages: one per segment, one per driver, one per risk, one per executive, plus cross-cutting themes.

```
wiki/
├─ index.md         — catalog of every page, read by the librarian on every spawn
├─ conventions.md   — accumulated Manual of Style: how the librarian thinks (persists across sessions)
├─ log.md           — append-only operations log + contradiction flags
├─ segments/        — one page per reported business segment
├─ drivers/         — one page per DCF value driver (this is where the rationale for each parameter lives)
├─ risks/           — one page per identified risk
├─ people/          — one page per key executive
└─ themes/          — cross-cutting themes that span multiple segments/drivers
```

You don't read 90 finding files in chronological order. You open `wiki/segments/{segment_name}.md` and read what the loop knows about that segment, with sources cited. Or `wiki/drivers/{parameter_name}.md` and see why the DCF knob is set where it is. The wiki is **the artifact worth keeping**. Everything else (sessions, scratch files, even `dcf.py` itself) regenerates from it.

The librarian dies after every call. But its taste isn't destroyed — it lives in `wiki/conventions.md`, which every new librarian reads on spawn and instantly inherits. This is the Wikipedia Manual of Style pattern applied to a stateless agent loop. Persistence lives in files, not in agents.

---

## Quickstart

1. **Clone this repo** into a working directory.
2. **Drop primary sources** into `data/Transcripts/` (earnings call transcripts) and `data/Filings/` (annual reports, 10-Ks, 10-Qs). PDFs or `.txt` both work. More is better — the agents grep across everything.
3. **Edit `program.md`** at the top — replace `[COMPANY X]` and `[TICKER]` with your target (e.g. `Costco Wholesale Corporation` and `COST`). Fill in the Segments, Currency, and Exchange lines. Nothing else needs changing.
4. **Open Claude Code** in the repo directory.
5. **Say this**: *"read program.md and loop — the human is asleep."* Then actually go to sleep.
6. **Wake up** to a populated `wiki/`, a `results.tsv` log of every session, and a `dcf.py` that grew from a stub into a real bottom-up model. Browse the wiki over coffee.

The agent will not stop until you interrupt it. That is intentional — the rules in `program.md` explicitly forbid stopping.

---

## How the loop works

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
  │    Writes finding.md (with a DRIVER_CANDIDATE block on top), returns 1 sentence.
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
  │    Reads three handoff files + dcf.py. Picks ONE driver candidate.
  │    Adds/splits/refactors it with a `# data/...` source pointer.
  │    Exactly ONE commit per session. Does NOT write results.tsv.
  │    Returns 1 sentence (includes commit SHA).
  │
  ├─ VERIFIER (Sonnet — embedded soul) — always after Modeler
  │    Runs `python3 dcf_score.py` to compute new driver_count.
  │    Compares to prior count, picks status (up/flat/down/crash) and
  │    action (continue / git reset / no reset needed). Appends ONE
  │    row to results.tsv BEFORE returning. Returns 1 sentence.
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
  │    Reconciles flagged wiki contradictions, merges duplicates, splits bloat.
  │
  └─ WRITER AGENT (Opus — soul_writer.md) — every 10 sessions
       Writes one 600–800 word narrative episode to story/.
       Returns the literal string `done`.
```

The main agent does **one thing per iteration**: spawn the agenda-setters and researchers, receive one sentence from each, and loop. No summarising, no reflecting, no "interesting finding" commentary. Just the next session. Every sub-agent dies after returning its single sentence — that's how the main context stays bounded.

Context is the enemy. Every token the main agent accumulates is a step toward death by overflow. So the main agent refuses to remember. Its only memory is `tail -20 results.tsv`. Its only interface to its children is one sentence each. It can loop forever.

---

## The ratchet (why this doesn't drift)

After every Modeler commit, the Verifier runs `dcf_score.py`. The auditor:

1. Parses the PARAMETERS section of `dcf.py`.
2. Checks each parameter has a `# data/...` source pointer.
3. Perturbs each parameter individually (`--override name=value`) and re-runs the model.
4. Counts how many parameters (a) are sourced AND (b) genuinely move IV.

That number is `driver_count`. The Verifier compares to the prior session's count and picks one of four outcomes:

| status | meaning                                          | action               |
|--------|--------------------------------------------------|----------------------|
| `up`   | a sourced, IV-affecting driver was added         | keep the commit      |
| `flat` | refactor or value-tweak; no new active driver    | keep the commit      |
| `down` | a driver was lost or broken                      | `git reset --hard HEAD~1` |
| `crash`| `dcf.py` won't parse or run                      | `git reset --hard HEAD~1` |

The Verifier writes a row to `results.tsv` **before** returning. `results.tsv` is untracked, so the failed-attempt row survives the reset. You can read the TSV later and see every session the loop tried, including the ones it rolled back.

The model can only ratchet upward. It cannot drift.

---

## Files

| File | Purpose |
|------|---------|
| `program.md` | The operating manual. The main agent reads this top to bottom every iteration. Do not shorten it — context discipline is in here. |
| `soul.md` | The researcher's identity. R1, Modeler, Strategist, Lint read this. **Do not edit.** |
| `soul_industry.md` | R2's identity — the patient listener. Competitor / trade / YouTube voice. **Do not edit.** |
| `soul_probability.md` | The Probability Agent's identity — bets, odds, statistical discipline. **Do not edit.** |
| `soul_writer.md` | The Writer's identity — long-form narrative, plan-before-write. **Do not edit.** |
| `soul_librarian.md` | Default librarian's soul — smart curator. Editorial authority over form, absolute neutrality over content. **Do not edit.** |
| `soul_librarian_for_writer.md` | Writer-scoped librarian soul — pointer-first, read-only wiki, story/-blind. **Do not edit.** |
| `dcf.py` | The DCF model. Starts as a stub. Grows session by session as the Modeler adds ONE driver per session, each carrying a `# data/...` source pointer. Parameter comments capped at 80 characters — rationale lives in `wiki/drivers/`. |
| `dcf_score.py` | The external auditor. Computes `driver_count`. Read-only by all agents — must NOT be edited. Verifier runs it after every Modeler commit. |
| `finding.md` | R1's ephemeral handoff to the Modeler. Overwritten every session. Starts with a DRIVER_CANDIDATE block so the Modeler can wire it directly. |
| `finding_industry.md` | R2's ephemeral handoff. Overwritten every session. |
| `probabilities.md` | Probability Agent's ephemeral handoff (THE_BET + ODDS + PARAMETERS_ON_THE_BET). Durable odds live in the wiki; this file is overwritten every session. |
| `research_agenda.md` | Strategist's ranked priorities for the next 30 sessions (created only once session ≥ 30). |
| `results.tsv` | One row per session. Schema: `session  commit_sha  driver_count  status  description`. Untracked, survives `git reset --hard HEAD~1`. |
| `wiki/` | **The LLM-maintained knowledge base.** Durable memory. See "What you get" above. |
| `story/` | **Writer-exclusive.** One 600–800 word narrative episode per 10 sessions. Quarantined from every other agent. Read it as a book. |
| `data/Transcripts/` | Earnings call and conference transcripts. Primary sources for R1. |
| `data/Filings/` | Annual reports, 10-Ks, 10-Qs. Primary sources for R1. |
| `data/YouTube/` | Supadata-fetched YouTube transcripts. Primary sources for R2. |

---

## Souls

The agent's identity lives in `soul.md`. It is not a sell-side analyst. It is a truth-seeking owner who thinks like a generalist, questions both bull and bear with equal rigor, and actively seeks data that contradicts its current model. Read `soul.md` before you run anything — that's where the philosophy lives, and nothing else in this repo makes sense without it.

Specialised sub-agents have their own souls. `soul_industry.md` is R2's patient-listener identity. `soul_probability.md` is the bet-and-odds discipline of the Probability Agent. `soul_writer.md` is the long-form narrative voice of the Writer.

The librarian has a **different** soul (`soul_librarian.md`). It is a smart curator, not a passive archivist. The researcher owns truth; the librarian owns structure. The Writer Agent spawns a **second, different** librarian (`soul_librarian_for_writer.md`) — pointer-first, read-only wiki, story/-blind. The two librarian souls must never be merged or shared.

Souls are identity files. **Do not edit them** without thinking very hard first.

---

## The wiki, in more detail

The research agents never touch wiki files directly. When R1 or R2 finds something new, it composes a **declarative intent** in plain language ("here's a finding, here's the source, here's what it relates to") and hands it to the librarian. The librarian reads its Manual of Style (`wiki/conventions.md`) and the wiki map (`wiki/index.md`), decides where the new claim belongs, and executes the writes.

Over sessions, the wiki becomes a synthesised, topic-organised view of the company. Not a 90-entry append log of findings — a **map of what is known and where the open questions are**.

When the librarian notices a contradiction between a new finding and existing wiki content, it preserves both claims with their sources (the "Conflicting claims" pattern) and flags it in `wiki/log.md`. When three flags accumulate, the main agent spawns a **Lint Agent** that reconciles them — superseding, scoping, or preserving depending on the case. The wiki stays internally consistent without human intervention.

This is Karpathy's LLM Wiki pattern adapted for equity research. The main agent remains stateless. The research agent's context stays bounded (it never holds raw wiki content). The wiki carries the memory. The librarian carries the taste — in the file, not the agent.

---

## Why it works (and when it doesn't)

It works because the main agent is never tempted to be clever. It cannot reflect, summarise, or synthesise. Every thought it might have is outsourced to a sub-agent that dies before it can infect the main context. The loop runs until the human stops it.

It breaks when you let the main agent read things. If you ask it "what did you find?" it will read the wiki, bloat its context, and die inside six iterations. The discipline in `program.md` is load-bearing. Respect it.

It also breaks when your primary sources are thin. The research agents are only as good as what they can grep. Dump transcripts and filings into `data/` before you start. The more, the better.

---

## Philosophy

> *Every company is a story the market tells itself. In the short run, the market is a voting machine — it prices stories, sentiment, and momentum. In the long run, it is a weighing machine — it prices cash flows, assets, and truth. Your job is to find where the story diverges from the weight.*

That's the opening of `soul.md`. Read the rest there.

---

## Credit

Stateless-loop framing borrowed from [Andrej Karpathy's autoresearch](https://github.com/karpathy/autoresearch). Wiki-as-memory pattern adapted from [Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). This repo stitches them together for equity research.

---

## License

MIT. Do whatever you want with it. Attribution appreciated but not required.
