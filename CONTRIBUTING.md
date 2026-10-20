# Contributing

The engine is one file with no dependencies, because it runs as a Claude Code hook on every prompt
and must start in ~0.1 s. Patches that keep that property are easy to accept.

## Before a pull request
1. `python3 tests/test_humona.py` — 52 stdlib tests, no network, each in a throwaway vault. Add one
   for whatever you change; every bug fixed so far has a regression test named after it.
2. `humona doctor` — 24 checks on the installation.
3. `humona lint` — the knowledge graph of your own vault, if you use one.

CI runs the same suite on Ubuntu, macOS and Windows against Python 3.9 and 3.12.

## Ground rules
- **Standard library only** in `engine/humona.py`, Python 3.8+, Windows included.
- **A hook must never block a session.** Subprocesses get timeouts and their own process group;
  stdin is polled, not blocked on. If your change can hang, it is wrong.
- **Paths from the model are untrusted.** Everything goes through `inside()` or `mt_path()`.
- **Never delete a note.** Supersede (`--supersedes`) or archive; history stays.
- **Measure before optimising.** The performance claims in the README are reproducible; if you
  change a hot path, post the numbers.
- Anything persisted is English. Notes are short, single-topic and `[[wikilinked]]`.

## Where things live
`engine/humona.py` (CLI + hooks), `engine/embed.py` (optional semantic daemon), `setup/install.py`
(machine setup), `setup/CLAUDE.md` (the always-loaded user rules), `tests/`, `skills/`.
See `CLAUDE.md` for the same summary aimed at an agent.
