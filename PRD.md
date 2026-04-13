# PRD: LLM Wiki Memory Substrate for Autonomous DCF Research

**Version:** 1.0  
**Author:** Vinny Nguyen  
**Branch:** `testing-llm-wiki` → merge to `main`

---

## Problem

The original template had a flat `notes.md` file as the research agent's only persistent memory. After ~20 sessions, notes.md became an unstructured append log — thousands of lines, no organization, no cross-references, no contradiction handling. The research agent couldn't efficiently query its own prior work, so it repeated angles, missed connections between findings, and produced redundant DCF commentary that bloated `dcf.py` parameter comments.

The main agent remained stateless (by design), but the research agent's "memory" was a junk drawer.

---

## Solution

Replace `notes.md` with an **LLM Wiki** — a structured, topic-organized knowledge base maintained by a dedicated **Librarian** sub-sub-agent. Adapted from [Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) for equity research.

### Key design decisions

1. **Separation of truth and structure.** The Research Agent owns truth (what was found, from which source). The Librarian owns form (where it lives, how it connects, how contradictions are structured). Neither crosses the boundary.

2. **The Librarian is a smart curator, not a passive archivist.** It has editorial authority over taxonomy, placement, cross-referencing, and supersession handling. It has absolute neutrality over quantified facts. This mirrors how good Wikipedia editors work.

3. **Taste persists in files, not agents.** The Librarian dies after every call. But `wiki/conventions.md` (its Manual of Style) carries forward every taxonomy decision it made. New Librarians read it on spawn and inherit the accumulated judgment. Persistence lives in artifacts, not in memory.

4. **Grep-first navigation.** The Librarian never reads the whole wiki. It reads `conventions.md` + `index.md` on spawn, then greps for key terms to find candidate pages. Individual pages are capped at 500w soft / 1000w hard. This keeps librarian context bounded.

5. **Contradictions are structured, not resolved.** When two sources disagree, the Librarian preserves both claims with provenance and flags it in `wiki/log.md`. After 3 flags accumulate, the main agent spawns a **Lint Agent** to reconcile. The wiki stays internally consistent without human intervention.

6. **Research Agent never touches wiki directly.** It composes a declarative intent in plain language and hands it to the Librarian. This prevents the research agent from bloating its own context with raw wiki content.

7. **dcf.py comment cap at 80 characters.** Rationale and narrative now live in `wiki/drivers/`, not in parameter comments. This keeps dcf.py scannable and prevents comment bloat.

8. **Price blindness.** No agent searches for, cites, or anchors to share price, analyst targets, or margin of safety. Intrinsic value is computed from business fundamentals only. This was added to `main` but is reinforced in the wiki architecture — no wiki page should contain market price data.

---

## Architecture

```
MAIN AGENT (Opus — stateless)
  reads: program.md, tail -20 results.tsv
  spawns: Research Agent → Modeler Agent → (rarely) Lint Agent
  receives: 1 sentence from each

RESEARCH AGENT (Sonnet — soul.md)
  1. spawns Librarian (QUERY mode) → gets compressed wiki answer
  2. reads primary sources in data/ via grep-first
  3. composes declarative write intent
  4. spawns Librarian (WRITE mode) → wiki updated
  5. writes finding.md (ephemeral handoff)
  6. returns 1 sentence to main

LIBRARIAN (Sonnet — soul_librarian.md)
  reads first: wiki/conventions.md, wiki/index.md
  QUERY mode: grep → read candidates → return compressed answer
  WRITE mode: parse intent → place/update/create pages → wire cross-refs
             → structure contradictions → update index → append log
  dies after returning

MODELER AGENT (Sonnet — soul.md)
  1. spawns Librarian (QUERY) for driver history
  2. reads finding.md + dcf.py
  3. edits parameters (80-char cap, REPLACE not APPEND)
  4. runs python3 dcf.py --json
  5. appends results.tsv
  6. returns 1 sentence to main

LINT AGENT (Sonnet — rare, contradiction-triggered)
  reconciles flagged contradictions, merges duplicates, splits bloat
```

---

## What changed (branch diff summary)

| Change | Files | Impact |
|--------|-------|--------|
| New wiki directory structure | `wiki/{index,conventions,log}.md`, `wiki/{segments,drivers,risks,people,themes}/.gitkeep` | Durable memory substrate replaces flat notes.md |
| Librarian soul | `soul_librarian.md` (new, 102 lines) | Distinct identity for the curator agent |
| Program.md rewrite | `program.md` (+506/-97 lines) | Full architecture docs, librarian instructions, lint rules, context discipline |
| dcf.py comment cap | `dcf.py` (2-line comment change) | 80-char cap, rationale → wiki/drivers/ |
| notes.md removed | `notes.md` deleted | Replaced by wiki/ |
| Gitignore | `.gitignore` (+2 lines) | Added .ruff_cache/, .mypy_cache/ |
| README update | `README.md` (partial) | Architecture diagrams, wiki explanation |

---

## Wiki directory structure

```
wiki/
├── conventions.md    ← Manual of Style (librarian reads FIRST)
├── index.md          ← Page catalog (one-liner per page)
├── log.md            ← Append-only operations log
├── segments/         ← One page per business segment
├── drivers/          ← One page per DCF value driver
├── risks/            ← One page per identified risk
├── people/           ← One page per key executive
└── themes/           ← Cross-cutting themes
```

All pages are markdown. Capped at 500w soft / 1000w hard. Librarian splits when exceeded.

---

## Success criteria

1. **Session count before context death:** ≥50 sessions without main agent context overflow (vs ~30 with notes.md).
2. **Angle repetition rate:** <10% of sessions repeat a previously covered angle (measurable from results.tsv).
3. **Wiki coherence:** after 30 sessions, a human can browse `wiki/` and understand the company's segments, drivers, risks, and key people without reading any transcripts.
4. **Contradiction handling:** flagged contradictions are resolved within 10 sessions of being flagged (via lint agent).
5. **dcf.py cleanliness:** no parameter comment exceeds 80 characters; all rationale traceable to wiki/drivers/ pages.

---

## Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| Librarian hallucinating facts not in the research intent | soul_librarian.md explicitly forbids supplying facts the researcher didn't provide; anti-pattern list enforced |
| Wiki bloat overwhelming librarian context | Grep-first navigation + 1000w hard cap per page + lint agent for merging duplicates |
| Conventions.md growing unbounded | Append-only with supersession markers; lint agent can consolidate |
| Research agent reading wiki directly (bypassing librarian) | program.md explicitly forbids it; research agent instructions don't include wiki read tools |

---

## Prior art

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — stateless loop pattern
- [Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — wiki-as-memory pattern
- Wikipedia Manual of Style — persistence-of-taste through conventions files
