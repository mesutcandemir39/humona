# Versioning, channels and support

Two numbers matter here, and they move independently.

| | What it versions | Where it lives | Changes when |
|---|---|---|---|
| **Engine version** | the code: CLI, hooks, MCP surface | `engine/humona.py` `VERSION`, `pyproject.toml`, `.claude-plugin/plugin.json` | every release |
| **Vault schema** | the layout of your memory on disk | `SCHEMA` in the engine, stamped into `memory/.brain-schema.json` | rarely, and never without a migration |

Rolling code back is easy. Rolling data back is not. Keeping the two numbers apart is what lets a
bad release be undone without touching a single note.

## Engine version: SemVer 2.0

`MAJOR.MINOR.PATCH`, and the promise attached to each part is about *your* setup, not ours:

- **PATCH** (2.14.0 → 2.14.1): fixes only. Nothing you type changes meaning.
- **MINOR** (2.14.x → 2.15.0): new commands, new flags, new behaviour that is off by default.
  Everything that worked keeps working.
- **MAJOR** (2.x → 3.0.0): something that worked no longer does. Reserved for a changed hook
  contract, a removed command, or a vault schema that older engines cannot read.

What counts as breaking, and therefore as MAJOR:

- removing a command or a flag, or changing what one does
- changing the shape of `--json` output that a script could depend on
- changing the hook contract (event names, payload keys, the injected block's element names)
- a vault schema bump that an older engine cannot read

What is explicitly *not* breaking: the wording of human-readable output, the ranking of search
results, the set of notes auto-recall chooses, and anything behind a flag that is off by default.

### Deprecation

A flag or command on its way out prints a warning naming its replacement for **at least two minor
releases** before it is removed, and the CHANGELOG entry says which release removes it. Nothing is
removed in a patch.

## Vault schema and migrations

The schema is a plain integer, currently **1**, stamped in `memory/.brain-schema.json` with the
version that wrote it.

- `humona migrate` brings a vault forward, one step at a time, and stamps the result.
- `humona migrate --dry-run` says what it would do and changes nothing.
- **An engine refuses to write a vault whose schema is newer than it understands.** It still reads
  it, and it tells you so. This is the guard that stops an old engine from quietly dropping fields
  it does not know about, which is the one way a rollback could corrupt memory.
- A migration is written so that it can be interrupted: it moves files rather than rewriting them
  in place where it can, and the stamp is written last, so a half-finished run is re-runnable.
- Take a snapshot first if the migration is large: `humona backup`.

## Release channels

| Channel | What it is | How to follow it |
|---|---|---|
| **stable** | the signed tags on `main` | the default; `humona upgrade` |
| **beta** | prerelease tags (`2.15.0-beta.1`) | `git -C <checkout> checkout <tag>` then `python3 setup/install.py` |
| **nightly** | `main` as it stands | `humona upgrade` on a checkout tracking `main` |

`release.json` in the repository is the manifest `humona upgrade` reads *before it applies
anything*:

```json
{ "channel": "stable", "latest": "2.15.0", "min_supported": "2.12.0", "yanked": [] }
```

- `yanked` is the kill switch. A version listed there is refused by every client that has not yet
  taken it, with the maintainer's note printed. No server, no telemetry — one `git show`.
- `min_supported` is the oldest version still receiving fixes. Below it, `humona upgrade` says so.

## What an upgrade actually does

```
fetch  →  print the version and the file diff  →  check release.json (yank, min_supported)
       →  check the tag signature (optional)   →  fast-forward only, never a merge
       →  run the test suite on the new code   →  re-apply setup
       →  run doctor; on failure, reset back to the previous commit and re-install
```

It refuses rather than guesses: a dirty checkout stops it, a failing test aborts it before
anything is installed, and a failing health check rolls it back. The vault is not a git target of
any step — a test asserts that the upgrade path never names it.

## Support window

- The **latest minor** gets fixes.
- The **previous minor** gets security fixes for 90 days after the next minor ships.
- Older than that: upgrade. Your memory is Markdown; nothing about it expires.

Security reports go through the process in [SECURITY.md](SECURITY.md), not through issues.

## Plugin versions

When installed as a Claude Code plugin, three places carry the version and must agree:
`engine/humona.py`, `.claude-plugin/plugin.json`, and the entry in `.claude-plugin/marketplace.json`.
Users on the plugin get updates the way Claude Code delivers every plugin update — bump the version
in the manifest and push; their client picks it up. They do not run `humona upgrade` at all.

## Checklist for cutting a release

1. `python3 tests/test_humona.py` — all green, on every OS CI covers.
2. `python3 tools/bench.py` — no regression in session-start tokens or hook latency.
3. `python3 tools/engine_map.py` — regenerate if the engine moved.
4. Bump the version in the three places above; add the CHANGELOG entry.
5. Update `release.json`: `latest`, and `min_supported` if the window moved.
6. `git tag -s v<version> -m "<version>"` — signed, so `humona upgrade --verify-tags` means something.
7. `python3 setup/export_public.py <dir>` and push the public copy.
8. Watch the issue tracker. If the release is bad: add it to `yanked`, push, and ship the fix.
