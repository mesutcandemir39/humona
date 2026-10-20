---
name: make-plan
description: Research and write an implementation plan into humona's memory, then execute it step by step (do).
---
# make-plan / do
Plan:
1. Research with smart-explore (outline/refs, map Notes) — don't read whole files.
2. Write `memory/projects/<p>/plans/YYYY-MM-DD-<slug>.md`: Goal, Context (files:lines), Steps as `- [ ]` checklist (each small + verifiable), Risks, Done-when.
3. Point working memory at it: `humona working -` with Goal + "Plan: [[projects/<p>/plans/<file>]]" + Current step.
Do:
4. Execute one step at a time; after each, tick `- [x]` in the plan and update Current step in working memory.
5. Delegate to a subagent only for independent, well-specified steps (parallel research/tests); give it the plan path + exact step.
6. Verify (tests/build) before ticking. On finish: `humona episode "…"`, record decisions with `humona remember --kind decision`.
