# humona

**Human-inspired memory for AI agents.** Markdown notes in a git repository you own — no
database, no service, no inference to remember.

This PyPI release is **0.0.1: the name, registered ahead of the packaged release.** The engine
itself is complete, tested on macOS, Linux and Windows, and in daily use — but it is installed
from its repository, because a pip install cannot yet carry the hooks, skills and installer
that make it work.

## Install the working engine

As a Claude Code plugin:

```
/plugin marketplace add mesutcandemir39/humona
/plugin install humona@humona
```

Standalone:

```bash
git clone https://github.com/mesutcandemir39/humona.git ~/humona-src
python3 ~/humona-src/setup/install.py
```

Everything — the measurements, the architecture, the SWOT and the comparison with other memory
systems — is at **https://github.com/mesutcandemir39/humona**.

MIT licensed.
