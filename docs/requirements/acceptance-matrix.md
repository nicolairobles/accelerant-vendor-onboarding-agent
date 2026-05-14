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
| REQ-010 | UI smoke test | `streamlit run app.py` and deployed Streamlit app | Reviewer starts at a vendor request queue, can open seeded requests, and can inspect decision, findings, evidence, drafts, workflow, and trace. | Verified |
| REQ-011 | Draft quality review | Decision packets and UI Drafts tab | Drafts are actionable, labeled drafts, and avoid approval/commitment language. | Verified |
| REQ-012 | Eval harness | `python3 -m vendor_agent.cli eval` | All seeded cases pass; failures show actionable diff. | Verified |
| REQ-013 | Fresh-clone smoke test | README commands | Setup and CLI commands work from a clean environment. | Verified locally |
| REQ-014 | Deployed smoke test | Streamlit URL | Deployed app loads and runs all cases without local files from reviewer. | Verified |
| REQ-015 | Document review | `ARCHITECTURE.md`, `PRODUCTIONIZATION.md`, README | Docs explain architecture, product judgment, evals, guardrails, and production path. | Implemented |
| REQ-016 | Public-sharing review | `.gitignore`, `.env.example`, git status, secret scan | No secrets; public repo contains only synthetic exercise materials and explicit env-var documentation. | Verified locally |
| REQ-017 | Build guardrails review | `.github/workflows/ci.yml`, tests, evals | CI runs compile checks, unit tests, and deterministic evals on push. | Verified |
| REQ-018 | Submit new request tests | `tests/test_upload_mode.py`, `tests/test_streamlit_app.py`, Streamlit smoke test | Multiple files and zip upload stage to a canonical case format; seeded requests are not mutated; missing required files are reported before triage; optional support docs are mapped. | Verified |
| REQ-019 | Dashboard regression test | `tests/test_streamlit_app.py` | App home renders a vendor request queue with status, risk, spend, missing-info, source, open action, and next-owner fields. | Verified |
| REQ-020 | Upload guardrail regression tests | `tests/test_upload_mode.py` | Policy docs are not misclassified as questionnaires; corrupt quote CSV is rejected; mixed-vendor zip is blocked; prompt injection does not bypass human gate; optional artifacts resolve matching checklist items. | Verified |
| REQ-021 | Workflow/workbook export tests | `tests/test_streamlit_app.py` | Case view includes triage workflow progress and workbook export contains Summary, Missing Info, Findings, Approval Route, and Trace sheets. | Verified |
| REQ-022 | Sample upload packet tests | `tests/test_sample_upload_packets.py`, `data/sample-upload-packets/README.md` | Valid sample packets run as expected; the net-new SupportFlow packet has no sample baseline; invalid/guardrail sample packets are blocked or remain human-gated; zips are available for manual app testing. | Verified |
| REQ-023 | Productized reviewer UX test | `tests/test_streamlit_app.py`, deployed smoke | Sidebar has no implementation-mode copy; missing-info follow-up is not rendered as inert checkboxes; request view starts with decision, next action, owner, Required Vendor Follow-up, Internal Review Route, and reviewer brief; drafts, evidence, workflow, trace, and exports stay behind disclosure. | Verified |
| REQ-024 | Synthesis guardrail tests | `tests/test_synthesis.py`, `tests/test_streamlit_app.py`, `docs/research/llm-synthesis-assessment.md` | Reviewer synthesis is generated from structured packet fields, optional OpenAI structured output is validated, known evidence IDs are cited, missing information is preserved, prohibited action language is blocked, UI/export surfaces remain deterministic-safe. | Verified |
| REQ-025 | Request lifecycle tests | `tests/test_streamlit_app.py`, deployed smoke | Seeded cases render as vendor requests; queue rows open detail pages; submit flow creates new queue records in session state; delete removes a request from the queue; noisy drafts/upload mappings/audit details stay behind disclosure. | Verified |

## Verification Tiers

Use the smallest tier that matches the risk.

| Tier | Use When | Required Checks |
| --- | --- | --- |
| Quick | Docs-only or narrow copy update | Markdown review, git diff |
| Standard | Parser, schema, policy, CLI, or UI change | Relevant unit tests plus CLI smoke |
| Critical | Approval routing, guardrails, evals, deployment, secrets, policy logic | Full pytest, eval CLI, manual evidence review, README/doc update |
