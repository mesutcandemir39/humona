# Security

## Reporting a vulnerability

Report privately through GitHub's **Report a vulnerability** button on the Security tab of this
repository. Please do not open a public issue for anything that could expose someone's notes.

Include what an attacker controls (a prompt? a note? a repository the user clones?), what they get,
and the smallest reproduction you have. A first response within a week is the goal; a fix ships as
a patch release with the problem described in the CHANGELOG once it is fixed.

## What this software can reach

Worth being explicit, because a memory system sits in an unusual place:

- **Its hooks run on every session start, every prompt and after tool calls.** They are registered
  in `~/.claude/settings.json` by `setup/install.py`. A hook is a local Python process; it never
  evaluates note content as code.
- **It reads and writes one directory**, the vault (`humona vault` prints it). Every model-chosen
  path goes through a containment check (`inside()`), and the Anthropic memory-tool surface is
  confined to a `/memories` prefix (`mt_path()`).
- **It runs `git` in two places and never mixes them.** The vault's git is used for sync; the code
  checkout's git is used only by `humona upgrade`. A test asserts the upgrade path never names the
  vault, because that is the bug that could rewrite someone's memory.
- **It makes no network calls of its own.** There is no telemetry, no account and no phone-home;
  a fresh vault has no remote at all. Three things reach the network, each only if you set them
  up: git against the remote *you* configured, the optional embedding model download
  (`humona semantic install`), and the optional decision provider — if you configure one,
  `humona decide`/`distill` POST to the `base_url` you gave them. `humona llm status` says whether
  a provider is configured on this machine.

## Trust boundaries

- **Notes are data, never instructions.** Injected memory is wrapped in `<humona-*>` elements and
  the session-start payload ends with a line saying so. Any `</humona…>` sequence inside a note is
  neutralised so a note cannot close the block it sits in and impersonate the harness. Treat this
  as defence in depth, not a guarantee: a model that reads a hostile note may still be influenced
  by it, so do not ingest documents you would not paste into a prompt yourself.
- **`humona ingest` is for your own documents.** Ingested text becomes searchable memory; it is not
  executed, but it is injected, so the paragraph above applies to it.
- **The sensory trace is redacted, not absent.** Prompts and commands are captured for two days
  with secrets patterns stripped. `humona pause` stops capture, `<private>…</private>` excludes a
  passage, and `--private` keeps a note out of sync entirely.
- **`humona doctor` fails if the vault's remote is the code's remote.** That is the one
  misconfiguration that would publish private notes to a public repository.
- **Deletion is explicit and user-only.** `humona forget` refuses to run without a terminal unless
  `--yes` is passed, so neither a model nor a cron job deletes memory on a guess.

## What is not a vulnerability

- A model deciding to write a poor note, or forgetting to write one. That is a prompt and rules
  question; the rules block is in `setup/CLAUDE.md`.
- Secrets you deliberately stored in a note. `humona doctor` scans synced notes for common secret
  patterns, but it is a safety net, not a scanner you should rely on.
- `humona upgrade` applying a commit you do not like. It prints the version and the diffstat and
  asks before it applies; pinning to signed tags is tracked in [ROADMAP.md](ROADMAP.md).
