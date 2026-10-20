## What this changes, and why

## How it was verified
<!-- Not "it should work". The command you ran and what it printed. -->
- [ ] `python3 tests/test_humona.py` passes (and a new test covers this change)
- [ ] `humona doctor` passes on my machine
- [ ] `python3 tools/bench.py` shows no regression in session-start tokens or hook latency

## Constraints checked
- [ ] `engine/humona.py` still imports only the standard library
- [ ] no hook can block a session (git in its own process group, stdin polled, not blocked on)
- [ ] a model-chosen path still goes through `inside()`
- [ ] notes are superseded or archived, never silently deleted
- [ ] performance claims in docs come with the command that reproduces them
