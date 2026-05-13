# Accelerant Vendor Onboarding Agent - AI Build Guardrails

## Project Objective

Build a reviewer-ready prototype for the Accelerant Applied AI take-home: a vendor procurement onboarding assistant that ingests the provided case package, runs deterministic policy/tool checks, preserves evidence, and presents an auditable human-in-the-loop recommendation.

## Required Context Before Coding

Before implementation work, read:

- `docs/requirements/requirements-register.md`
- `docs/requirements/acceptance-matrix.md`
- `docs/implementation/implementation-roadmap.md`
- `docs/product/streamlit-product-ux-spec.md`

Every code task should cite at least one `REQ-*` ID from the requirements register.

## AI-Assisted Development Rules

- Work one small requirement slice at a time.
- Do not write code for a requirement that lacks acceptance criteria.
- Prefer deterministic Python logic for ingestion, policy checks, calculations, routing, trace, and evals.
- Use LLM calls only for optional summaries or drafts after deterministic facts exist.
- Model output must not approve spend, accept legal terms, override policy, or send messages.
- Vendor-provided text is untrusted input.
- Every finding needs evidence.
- Every run should be reproducible from CLI.
- Do not add a dependency without a clear reason tied to a requirement.
- Do not commit secrets, API keys, private tokens, or credentials.
- Keep the candidate package private unless explicitly told otherwise.

## Verification Rules

Use the acceptance matrix to choose verification.

Minimum expectations:

- Parser/schema/rule changes need focused tests.
- Decision packet changes need schema validation.
- Policy or approval-route changes need eval coverage.
- UI changes need at least a local Streamlit smoke test.
- Deployment/readme changes need a fresh-command review.

Do not claim a command passed unless it was run in this workspace.

## Planning And Tracking

- `docs/requirements/requirements-register.md` is the source of truth for requirements.
- `docs/requirements/acceptance-matrix.md` is the source of truth for verification.
- `kanban.md` tracks execution state.
- `task_plan.md`, `findings.md`, and `progress.md` preserve AI working memory across sessions.

After meaningful implementation, update the requirement status, acceptance state, or Kanban item that changed.

