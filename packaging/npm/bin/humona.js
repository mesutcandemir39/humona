#!/usr/bin/env node
// humona 0.0.1 — the name, registered ahead of the packaged release. The engine is Python and
// installs from its repository; a wrapper that pretended otherwise would just fail later.
const REPO = "https://github.com/mesutcandemir39/humona";

process.stdout.write(`humona 0.0.1 — the name, not the engine yet.

The working engine is installed from its repository:

  As a Claude Code plugin
    /plugin marketplace add mesutcandemir39/humona
    /plugin install humona@humona

  Standalone (needs Python 3.8+)
    git clone ${REPO}.git ~/humona-src
    python3 ~/humona-src/setup/install.py

Watch ${REPO} for the packaged release.
`);
