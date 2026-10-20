---
name: smart-explore
description: Explore code structure and trace code paths/flows without reading whole files.
---
# smart-explore
Token rule: structure first, full reads last.
1. Known project? Read `memory/projects/<p>/map.md` Notes and `humona search "<topic>"` first.
2. `humona outline <dir> --max 30` → top-level symbols per file with line numbers.
3. `humona outline <file>` → every symbol + line; then `Read` with `offset`/`limit` around the lines you need — never the whole file unless small (<200 lines).
4. Trace a flow (pathfinder): `humona refs <symbol>` → DEF then USE sites (file:line). Follow the chain symbol by symbol (entry point → handler → service → data), outlining each hop.
5. Write the discovered path as one line in map Notes: `path:line → path:line — what flows` so it's never re-traced.
