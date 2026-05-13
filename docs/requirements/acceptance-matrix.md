# Acceptance Matrix

This matrix defines how we know each requirement is actually satisfied.

| Requirement | Primary Check | Command Or Artifact | Pass Condition | Current State |
| --- | --- | --- | --- | --- |
| REQ-001 | Source inventory test | `tests/test_case003_vertical_slice.py`, `python3 -m vendor_agent.cli eval` | All expected case files are detected; missing files produce explicit errors. | Verified |
| REQ-002 | Parser tests | `tests/test_case003_vertical_slice.py`, `tests/test_eval_harness.py` | Parsed facts match source package fixtures. | Verified |
| REQ-003 | Evidence resolution test | `python3 -m vendor_agent.cli eval` | Every fact/finding has a valid evidence reference. | Verified |
| REQ-004 | Decision packet schema validation | `outputs/case_001.json`, `outputs/case_002.json`, `outputs/case_003.json` | JSON validates against `DecisionPacket`. | Verified |
| REQ-005 | Tool unit tests | `tests/test_case003_vertical_slice.py`, `tests/test_eval_harness.py` | Budget, duplicate vendor, TCV, and risk outputs are deterministic. | Verified |
| REQ-006 | Policy rule tests | `python3 -m vendor_agent.cli eval` | Expected blockers, warnings, and approvals match case baselines. | Verified |
| REQ-007 | Missing info eval | `evals/seed-cases.json` | Missing vendor/internal info matches expected baseline per case. | Verified |
| REQ-008 | Approval route eval | `python3 -m vendor_agent.cli eval` | Approval route matches expected reviewers and never grants final approval. | Verified |
| REQ-009 | Trace validation | `outputs/case_*.trace.json` | Trace includes tool names, inputs, outputs, timing, and status. | Verified |
| REQ-010 | UI smoke test | `streamlit run app.py` | Reviewer can run all three cases and inspect Overview, Findings, Evidence, Drafts, Trace. | Implemented; HTTP 200 local smoke passed |
| REQ-011 | Draft quality review | Decision packets and UI Drafts tab | Drafts are actionable, labeled drafts, and avoid approval/commitment language. | Verified |
| REQ-012 | Eval harness | `python3 -m vendor_agent.cli eval` | All seeded cases pass; failures show actionable diff. | Verified |
| REQ-013 | Fresh-clone smoke test | README commands | Setup and CLI commands work from a clean environment. | Verified locally |
| REQ-014 | Deployed smoke test | Streamlit URL | Deployed app loads and runs all cases without local files from reviewer. | Not started |
| REQ-015 | Document review | `ARCHITECTURE.md`, `PRODUCTIONIZATION.md`, README | Docs explain architecture, product judgment, evals, guardrails, and production path. | Implemented |
| REQ-016 | Confidentiality review | `.gitignore`, `.env.example`, git status | No secrets; repo stays private; package handling is explicit. | Verified locally |
| REQ-017 | Guardrail files review | `AGENTS.md`, `.github/`, `docs/requirements/` | AI/build guardrails exist and are referenced by future work. | Verified |
| REQ-018 | Upload package tests | `tests/test_upload_mode.py`, Streamlit smoke test | Multiple files and zip upload stage to canonical case format; missing required files are reported before triage. | Verified |

## Verification Tiers

Use the smallest tier that matches the risk.

| Tier | Use When | Required Checks |
| --- | --- | --- |
| Quick | Docs-only or narrow copy update | Markdown review, git diff |
| Standard | Parser, schema, policy, CLI, or UI change | Relevant unit tests plus CLI smoke |
| Critical | Approval routing, guardrails, evals, deployment, secrets, policy logic | Full pytest, eval CLI, manual evidence review, README/doc update |
