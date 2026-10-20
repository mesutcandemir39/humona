# Roadmap — what goes in before this is published, and what stays out

Written 2026-10-21, after measuring this engine against the three systems worth comparing to
([Zep/Graphiti](https://arxiv.org/abs/2501.13956), [Letta MemFS](https://docs.letta.com/concepts/memfs),
[claude-mem](https://github.com/thedotmack/claude-mem)) and installing the last one to see what it
actually does. Every gap below is something observed, not imagined, and every item says how it will
be checked.

## Where we actually stand

| | this engine | claude-mem v15 (measured on 2026-10-21) |
|---|---|---|
| installed size | **1.3 MB, 118 files** | **1.6 GB, 10,284 files** |
| storage | Markdown notes + git | SQLite (20+ tables, WAL) + Chroma vectors |
| runtime | nothing resident | Bun worker on `127.0.0.1:37701`, uv, tree-sitter CLI, Node 20+ |
| writing a memory | no model call | an LLM compresses observations (`--provider claude\|codex\|gemini\|openrouter\|host`) |
| reading memory without the tool | open the file | query the database |
| harnesses | Claude Code | Claude Code, Codex, Cursor, Gemini, OpenClaw, Copilot, OpenCode… |
| extras | Obsidian graph | web viewer, MCP tools, team sync, evals, Docker, optional cloud (cmem.ai) |
| licence · stars | MIT · — | Apache-2.0 · ~102k |

Read that table honestly: **claude-mem does more than we do.** It captures everything passively,
compresses it with a model, serves it over an API, and supports seven harnesses. It costs 1,200×
the disk, a resident worker, a model bill per session, and memory you reach through its database.
We are the other trade — nothing resident, no model needed to remember, and notes a human can read
in ten years. Neither is "better"; they are different products, and ours is only worth publishing
if it is honest about which one the reader wants.

## Gaps found by inspection and testing

Fixed today, both were real bugs:

- ~~`humona recall <exact file name>` answered with a *different* note~~ — a bare file name was not
  looked up inside the layer folders, so it fell through to ranked search and returned the best
  scoring other note, silently. `--into` had the same path, which would have appended text to the
  wrong note. Exact resolution now comes first, a ranked answer says it is a guess, and `--into`
  refuses one. *(4 tests)*
- ~~A new frontmatter field read as empty forever~~ — the ranking cache keys entries by mtime+size,
  so adding `valid_until` to the cached metadata did not invalidate anything. The cache now stores
  its field list and rebuilds when it changes. *(1 test)*

Closed on 2026-10-21, in the same pass:

1. **Episode summaries can be written by a model** — `humona llm episodes-on` sends the session
   trace to the configured provider and stores a one-to-three sentence summary; off by default,
   so remembering still costs no inference, and any failure falls back to the heuristic digest.
   *(3 tests, including a provider that answers with the wrong shape.)*
2. **A shared vault for a team** — `humona shared <dir>` adds a second vault whose long-term notes
   are searched and injected with a `shared/` prefix. It is read-only by construction: no recall
   counter is written into it, `--into`/`--supersedes` refuse it, and `doctor --fix`, `lint` and
   `index` never walk it. *(5 tests.)*
3. **MCP over stdio, launched on demand** — `humona mcp` speaks JSON-RPC with `search`, `recall`,
   `facts` and `remember`, for editors that have no hooks. Not registered anywhere by default,
   because a registered server's tool definitions cost tokens in every request. *(4 tests.)*
4. **The embedding layer is measured** — `tools/bench.py --semantic` prints a second accuracy
   block. It moves exactly the row it should: blind-question hit@1 0.30 → 0.45 on a 150-note vault.
5. **`humona upgrade --verify-tags`** refuses unless the newest upstream tag carries a good GPG
   signature, plus `--check` to report without changing anything. Off until the project signs its
   tags; `--no-verify-tags` wins over the config, so the opt-out is real.
6. **`valid_from`** now behaves like `valid_until`'s mirror: a note that becomes true later is not
   injected yet and `humona lint` lists it under *not yet valid*.
7. **`docs/engine-map.md`** is generated from the file's own section markers by
   `tools/engine_map.py`, and a test fails when it drifts — which it did, immediately, when the
   MCP section landed.
8. **The install is tested on three operating systems** — a separate CI job runs
   `setup/install.py` on ubuntu, macOS and Windows runners, then requires `humona doctor` to pass
   with no FAIL and a written note to be findable. The unit suite still skips the installer on
   Windows, because there it edits the user PATH.

Plus two bugs and one bias found while doing the above:

- **Every script is searchable now.** The tokeniser folded six Turkish letters by hand and dropped
  everything else: `Ärzte` became `rzte`, `straße` became `stra`, and Cyrillic, Greek, Hebrew,
  Arabic and CJK produced **no tokens at all** — a note in those scripts was invisible to search
  and to ranking. Folding is now Unicode (NFKD, marks stripped, Hangul recomposed) and scripts
  written without spaces are indexed as character bigrams. File names keep their script instead of
  collapsing to `note`, `note-2`, `note-3`.
- **The stopword list carried a second copy of itself in Turkish**, so auto-recall worked better
  for one language than for every other. The gate is now document frequency — a term in 40% of
  the vault carries no signal in any language — with an English list only as the floor for a vault
  too small for frequencies to mean anything. The four Turkish suffixes left the stemmer with it.
- **The vault is kept in one language and lint now says so.** Three long-term notes were in
  Turkish; they are rewritten in English (quoted German phrases stay, because they are content),
  renamed, and their inbound wikilinks updated. A `not in English` lint section and a test over
  the source tree keep it from coming back.

Still open:

- **Per-language stemming** is deliberately not attempted. `fold()` plus truncation carries every
  script; a suffix table per language is a dependency in disguise.
- **Verbatim captured prompts stay in the language they were typed in.** A record is evidence, not
  prose to translate, and short-term notes decay anyway.

## The 100k-user checklist, answered honestly

A local, serverless tool does not need everything a hosted service needs, and pretending otherwise
is how a checklist becomes theatre. Three columns: what applies and is done, what applies and is
open, and what does not apply here and why.

**Done**

| Requirement | How it is met |
|---|---|
| Remote update | `humona upgrade`: fetch → diff → optional GPG tag check → fast-forward only → test suite → install → health check. Plugin users get updates through Claude Code itself. |
| Rollback | A failing health check resets the engine to the previous commit and re-installs. Tested by publishing a broken release to a fake upstream. |
| Kill switch | `release.json` `yanked[]`, read from upstream *before* anything is applied. One `git show`, no server. |
| Anti-rollback / minimum version | `min_supported` in the same manifest; the vault schema guard stops an old engine writing a new vault. |
| Atomic install | Fast-forward only, never a merge; a dirty checkout blocks it. Note files are written through a temp file and `os.replace`. |
| Backup and restore | `humona backup` / `--restore`, plus the vault's own git history. Restore refuses to overwrite notes. |
| Schema versioning and migration | `SCHEMA` + `memory/.brain-schema.json` + `humona migrate`. Documented in VERSIONING.md. |
| Supply chain | Zero runtime dependencies — there is no dependency tree to scan, no lockfile to pin, no transitive package to be compromised. The whole runtime is one file of standard-library Python. |
| Secret scanning | `humona doctor` scans synced notes; the sensory trace is redacted before it is written. CI runs the suite on three operating systems. |
| Privacy and user control | Everything is local; a fresh vault has no remote. `humona report`, `humona forget`, `humona backup`, `--private`, `humona pause`, `<private>…</private>`. No telemetry, no account. |
| Diagnostics without PII | `humona doctor` and `humona report` describe the install and what is stored, never note contents. |
| Versioning policy | SemVer, channels, support window, deprecation window — VERSIONING.md. |
| Threat model | SECURITY.md: hooks, path confinement, the two git repositories, memory as data rather than instructions. |

**Open, and ordered**

1. **Signed tags in practice.** `--verify-tags` exists; the project does not sign yet. Needs a key,
   a published fingerprint, and the release checklist to use `git tag -s`.
   → *verify:* a release tag verifies with `git verify-tag` on a machine that only has the
   published public key.
2. **Staged rollout.** Everyone who runs `humona upgrade` gets the same version at once. A `rollout`
   field in `release.json` (percentage plus a stable hash of the machine id) would hold a new
   version back from most users for a day.
   → *verify:* with `rollout: 10`, nine of ten simulated machine ids are told to wait.
3. **Provenance / SBOM.** There is nothing to build, but publishing a checksum of the exported tree
   and a GitHub attestation would let someone verify the copy they cloned.
   → *verify:* `gh attestation verify` passes against a release artefact.
4. **A real load test of one vault at scale.** Simulated to ~20k notes; what is missing is a
   sustained multi-session run on one machine with the hooks firing.
   → *verify:* bench numbers at 20k notes stay inside the hook budget.

**Not applicable, and why**

| Requirement | Why not |
|---|---|
| Rate limiting, quotas, backpressure, queues | No server. Every call runs locally, in the user's own process, against their own disk. |
| Multi-tenant isolation | One vault per person. There is no shared store that could leak between users. |
| `/health`, `/ready`, metrics, OpenTelemetry | Nothing runs between sessions. `humona doctor` is the health check, and it runs on demand. |
| Database connection pools, replicas, migrations at scale | Markdown files and git. The migration path is the vault schema above. |
| Encryption at rest and key management | The vault sits in the user's filesystem; disk encryption is the operating system's job, and a remote is theirs to choose. Nothing is transmitted by default. |
| Telemetry defaults and data-retention policy | There is no telemetry. Retention is `humona report` and `humona forget`, both local. |
| GDPR data-subject requests | No personal data ever leaves the user's machine; there is no controller to make a request to. |

## Before the repository goes public

- [x] README rewritten around measured numbers with the command that reproduces each one
- [x] `AGENTS.md` so an agent can install it without improvising
- [x] code and vault separated, so a user's notes can never be pushed to the code's remote
- [x] `humona upgrade` for later versions
- [x] `tools/bench.py` with a naive-grep and a full-replay baseline
- [x] `SECURITY.md` — what to report privately, and what the threat model is (hooks run on every
      prompt; a vault may hold private notes)
- [x] issue and PR templates, and a `good first issue` or two from the list above
- [x] CI runs the install on all three operating systems, then requires `doctor` to pass
- [ ] a tagged `v2.12.0` release so `humona upgrade` has something to pin to
- [ ] decide the public name (`claude-memory`) and create the repository — **the author's call,
      not the agent's**

## Why someone would choose this

Not adjectives — each line is a thing the alternatives cannot do, or a cost they impose.

1. **Your memory is a folder of Markdown files in your own git repository.** No database to
   migrate, no service to keep alive, no export feature needed; `cat` and `grep` work on it, and
   so does Obsidian's graph view.
2. **Remembering costs no inference.** Writing a note is a file write. Every alternative spends a
   model call per message or per session to decide what to keep.
3. **Nothing is resident and nothing is uploaded.** No worker, no port, no vector service, no
   account. A new vault has a local git history and no remote at all.
4. **A session start costs ~480 tokens against a 300-note vault, 95× cheaper than replaying it**,
   and you can re-measure that in 30 seconds offline.
5. **It is auditable.** 3,225 lines of standard-library Python, 89 tests, and a `doctor` that
   names the command repairing each failing check.
6. **It refuses to guess where guessing corrupts.** `--into` will not write through a fuzzy match,
   `humona task done` will not close without `--verify`, deletion is explicit and user-only, and a
   contradicted note is superseded rather than erased.
7. **It expires facts instead of rotting.** `valid_until` takes a fact out of the injected context
   on the date it stops being true, and `humona lint` lists it for superseding.

## The workflow layer (it is not only storage)

Worth stating plainly, because "memory system" undersells it:

- **Session lifecycle** — `SessionStart` injects the project's card, working memory, open tasks,
  the long-term notes that matter and the last episodes; `UserPromptSubmit` adds auto-recall for
  the current prompt; `PostToolUse` keeps a redacted sensory trace; `PreCompact`/`SessionEnd`
  consolidate, index and sync. A killed session is recovered by `humona catchup` from Claude Code's
  own logs.
- **Work tracking** — `humona task start|block|done --verify` (a task cannot close without saying
  how it was checked), `humona working -` for the current goal with `step -> verify: check` per
  step, and `humona board` as a kanban across every project.
- **Routing** — `humona whose "<request>"` and the `<humona-project-guess>` block, so a request
  reaches the right project's memory instead of the one that happens to be open.
- **Knowledge hygiene** — `humona lint` (broken links, orphans, stale, expired, duplicates,
  superseded-but-linked), `humona index` (the root catalog plus a `MEMORY.md` per layer),
  `humona promote`, `humona archive`, `humona forget`.
- **Skills** — `mem-search`, `smart-explore`, `learn-codebase`, `make-plan`, `knowledge-agent`:
  the repeatable procedures that use the memory rather than just reading it.
- **Rules** — the always-loaded block that tells the model when to write memory, plus the coding
  rules folded in from karpathy-guidelines (think first, minimum code, surgical edits, every task
  a verifiable goal).

## What stays out, and why

- **A transcript database.** Measured at our scale: Markdown + git beats SQLite until well past
  20k notes, and a lossless store of every message grows to a gigabyte and rots.
- **A permanently registered MCP server.** Tool definitions cost tokens in *every* request; a CLI
  costs nothing until it is called.
- **A knowledge graph with per-message LLM extraction.** The accuracy is real and so is the bill;
  we take the bi-temporal idea (supersede, expire) without the infrastructure.
- **Background agents that rewrite memory on their own.** Consolidation is deterministic and runs
  at session end for free. If judgement is ever needed there, it goes behind the optional provider.
- **A published LoCoMo or LongMemEval score.** Explained in the README: the datasets no longer
  separate a memory system from a long context window, and the numbers are mostly vendors scoring
  themselves.
