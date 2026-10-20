# Changelog

## 3.0.0 — 2026-10-21 — **humona**
The project has a name. `brain` was a description; **humona** — human + memory — is a name the
product can carry, with a logo and an identity of its own. MAJOR because the command changed, even
though nothing you already have stops working.

**Renamed**
- The command is **`humona`**. `brain` stays installed as an alias, so every habit and every script
  keeps working.
- `engine/brain.py` → `engine/humona.py`, `tests/test_brain.py` → `tests/test_humona.py`.
- Environment variables are `HUMONA_*` (`HUMONA_VAULT`, `HUMONA_STATE`, `HUMONA_SHARED`,
  `HUMONA_LLM_*`, …). The `BRAIN_*` names are still read, through one `envvar()` helper.
- The injected elements are `<humona-memory>`, `<humona-recall>`, `<humona-tasks>` and the rest;
  a note still cannot close either prefix.
- Machine-local state moves to `…/humona`, and an existing `…/brain` directory keeps being used —
  renaming it would strand the config that records where the vault is.
- The vault marker is `.humona-schema.json`; the old `.brain-schema.json` is read once and then
  superseded.
- The rules block in `~/.claude/CLAUDE.md` is delimited by `<!-- humona:start -->`; the installer
  replaces a pre-3.0 `brain:` block rather than leaving two.
- Default vault for a fresh install: `~/humona/vault` (workspace `~/humona`).
- Package name `humona` on PyPI, plugin and marketplace named `humona`, repository
  `mesutcandemir39/humona`.

**Added**
- A logo: `docs/logo.svg`, minimal, a green eye with remembered facts drifting into the pupil.
  `tools/make_icons.py` renders the listing PNG from the same geometry, so the two cannot drift.
- `TestBackwardCompatibility`: the old environment names still drive the engine, a vault stamped
  with the old marker is read and restamped, and a note cannot close either element prefix.

**Unchanged**
- Your notes. The vault layout is schema 1 either way; nothing is migrated, moved or rewritten.

## 2.15.0 — 2026-10-21
Everything needed to hand this to strangers: it installs as a Claude Code plugin, it cannot lose
memory across versions, and a bad release cannot reach everyone.

