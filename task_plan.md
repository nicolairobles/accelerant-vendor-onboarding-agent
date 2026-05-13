# Task Plan

Goal: build the Accelerant vendor onboarding prototype with explicit requirements traceability and AI-assisted development guardrails.

## Phases

| Phase | Status | Outcome |
| --- | --- | --- |
| 1. Source package and exam understanding | Complete | Candidate package copied and exam requirements summarized. |
| 2. Prototype strategy and UX direction | Complete | Strategy, critique, UX spec, and implementation roadmap created. |
| 3. Requirements control plane | Complete | Requirements register, acceptance matrix, AI guardrails, and GitHub templates created. |
| 4. Deterministic core implementation | Complete | CLI emits valid decision packets for all three cases. |
| 5. Policy routing and eval harness | Complete | All three cases pass deterministic evals. |
| 6. Streamlit review cockpit | Complete | Reviewer starts from a case queue, drills into cases, and inspects overview, workflow, findings, evidence, drafts, and trace locally. |
| 7. Upload guardrails and edge-case coverage | Complete | Upload mode validates required files, maps optional support artifacts, and blocks high-risk ambiguous packages. |
| 8. Sample upload packets | Complete | Reviewer can manually upload valid, invalid, and guardrail zips from `data/sample-upload-packets/zips`. |
| 9. Packaging and deployment | Pending | Private repo and deployed reviewer app are ready. |
| 10. Product UX cleanup and exam-fit audit | Complete | Removed confusing/nonfunctional UI, aligned visible workflow to procurement reviewer needs, and re-verified end to end. |
| 11. Process-flow synthesis alignment | Complete | Assessed the PNG workflow and added an LLM-ready reviewer synthesis layer behind deterministic packet validation. |
| 12. Optional live OpenAI synthesis | Complete | Added opt-in OpenAI structured-output synthesis with deterministic fail-closed fallback and live smoke verification. |
| 13. Action-first case review UX | Complete | Reworked case pages around decision, next action, owner, vendor follow-up, internal route, editable AI-assisted drafts, and collapsed audit details. |

## Current Decision

The Kanban remains useful for execution state, but requirements live in `docs/requirements/requirements-register.md` and verification lives in `docs/requirements/acceptance-matrix.md`.

The deterministic pipeline, eval harness, dashboard-first Streamlit cockpit, upload guardrails, workbook export, productized reviewer UX, optional OpenAI reviewer synthesis, action-first case review page, and core submission docs are implemented locally. External redeployment after this UI/guardrail pass remains pending.

The current pass completed the action cockpit cleanup. The app now presents a reviewer-facing decision and draft workflow, not implementation-mode labels or fake task controls. Evidence, trace, exports, and human-gate controls remain available through contextual sections and progressive disclosure.

## Errors Encountered

| Error | Resolution |
| --- | --- |
| Bare `pytest` used Python 3.13 without project dependencies | Installed declared requirements for `python3` and verified with `python3 -m pytest -q`. |
| Background Streamlit process exited when launched through a short shell wrapper | Ran Streamlit in a foreground exec session and verified HTTP 200 at `http://127.0.0.1:8501`. |
