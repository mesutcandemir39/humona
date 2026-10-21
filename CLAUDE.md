# brain — project rules

Persistent memory for Claude Code: an Obsidian vault of markdown notes plus a stdlib-only Python
engine driven by hooks. The vault in `memory/` is the user's own memory; the code is `engine/humona.py`.

## Before changing anything
- `python3 tests/test_humona.py` — 49 stdlib tests, ~30 s, no network. Run it before every push;
  this repo has **no CI** (private repos meter Actions minutes). `setup/export_public.py` ships the
  workflow to the public copy instead.
- `humona doctor` — checks the installation (hooks, PATH, git, frontmatter, caps, secrets); every line must say `OK`.
- `humona lint` — health of the knowledge graph (broken links, orphans, stale, duplicates).

## Layout
- `engine/humona.py` — the whole CLI and every hook, one file on purpose: hooks must start fast
  (~0.13 s floor). Heavy stdlib imports (`urllib`, `difflib`) are lazy for that reason.
- `engine/embed.py` — optional semantic daemon (fastembed), machine-local venv, never required.
- `setup/install.py` — writes `~/.claude/settings.json` hooks, the CLAUDE.md rules block, skills,
  `humona` on PATH. `setup/CLAUDE.md` is the source of the always-loaded user rules — edit it there.
- `packaging/payload.py` — stages the mini-checkout both registry packages carry, because the
  engine needs a checkout around it (`CODE = parents[1]`). `packaging/pypi/build.py` and
  `packaging/npm/build.py` build from it. Never `uv build` at the root or `npm publish` in
  `packaging/npm`: both ship the code without the payload. See `packaging/README.md`.
- `tests/test_humona.py` — every test runs in a throwaway vault via `HUMONA_VAULT`/`HUMONA_STATE`/
  `BRAIN_CC_PROJECTS`, so the suite never touches real memory.
- `memory/` — the vault. Never rewrite notes by hand in bulk; use the CLI so caches stay valid.

## Rules
- Zero dependencies in `engine/humona.py`. Standard library only, Python 3.8+, Windows included
  (stdout is reconfigured to UTF-8 because a cp1252 console crashed on `ADDED →`).
- A hook must never block a session: git runs in its own process group with a timeout, and
  `hook_input()` polls stdin for readability instead of blocking on it.
- Every model-chosen path goes through `inside()`; `/memories` paths through `mt_path()`.
- Anything persisted is English. Replies to the user follow the user's language.
- Decisions that cost measurement effort belong in the vault (`humona remember`), not only in git.
