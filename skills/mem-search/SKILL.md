---
name: mem-search
description: Search past sessions, decisions and fixes in humona's memory; also timeline reports of what happened.
---
# mem-search
Progressive recall — stop at the cheapest layer that answers:
1. `humona search "<query in English>" -k 5` → index with 1-line snippets (hybrid keyword + semantic). Add `-t semantic|episodic|procedural|short-term|knowledge` to narrow, `--all` to include Archive.
2. `humona timeline -n 10` (or `--all`) → chronological one-liners of episodes/decisions.
3. `humona recall <path>` → full note, only for the 1-3 hits you actually need (bumps recall strength).

Timeline report (when asked "what did we do…"): run `humona timeline -n 20 [--all]`, recall only ambiguous items, answer as a short dated list grouped by project. Cite note paths.
If nothing found, say so — don't guess.
