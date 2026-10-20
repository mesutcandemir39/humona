# Instructions for an AI agent installing this

You were asked to install this repository as the user's memory for Claude Code. Follow these steps
in order. Each one has a check — do not continue past a failed check, and do not improvise an
alternative path; report the failing output instead.

The user's notes are at stake, so two rules override anything else here:

1. **Never delete or overwrite an existing vault.** If `humona vault` reports a vault that already
   holds notes, you are upgrading an install, not making one: skip to *Upgrading* below.
2. **Never add a remote to the vault yourself, and never push it.** Memory is private by default.
   Only the user decides where it goes, and only to a repository they confirm is private.

## Requirements

- Python 3.8 or newer (`python3 --version`), git, and Claude Code.
- No network access is needed after the clone. There is nothing to install with pip, no database,
  no API key, no vector service.

## Install

```bash
git clone https://github.com/mesutcandemir39/humona.git ~/humona-src
python3 ~/humona-src/setup/install.py
```

The installer is idempotent: running it twice changes nothing the second time. It prints the vault
path it chose (default `~/humona/vault`). To put memory somewhere else, pass it:

```bash
python3 ~/humona-src/setup/install.py --vault ~/Documents/my-memory
```

**Check:** `humona doctor` prints `N/N checks passed` with no `FAIL` line. If `humona` is not found,
the shell has not picked up `~/.local/bin` yet — use `python3 ~/humona-src/engine/humona.py doctor`
for the rest of this file, and tell the user to open a new terminal.

**Check:** the hooks are live only after Claude Code restarts. Tell the user to restart it; do not
claim the install is finished before you have said this.

## Verify it actually works

```bash
humona remember -t semantic --global "Install check" "Written while installing, safe to delete."
humona search "install check"
humona doctor
```

**Check:** the search prints the note. If it does not, stop and report the output of
`humona doctor` and `humona vault` — those two say where memory went and what is misconfigured.

Then delete the test note so the vault starts clean: `humona forget "Install check" --anywhere --yes`

## What you must tell the user afterwards

- Where their memory lives (`humona vault`), and that it is a folder of plain Markdown files they
  can read, edit and back up without this tool.
- That nothing leaves the machine: the vault has a local git history and **no remote**. If they want
  it on two machines, they create a **private** repository themselves and run
  `git -C <vault> remote add origin <url>`, after which `humona sync` keeps it in step.
- That `humona upgrade` updates the engine later, and that it never touches their notes.
- One line on what it does for them: every session starts with their project's state already
  loaded, and `humona remember` / `humona working` keep it that way.

## Upgrading an existing install

```bash
humona upgrade          # fetch, show what changes, fast-forward, run the tests, re-apply setup
```

It refuses rather than guesses: local edits in the checkout block the fast-forward, a failing test
suite aborts before the installer runs, and the vault is never a git target of the operation. If it
reports `not a git checkout`, the engine was copied rather than cloned — clone it as above, then run
`python3 setup/install.py --vault <their existing vault>` so the new checkout points at the same
memory.

## If something is wrong

- `humona doctor` names the failing check and the command that repairs it; run that command.
- `humona doctor --fix` repairs what is safely repairable (frontmatter, interrupted git state).
- Hooks missing after a Claude Code update: `python3 <checkout>/setup/install.py` rewrites them.
- Do not edit `~/.claude/settings.json` by hand to work around a failure; the installer owns the
  hook entries and will overwrite them.