- **It is a Claude Code plugin.** `/plugin install brain --marketplace mesutcandemir39/claude-memory`
  installs the hooks, the five skills, the `brain` command (through the plugin's `bin/`) and the
  MCP server as one unit, with no setup step — Claude Code reports the footprint as ~139 tokens
  always-on. `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `hooks/hooks.json`,
  `.mcp.json`, `bin/brain`, and an icon; `claude plugin validate` passes.
  - A plugin's cache directory changes with every version, so the vault defaults to `~/claude/brain`
    and never to the checkout when running as a plugin — the one way an update could have taken
    memory with it.
  - First plugin run creates the vault silently (a hook's stdout is parsed as JSON) and carries a
    compact rules block, because Claude Code does not load a plugin's `CLAUDE.md`.
- **Vault schema versioning.** `memory/.brain-schema.json` records the layout; an engine **refuses
  to write** a vault written by a newer engine, and still reads it. `brain migrate [--dry-run]`
  moves a vault forward. Rolling code back no longer risks the data.
- **`brain backup` / `--restore`.** One tar.gz of the whole vault, restored by any machine with
  `tar`; a restore over a vault that holds notes is refused unless `--force`.
- **A bad release stops itself.** `brain upgrade` now reads `release.json` from upstream before it
  applies anything (a **yanked** version is refused with the maintainer's note), and runs the
  health check *after* install — **resetting the engine back to the previous commit if it fails**.
  Verified by tests that publish a broken release to a fake upstream and watch the rollback.
- **`brain code`** — ranked pointers into a repository (`path:line` plus the matching line) using
  the vault's own ranking and tokeniser, so it works in any language. `-t code|docs|all`, git-aware
  file selection, nothing stored, ~0.5 s on this repo.
- **CJK and Cyrillic retrieval measured, not assumed**: `tools/bench.py --languages` scores
  Japanese, Chinese, Korean and Russian at **hit@1 1.00** on 40 near-identical notes each.
- **README rebuilt** around three GIFs rendered from real runs (`tools/demo_gifs.py`), an honest
  SWOT, the plugin install line, an answer to "do I need Obsidian?" (no, and how to use it anyway),
  and a table of surfaces beyond Claude Code.
- **`VERSIONING.md`** — SemVer rules and what counts as breaking, the vault schema, release
  channels, `release.json` (yank list, `min_supported`), the support window, and a release
  checklist. **`CODE_OF_CONDUCT.md`** added.
- 113 tests (was 104), 27 doctor checks.

## 2.14.0 — 2026-10-21
Every open item on the roadmap, plus what fixing them uncovered.

- **Search works in every language it is given.** The tokeniser folded six Turkish letters from a
  hand-written table and threw the rest away: `Ärzte` indexed as `rzte`, `straße` as `stra`, and
  Cyrillic, Greek, Hebrew, Arabic and CJK produced **no tokens at all**, so a note in those scripts
  was invisible to search and to ranking. Folding is now Unicode — NFKD, combining marks stripped,
  Hangul recomposed because NFKD splits it into jamo — and scripts written without spaces are
  indexed as character bigrams. File names keep their script instead of collapsing to `note-2`.
- **Auto-recall no longer favours one language.** The stopword list carried a Turkish copy of
  itself; the gate is now document frequency (a term in 40% of the vault carries no topic signal
  in any language), with an English list as the floor for a vault too small for frequencies to
  mean anything. The Turkish suffixes left the stemmer with it.
- **The project is English, and a test says so.** `TestWrittenInEnglish` scans the source tree for
  foreign prose (lines marked `# i18n-data` hold foreign words as data and are exempt), `brain
  lint` gained a *not in English* section for long-term notes, and the installed rules block now
  states both halves of the rule: persist in English, reply in the user's language, keep captured
  prompts verbatim.
- **`brain llm episodes-on`** — episode summaries written by any OpenAI-compatible provider from
  the session trace. Off by default: remembering stays free, and a failure falls back to the
  heuristic digest.
- **`brain shared <dir>`** — a second, read-only vault for a team's decisions. Its long-term notes
  are searched and injected with a `shared/` prefix; no recall counter is written into it,
  `--into`/`--supersedes` refuse it, and `doctor --fix`, `lint` and `index` never walk it.
- **`brain mcp`** — MCP over stdio (`search`, `recall`, `facts`, `remember`) for harnesses without
  hooks, launched by the client and registered nowhere by default, because a registered server's
  tool definitions cost tokens in every request.
- **`brain upgrade --verify-tags`** refuses unless the newest upstream tag has a good GPG
  signature; `--check` reports without changing anything; `--no-verify-tags` overrides the config.
- **`valid_from`** mirrors `valid_until`: a note that becomes true later is not injected yet and
  lint lists it under *not yet valid*.
- **`tools/bench.py --semantic`** measures the optional embedding layer. It moves the row it
  should: blind-question hit@1 0.30 → 0.45 on 150 notes.
- **`docs/engine-map.md`**, generated from the engine's own section markers by
  `tools/engine_map.py`, with a test that fails when it drifts.
- **CI installs the engine on ubuntu, macOS and Windows** and requires `brain doctor` to pass with
  no FAIL and a written note to be findable.
- Three long-term notes written in Turkish are rewritten in English, renamed, and their inbound
  wikilinks updated (quoted German phrases stay — they are content).
- 104 tests (was 89).

## 2.13.0 — 2026-10-21
- **`brain recall <exact name>` no longer answers with a different note.** A bare file name was not
  looked up inside the layer folders, so `2026-10-20_claude_85f81a16` fell through to ranked search
  and returned the best-scoring *other* note, silently — found by Mesut asking whether memory could
  locate one session without the index. Exact resolution now runs first (`resolve_exact`), a ranked
  answer prints `(no note called … — closest match by rank:)`, and `--into` / `--supersedes` refuse
  a guess outright instead of appending text to the wrong note.
- **The ranking cache rebuilds when its field list changes.** Entries are keyed by mtime+size, so
  adding a cached frontmatter field left old shards answering `""` forever — `valid_until` was read
  as empty and expired notes kept being injected. The shard now stores `__meta_keys__`.
- **`valid_from` / `valid_until` (Zep's event timeline, without the graph).** `brain remember
  --valid-until YYYY-MM-DD` records when a fact stops being true; after that date it is no longer
  injected at session start, stays searchable and recallable, and `brain lint` lists it under
  *expired* so it gets superseded or archived. The 120-day staleness heuristic could not express an
  appointment next week or a price fixed today.
- **A `MEMORY.md` per layer** (`Semantic/`, `Episodic/`, `Procedural/`, `projects/`), written by
  `brain index` — Letta's rule that a folder without its own index is a folder nothing can enter
  cheaply. Expired notes are marked. `3-LongTerm/Core/MEMORY.md` is never touched: it is Claude
  Code's own auto-memory index.
- **The session-start block reports its budget**: `chars="2908/9500"`, so the cap is something the
  model can see rather than discover by truncation.
- **`ROADMAP.md`** — the pre-publication plan: every open gap with the check that closes it, a
  measured comparison against claude-mem v15 (1.3 MB / 118 files here vs 1.6 GB / 10,284 files
  there, measured by installing it), why someone would pick this engine, the workflow layer, and
  what stays out.
- **`SECURITY.md`**, issue and PR templates (shipped to `.github/` by `export_public.py`).
- 89 tests (was 79).

## 2.12.0 — 2026-10-20
- **Code and memory are separate repositories.** The engine checkout is public and upgradable; the
  vault is the user's own and never pushed to a remote they did not choose. `BRAIN_VAULT` → installer
  config → the checkout itself (the old single-directory layout keeps working and doctor labels it).
  New `brain vault [dir] [--move]`, `--vault` on the installer, and a doctor check that FAILS if the
  vault's remote is the code's remote — the one mistake that would publish private notes.
- **`brain upgrade`** — fetch the code remote, print the version and file diff it would apply,
  fast-forward only (never merge), run the test suite on the new code, re-apply setup, run doctor.
  Refuses on a dirty checkout, aborts before installing if a test fails, prints its own rollback
  command. Runs git in the code checkout only, asserted by a test. Deliberately not `curl | sh`.
- **A vault with no remote is a complete install.** `git init` with no origin at install time, so the
  user gets history and undo while nothing can leave the machine; doctor reports local-only as OK
  instead of demanding a remote.
- **`tools/bench.py`** — accuracy, cost, speed and usability in one offline run (~30 s, no API key),
  against a naive-grep baseline and the full-replay cost baseline, with one correct answer per
  question by construction. 300 notes: session start ≈479 tokens vs 45,436 for full replay (95×),
  hooks ~220 ms p50, hit@1 1.00 when the question names its subject, 0.25 when it only describes it.
  The README quotes it and a test keeps it honest.
- **Karpathy's coding guidelines are rules, not a skill** (rules 11–14 of the installed CLAUDE.md
  block): think before coding, minimum code, surgical edits, every task a verifiable goal.
- **`AGENTS.md`** — the install an AI agent follows, step by step, with a check after each step and
  the two rules it must not break (never overwrite a vault, never add a remote to it).
- Exit codes now reach the shell, so CI and agents can tell a failed upgrade or doctor run.
- `pyproject.toml` version had drifted three minors behind the engine; both are 2.12.0.
- 79 tests (was 71), including an install into a throwaway HOME that must pass doctor with no FAIL.

## 2.11.0 — 2026-10-20
- **Working memory carries its checks** — `WORKING_TPL`'s Next section is now
  `- <step> -> verify: <the check that proves it>`, and rule 3 of the always-loaded CLAUDE.md block says
  a step with no check is not finishable by a fresh session. The one idea worth taking from
  karpathy-guidelines; the skill itself is not installed (rules 1-3 duplicate what Claude Code and
  `brain/CLAUDE.md` already say, rule 4 is a weaker verified-or-not-done).
- **Working memory carries its checks** — `WORKING_TPL`'s Next section is now
  `- <step> -> verify: <the check that proves it>`, and rule 3 of the always-loaded CLAUDE.md block says
  a step with no check is not finishable by a fresh session. The one idea worth taking from
  karpathy-guidelines; the skill itself is not installed (rules 1-3 duplicate what Claude Code and
  `brain/CLAUDE.md` already say, rule 4 is a weaker verified-or-not-done).
- **`brain forget`** — the engine's only deletion path. Decay moves unrecalled episodes into `Archive/` and
  nothing deleted them; now `brain forget <path|title>… | --all | --older-than DAYS` does, deliberately:
  archived notes only unless `--anywhere`, inbound `[[links]]` printed before anything goes, refused without a
  terminal unless `--yes` (so neither Claude nor cron deletes on a guess), `--dry-run` to preview. The note is
  purged from `idx-*.json` and `vectors.json` too, which cache a gist of every note. Git history still holds
  the file.
- **`tools/demo_gif.py`** — renders `docs/session-start.gif` from a real hook run against a throwaway demo
  vault, so the README shows the actual session-start payload and its measured cost. Dev-only (Pillow).

## 2.10.0 — 2026-10-20
Multi-project tracking: a board, stages, and knowing which project a request belongs to.
- **`brain board`** — kanban across every project: in flight, blocked (with the reason), queued (with due
  dates), the project's current focus line and when it was last touched. Written to `memory/board.md` at
  session end and linked from `index.md`; at the workspace root a compact `<brain-board>` block rides in the
  session-start payload.
- **Task stages:** `brain task start|block|done`, `--due`, `--why`. `block` is refused without `--why`, as
  `done` is refused without `--verify`. Old `{done: bool}` task files migrate on read.
- **Interrupted sessions are marked.** When a session ends with a task in flight — including when the usage
  limit cuts it off — consolidation stamps the episode with `Interrupted while: [id] <task>`, so the next
  session resumes instead of re-deriving where it was.
- **`brain whose "<request>"`** — routes a request to a project from its notes, cards, maps, episodes and
  working memory plus the project name. When a prompt looks like another project, auto-recall emits
  `<brain-project-guess>` with that project's card and commands rather than answering from the wrong memory.
- Rules block: scope notes with `-p <project>` (that is what makes routing work); `--global` is for
  cross-project lessons only.
- 64 tests (was 58).

## 2.9.0 — 2026-10-20
Context budgeting, the agentic harness layer, and the polish an open-source reviewer looks for.
- **Injection ledger.** Every session records the notes already in its window (session start claims its own
  payload), so auto-recall never repeats itself, and a session cap of 4000 chars (~1000 tokens) stops the drip.
  Measured over 50 prompts in one session: **2661 → 533 injected tokens (−80 %)**.
- **`brain task`** — the harness checklist Anthropic measured: JSON in the vault, one feature at a time, and
  `done` is refused without `--verify "how it was checked"`. Open tasks ride in the session-start payload as
  `<brain-tasks>`, giving the fixed-order orientation the pattern calls for.
- **Fixed:** the ranking cache made note bodies lazy and the semantic half of auto-recall crashed on `None`
  (swallowed by the hook guard, so recall silently degraded). Found while measuring the ledger; now covered by
  a regression test that asserts no result ever carries a `None` body.
- `brain lint` also reports notes missing from `index.md`; Obsidian now ignores `Archive/` as well, so decayed
  episodes stop showing up as unlinked nodes in the graph.
- `pyproject.toml`: `pip install .` provides the `brain` console script, no dependencies, with an optional
  `[semantic]` extra. The public copy is published as **claude-memory**.
- 58 tests (was 52).

## 2.8.0 — 2026-10-20
Audited against a simulated three-year vault (4381 notes, 8.4 MB: 2190 sessions, 1100 long-term notes,
30 projects, two 1000-chunk corpora) and fixed what the numbers exposed.
- **Ranking cache.** Per-prompt recall took 1.39 s at three years because every message re-tokenised 1100
  notes. Term frequencies, metadata and gists are now cached per layer in the machine-local state dir, keyed by
  mtime+size, and bodies are read only for the notes actually returned. Per-prompt recall: **1.39 s → 0.25 s**,
  `search --all` 2.51 s → 0.50 s, session start 0.57 s → 0.30 s, peak RSS 27 MB. `brain reindex` rebuilds it.
- Lazy `urllib`/`difflib` imports: the startup floor every hook pays dropped 0.17 s → 0.13 s.
- `fact_rows` serves the session-start index from the cache instead of reading 1100 files (0.195 s → 0.06 s).
- `git gc --auto` runs weekly from session end, so years of commits stay packed (8.4 MB → 3.6 MB `.git`).
- `projects/new.sh` now scaffolds the harness layout Anthropic recommends: committed `CLAUDE.md`, deterministic
  `init.sh`, `.claude/`. This repo gained its own `CLAUDE.md` too.
- The installer configures Obsidian's ignore filters, so engine/setup/skills/tests/docs stay out of the graph
  view and search — only `memory/` is knowledge. Removed a stray empty `projects/brain/_card.md`.
- 52 tests (was 49): cache invalidation on an outside edit, `reindex`, and the shard that keeps ingested
  corpora out of the per-prompt path.

## 2.7.0 — 2026-10-20
The wiki layer, from selmakcby/knowledge-pipeline's INGEST/QUERY/LINT pattern, the three most-starred
Claude memory projects (coleam00/claude-memory-compiler, HelloRuru/claude-memory-engine,
obra/claude-memory-extractor, plus alexknowshtml/claude-memory-health) and Anthropic's context-engineering
and long-running-harness posts. All four of those projects converge on the same missing piece: a health pass
over the knowledge graph.
- **`brain lint`**: broken `[[links]]`, pages several notes link to but nobody wrote, orphans, stale claims,
  superseded-but-still-linked notes, empty notes, duplicate titles. Report only, `--json` available. It found
  9 orphans in this vault on the first run; they are now cross-linked with a stated reason each.
- **`brain index`**: generates `index.md`, a catalog of every note as a real `[[wikilink]]` grouped by layer,
  so Obsidian's graph and backlinks work and an agent can browse memory without searching. Refreshed at
  session end; excluded from search so it never feeds back as a hit.
- **`brain links <note>`**: outbound and inbound links (backlinks).
- **Provenance:** `brain remember --source PATH|URL` records where a claim came from; `distill` sets it to the
  episode it distilled.
- Rules block tightened: one topic per note with an explicit type decision rule (Anthropic: overlapping memory
  categories make retrieval unreliable), link new notes so they are not orphans, and episodes record how the
  result was verified (their long-running-harness lesson).
- 49 tests (was 43).

## 2.6.0 — 2026-10-20
Learned from Anthropic's memory-tool documentation, Claude Code's own memory design and mem0's plugin.
- **`brain memory-tool`**: serves Anthropic's `memory_20250818` contract (view/create/str_replace/insert/delete/
  rename) against this vault, with the documented result strings, `view_range`, 6-wide line numbers, 16 k
  truncation and 2-level listings — any Claude API app can now use the vault as its memory backend.
- **Security:** every model-chosen path is URL-decoded, resolved and confined to the vault. `brain recall
  ./secret.md` used to read a file outside the vault into context *and* write the recall counter into it;
  `/memories/../../x`, `%2e%2e%2f`, absolute paths and symlinks out are all refused now. The memory root cannot
  be deleted or renamed, and memory files are capped at 1 MB.
- `brain pause [--minutes N]` / `brain resume` for private work; `PostToolUseFailure` is captured and failures
  lead the episode trace.
- Notes unverified for 120+ days are flagged inline in the session-start index (Claude Code's freshness idea).
- `brain doctor` fails before Claude Code's silent `MEMORY.md` truncation (200 lines / 25 KB) — 24 checks.
- Session-start directive now carries Anthropic's "assume interruption" framing with our own commands.
- 43 tests (was 34): the whole memory-tool contract, six traversal attempts, pause/resume, failure capture.

## 2.5.1 — 2026-10-20
Two frontmatter bugs, both reported by GitHub refusing to render a note.
- Values are now quoted when plain YAML would misread them, so `title: Auto-recall gating: coverage…` no longer
  renders as *"mapping values are not allowed in this context"* on GitHub or in Obsidian's property pane. The
  reader unquotes on the way back, and the quoting is idempotent. `brain doctor` checks every note and
  `--fix` repairs them (3 notes in this vault).
- **Data loss fixed:** `read_note` only parses top-level scalars, so rewriting a header from the parsed dict
  deleted nested blocks — Claude Code's `metadata:\n  type: user` disappeared the first time a Core note was
  recalled (`recall_count` is written back). `write_note` now merges into the existing header and never touches
  a line it did not parse. The damaged note was restored from git history.
- 34 tests (was 30), including both regressions and a nested block surviving a recall.

## 2.5.0 — 2026-10-20
- `--json` on `context`, `search`, `facts`, `timeline`, `recall`, `stats`: one stable envelope so other agents,
  cron jobs or dashboards can read memory without parsing prose.
- Decision layer: `brain decide` (typed question + answer space → `{answer, confidence, reason}`), any
  OpenAI-compatible provider (`BRAIN_LLM_BASE_URL`/`BRAIN_LLM_MODEL`/`BRAIN_LLM_API_KEY`), strict
  `json_schema` structured outputs with a JSON-mode fallback, `brain llm status|test`.
- `brain remember --decide` resolves the dedup gate (add/update/skip) itself; `brain distill <note> [--write]`
  drafts a long-term note from an episode. Both no-ops without a provider; the agent stays the default decider.
- Documented seam for a local typed-decision model (Laya/Jev shape): `_decide_<name>` + `BRAIN_DECIDE_BACKEND`.
  Not shipped — Laya is zero-shot 0.362 vs a 0.461 majority baseline, 49 s per prediction on a CPU VPS, 2.5 GB.
- **Windows fix:** every non-ASCII `print` (`ADDED →`) crashed on a cp1252 console; stdout/stderr are now
  reconfigured to UTF-8. Found by CI, covered by a local `PYTHONIOENCODING=cp1252` test.
- `new_note()` is now shared by `remember` and `distill`, so both write identical notes.
- CI moved out of the private vault (Actions minutes are metered there): `setup/export_public.py` installs
  `setup/workflow-test.yml` into the public copy, where it runs free on Ubuntu/macOS/Windows × 3.9/3.12.
- 30 tests (was 21), including a local stub OpenAI server — no network, no key, no cost.

## 2.4.0 — 2026-10-20
- Injected context is now one XML element per memory document with markdown inside, metadata in attributes, and
  the directive after the data. Measured with `cl100k_base`: session start 549 vs 514 tokens against markdown
  headings (+6.8 %), per-prompt auto-recall 53 vs 52 (+1). Content can never close our tags.
- Test suite: 21 stdlib tests in throwaway vaults (`BRAIN_CC_PROJECTS` added for isolation) + CI on
  Ubuntu/macOS/Windows × Python 3.9/3.12.
- Fixed by those tests: the orphan-recovery digest matched raw JSONL substrings (any whitespace change would
  have silently disabled it — it now parses each line), and the auto-recall BM25 floor rejected correct matches
  in a small vault (1.0 → 0.3; the coverage/rare-word gate is the precision control).
- Typo repair compares whole words instead of 6-char stems: `sqllite databse` → `sqlite database`.
- MIT licence, `setup/export_public.py` for a memory-free public copy, generic rules block.

## 2.3.0 — 2026-10-20
Studied mikeadolan/claude-brain (SQLite + FTS5 + MCP, lossless transcript capture) and took what fits a
curated-notes vault; measured where our markdown scan stops being free: 200 notes 0.21 s, 1k 0.46 s, 5k 1.54 s, 20k 6.07 s.
- `brain catchup`: writes episodes for sessions that ended without one (terminal killed, crash) by reading
  Claude Code's own JSONL logs; runs at session end and, throttled, at session start. Bounded reads (64 KB head + 256 KB tail).
- Hook output moved to `hookSpecificOutput.additionalContext` (injected as a system reminder, capped at 9500 chars);
  manual runs still print plain text. After `compact`/`clear`/`resume` the re-injected context is 1.5× richer.
- `hook_input()` can no longer block on an inherited empty stdin (0.5 s readability check) — this had frozen `brain context`.
- Contradiction resolution: `brain remember --supersedes PATH` links new→old, old→new; superseded notes drop out of the
  index and rank at 0.3× in search instead of being deleted.
- Ranking: mild recency bias (today ~+25 %, a month ago ~+12 %); typo repair against the vault vocabulary when a search
  returns nothing; auto-recall no longer matches URLs, e-mail addresses or pasted code.
- `brain facts --stale DAYS` surfaces memory rot (never recalled since written); `brain doctor` warns above 3000 searchable notes.

## 2.2.0 — 2026-10-20
- Auto-recall: synchronous `UserPromptSubmit` hook injects up to two pointers to matching long-term notes (`<brain-recall>`); gated on word coverage / rare words / cosine ≥ 0.30, keyword+semantic, ~0.15 s, `brain autorecall on|off`.
- `brain facts`: index of every long-term note (title + gist, recall-sorted); session-start context now carries it, budget-capped (`nfacts`/`facts`).
- Session start at the workspace root lists recent work from every project; duplicate summaries are collapsed in context and `timeline`.
- One transcript digest per session, written to the project that session actually worked in; side-project episodes get a gist from their own trace.
- `~/.claude`, the workspace root and area folders are no longer phantom projects; notes created under `general` are stored as global.
- `git` can no longer hang a hook: own process group, killed as a whole on timeout, never interactive (`GIT_TERMINAL_PROMPT=0`); a pull younger than 90 s is reused. Session start measured ~1.2 s with sync.
- `projects/` grouped by life area (personal, work-germany, work-turkey, sandbox, archive) with `new.sh`.

## 2.1.0 — 2026-10-20
- `brain report`: what is remembered, what will be forgotten and when.
- Hybrid search: keyword BM25 + optional multilingual semantic layer (fastembed, machine-local venv, warm daemon ~10 ms/query, auto-fallback to keyword).
- `brain outline` (symbols + lines, ~27× fewer tokens than full reads), `brain refs` (definitions → uses).
- `brain ingest` knowledge corpora; `brain timeline`; `--kind` observation types; `<private>` prompt tags.
- Zero-token episode auto-summary from transcript (session title + last reply gist).
- Skills: mem-search, smart-explore, learn-codebase, make-plan, knowledge-agent (installed by setup, synced via repo).

## 2.0.0 — 2026-10-20
- `brain doctor/update/profile`, robust sync (rebase → merge → offline, auto-repair), sync lock, atomic writes.
- Secret redaction, `--private` notes, machine-local state outside the vault.

## 1.0.0 — 2026-10-20
- Layered memory (sensory, short-term, working, long-term), project cards + code maps, git sync, cross-platform installer.
