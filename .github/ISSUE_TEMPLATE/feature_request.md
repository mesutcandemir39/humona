---
name: Feature request
about: Something the engine should do and does not
labels: enhancement
---

**What you are trying to do**, and what you do today instead.

**Why it belongs in the engine** rather than in your own rules or a skill.

**What it must not cost.** The two standing constraints: a hook may never block a session
(~0.2 s budget), and nothing may add a runtime dependency to `engine/humona.py`. If your idea needs
either, say so — it may still be right, as an optional layer.

**How we would know it works** — the check that would prove it, in the shape the tests use.
