# Requirements Register

This is the source of truth for what the Accelerant prototype must satisfy. Kanban tasks should reference these requirement IDs.

Status values:

- `Proposed` - identified, not ready to build
- `Ready` - acceptance criteria are clear
- `In Progress` - implementation started
- `Implemented` - code exists
- `Verified` - tests/evals/UI checks passed
- `Deferred` - intentionally out of current scope

| ID | Requirement | Source | Priority | Acceptance Criteria | Verification | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | Source package inventory | Exam: read intake, email, quote, questionnaire, contract, policy docs | Must | System lists expected files per case and reports missing/unreadable files clearly. | Unit test plus eval fixture | Verified |
| REQ-002 | Deterministic ingestion | Exam: read case inputs | Must | Intake workbook, quote CSV, vendor email, security questionnaire, contract PDF, policy docs, budget lookup, and vendor register are parsed into typed facts. | Parser tests | Verified |
| REQ-003 | Evidence model | Exam: recommendation must be auditable | Must | Every extracted fact and finding can point to source file plus page, sheet, section, cell, or snippet. | Schema validation plus evidence resolution test | Verified |
| REQ-004 | Structured decision packet | Exam: produce structured output | Must | Each run emits JSON with summary, missing info, findings, approval route, drafts, evidence, and trace. | `python3 -m vendor_agent.cli run` output validation | Verified |
| REQ-005 | Budget and vendor tools | Exam: include tools/function calls | Must | Deterministic functions perform budget lookup, duplicate vendor check, TCV calculation, and vendor risk lookup. | Tool unit tests plus trace check | Verified |
| REQ-006 | Policy findings | Exam: check internal policies | Must | Finance, legal, security, procurement, and vendor-risk rules produce function-specific findings with severity and evidence. | Policy rule tests plus case evals | Verified |
| REQ-007 | Missing information detection | Exam: identify missing info | Must | Missing documents and unresolved questions are surfaced as actionable requests to vendor or internal owner. | Case eval baselines | Verified |
| REQ-008 | Approval route | Exam: human-in-loop signoffs | Must | Output states required reviewers and explicitly prevents autonomous approval or spend commitment. | Case eval plus UI review | Verified |
| REQ-009 | Tool/function trace | Exam: include tools/function calls | Must | Every parser/tool/rule call emits a trace entry with inputs, outputs, status, timing, and evidence IDs when applicable. | Trace schema validation | Verified |
| REQ-010 | Streamlit review cockpit | Exam: working prototype usable by others | Must | App lets reviewer select a case, run triage, inspect overview, findings, evidence, drafts, and trace, and export outputs. | Streamlit smoke test plus manual UX checklist | Verified |
| REQ-011 | Draft outputs | Product judgment | Should | System drafts vendor follow-up and internal ticket text, clearly labeled as drafts. | Snapshot/human review | Verified |
| REQ-012 | Eval harness | Exam: reproducible results; production judgment | Must | All three cases have expected baselines and a CLI eval command that fails on regressions. | `python3 -m vendor_agent.cli eval` | Verified |
| REQ-013 | Reproducible CLI | Exam: runnable repo | Must | Fresh clone can run CLI without Streamlit and produce deterministic JSON outputs. | README command smoke test | Verified |
| REQ-014 | Deployment path | Exam: deployed environment usable by others | Must | Private deployed Streamlit app can run all cases with no local setup. | Deployed smoke test | Verified |
| REQ-015 | Productionization narrative | Exam: explain production path | Must | Docs explain architecture, guardrails, monitoring, evals, human workflow, and enterprise system integrations. | Document review | Implemented |
| REQ-016 | Confidentiality and secrets | Interview/package sensitivity | Must | Candidate package remains private; no secrets committed; `.env.example` documents env vars only. | Git status and secret scan/manual review | Verified |
| REQ-017 | AI-assisted development guardrails | Vibe-coded project risk | Must | Repo contains local AI instructions, requirement register, acceptance matrix, issue form, and PR checklist. | File presence plus review | Verified |
| REQ-018 | Uploaded vendor package mode | Reviewer testing risk | Must | App accepts a new single-vendor package as multiple files or a zip, validates required artifacts, stages files temporarily, and runs the same deterministic pipeline. | Upload unit tests plus Streamlit smoke test | Verified |

## Traceability Notes

- The first vertical slice should cover `REQ-001` through `REQ-009` for `case_003`.
- The UI should not begin until `REQ-004`, `REQ-006`, `REQ-008`, and `REQ-009` have usable output.
- LLM synthesis is not its own requirement until deterministic outputs are stable; it supports `REQ-004`, `REQ-011`, and `REQ-015`.
- Upload mode is required for reviewer-driven testing, but it should not fork the business logic. Uploaded packages must stage into the same canonical case structure and call the same pipeline as sample cases.

## Implementation Notes

- `REQ-001` through `REQ-009` are verified across all three provided cases by `python3 -m vendor_agent.cli eval`.
- `REQ-010` is verified locally and in the deployed Streamlit app.
- `REQ-014` is verified with the deployed Streamlit app, default sample run, upload validation, uploaded zip run, and HTTP cookie-jar smoke check.
- `REQ-018` is verified for multi-file uploads, zip uploads, and missing-file validation.
