---
name: learn-codebase
description: Learn a repository deeply once and store it in humona's memory (card, map, key facts).
---
# learn-codebase
Goal: next session needs ~1-2k tokens instead of re-exploring.
1. `humona card` and `humona map` (creates/refreshes; map Notes are preserved).
2. Read README, manifest (package.json / pyproject / Cargo.toml / go.mod), CI config, entry points. Use `humona outline` for source dirs, not full reads.
3. Fill `_card.md` tersely: Purpose, Stack, Commands (build/test/run/lint), Entry points, Rules & gotchas.
4. Fill map `## Notes (Claude)`: 10-25 lines `path:line — purpose`, key flows from `humona refs`.
5. `humona remember` only non-obvious facts (conventions, pitfalls, decisions) with `--kind`.
6. `humona episode "Learned <repo>: …"`. Keep everything English and short.
