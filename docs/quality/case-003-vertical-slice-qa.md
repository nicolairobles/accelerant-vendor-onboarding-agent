# Case 003 Vertical Slice QA Assessment

Date: 2026-05-13

Scope: deterministic `case_003` implementation covering `REQ-001` through `REQ-009`.

## Executive Assessment

The `case_003` vertical slice is a credible first implementation of the core exam requirements. It now produces a structured, evidence-backed decision packet and a separate trace file through the CLI. It correctly blocks TalentPulse AI because the request combines high-risk employee-data AI processing, missing security/legal materials, insufficient budget, long contract term, Net 90 terms, non-US subprocessors, and model-training/data-use concerns.

Current quality rating for this slice: `B+`.

It is not submission-ready overall because only one of three cases is implemented and there is not yet a cross-case eval harness or Streamlit review cockpit. But the architecture is now grounded in working code rather than only strategy.

## QA Checks Performed

### Requirements Coverage

- `REQ-001` source package inventory: pass for `case_003`.
- `REQ-002` deterministic ingestion: pass for `case_003` intake, quote, contract, questionnaire, vendor email, policies, budget lookup, and vendor register.
- `REQ-003` evidence model: pass for `case_003`; all findings and trace evidence references resolve.
- `REQ-004` structured decision packet: pass for `case_003`; output validates against `DecisionPacket`.
- `REQ-005` budget/vendor tools: pass for `case_003`; budget, duplicate vendor, TCV, and risk classification run deterministically.
- `REQ-006` policy findings: pass for `case_003`; expected Finance, Legal, Security, Procurement, and Vendor Risk findings are present.
- `REQ-007` missing information: pass for `case_003`; missing SOC 2 Type II, DPA, AI training opt-out, SCIM answer, and incident response summary are surfaced.
- `REQ-008` approval route: pass for `case_003`; blocked route includes required human reviewers and prohibited actions.
- `REQ-009` tool/function trace: pass for `case_003`; trace includes tool name, inputs, outputs, status, timing, requirement IDs, and evidence IDs where applicable.

### Functional Output QA

Verified output facts:

- Vendor: TalentPulse AI
- Status: blocked
- Risk tier: high
- ACV: $120,000
- One-time fees: $20,000
- Total contract value: $380,000
- Budget remaining: $90,000
- Budget delta: -$30,000
- Required reviewers: Business owner, Procurement manager, VP Finance, CFO, Legal, Security, Executive sponsor
- Evidence count: 39
- Trace steps: 15

### Guardrail QA

Verified:

- No LLM dependency in the slice.
- Packet status is not approved.
- Drafts are marked as requiring human approval.
- Approval route explicitly prohibits approving vendors, committing spend, accepting contract terms, sending external communications, or bypassing required reviewers.
- No secrets were found in `.env` or Streamlit secrets files.
- Generated runtime outputs remain under ignored `outputs/`.

## Issues Found And Fixed

### 1. Trace entries lacked evidence IDs

Finding: The trace included tool calls and outputs, but most trace entries did not carry the evidence IDs they depended on.

Fix: Added `evidence_id_extractor` support to `TraceRecorder.run` and populated evidence IDs for ingestion, tools, missing-info detection, policy checks, approval routing, and drafts.

Files:

- `vendor_agent/tracing.py`
- `vendor_agent/pipeline.py`
- `tests/test_case003_vertical_slice.py`

### 2. Vendor email was read but not represented as structured evidence

Finding: The vendor email was traced but not included in `CaseFacts` or the evidence model, weakening the claim that all source materials were ingested.

Fix: Added `parse_vendor_email`, added `vendor_email` to `CaseFacts`, and added regression coverage.

Files:

- `vendor_agent/schemas.py`
- `vendor_agent/parsers.py`
- `vendor_agent/pipeline.py`
- `tests/test_case003_vertical_slice.py`

### 3. Policy strings were too case-specific

Finding: Several policy outputs hardcoded TalentPulse, PEOPLE-010, HRIS/Slack, or contact-specific wording. That was acceptable for the first slice but bad for the next generalization step.

Fix: Replaced hardcoded strings with values from `CaseFacts` where practical.

Files:

- `vendor_agent/policies.py`
- `vendor_agent/pipeline.py`

### 4. Tests did not cover missing-file reporting

Finding: `REQ-001` required missing/unreadable files to be surfaced, but the tests only checked the happy path.

Fix: Added a synthetic package-layout test proving `inventory_case` reports a missing quote file.

File:

- `tests/test_case003_vertical_slice.py`

### 5. Work item used a brittle verification command

Finding: The work item still listed bare `pytest`, but this machine's bare `pytest` points at a Python environment without project dependencies.

Fix: Updated the work item to use `python3 -m pytest -q`.

File:

- `docs/requirements/work-items/REQ-001-009-case-003-vertical-slice.md`

## Residual Risks

- Only `case_003` is implemented and verified. Full requirement verification still requires `case_001`, `case_002`, and a real eval harness.
- Policy logic is deterministic but still encoded directly in Python. Before productionization, policy rules should move toward config/data-backed rules or at least dedicated rule tables.
- Parser assumptions match the provided package but are not robust to arbitrary vendor packets.
- The current Streamlit app is still a placeholder and does not use the decision packet yet.
- CLI has `run` only; `eval` is planned but not implemented.
- Dependencies are unpinned. That is acceptable for the prototype phase, but final submission should use pinned or range-bounded dependencies.
- Generated outputs are ignored by git, which is good for runtime hygiene but means final reviewer artifacts need to be regenerated or intentionally exported before submission.

## Final QA Verdict

This slice is acceptable to build on.

Do not start UI polish yet. The next quality move is to generalize the deterministic core across all three cases and add the eval harness. After all three cases pass deterministic evals, the Streamlit app can consume the same decision-packet contract.

## Verification Commands

```bash
python3 -m py_compile app.py vendor_agent/*.py tests/*.py
python3 -m pytest -q
python3 -m vendor_agent.cli run \
  --case data/source-package/Candidate_package/cases/case_003 \
  --out outputs/case_003.json
```

Latest result:

- `python3 -m py_compile app.py vendor_agent/*.py tests/*.py`: pass
- `python3 -m pytest -q`: `7 passed`
- CLI run: wrote `outputs/case_003.json`, wrote `outputs/case_003.trace.json`, status `blocked`

