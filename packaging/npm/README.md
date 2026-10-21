# humona

**Human-inspired memory for AI agents.** Markdown notes in a git repository you own — no
database, no service, no inference to remember.

```bash
npm install -g humona
humona doctor
```

The engine is a single standard-library Python file, so this package needs **Python 3.8+** on
PATH and nothing else. It carries the engine and everything it needs; the Node wrapper only
chooses an interpreter and hands over your arguments.

## Setting it up

Installing the package puts `humona` on your PATH. Wiring it into Claude Code — the hooks, the
skills and the always-loaded rules — is a separate, explicit step, because it writes to
`~/.claude`:

```bash
humona update
```

Then restart Claude Code and run `humona doctor`; every check must say `OK`.

## If you use Claude Code

The plugin is the shorter path, and it updates the way every other plugin does:

```
/plugin marketplace add mesutcandemir39/humona
/plugin install humona@humona
```

## Upgrading

```bash
npm install -g humona@latest
```

Your notes are never touched by an upgrade: the vault lives in `~/humona/vault`, deliberately
outside the code.

Full documentation, the measured benchmarks and the SWOT:
<https://github.com/mesutcandemir39/humona>

MIT
