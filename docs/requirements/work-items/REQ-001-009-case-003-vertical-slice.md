# Work Item: Case 003 Deterministic Vertical Slice

Status: Verified

## Requirement Coverage

- `REQ-001` Source package inventory
- `REQ-002` Deterministic ingestion
- `REQ-003` Evidence model
- `REQ-004` Structured decision packet
- `REQ-005` Budget and vendor tools
- `REQ-006` Policy findings
- `REQ-007` Missing information detection
- `REQ-008` Approval route
- `REQ-009` Tool/function trace

## User Or Reviewer Outcome

A reviewer can run one command for `case_003` and receive a valid, evidence-backed decision packet showing why TalentPulse AI is blocked and who must review it.

## Scope

Expected implementation files:

- `vendor_agent/schemas.py`
- `vendor_agent/inventory.py`
- `vendor_agent/parsers.py`
- `vendor_agent/tools.py`
- `vendor_agent/policies.py`
- `vendor_agent/pipeline.py`
- `vendor_agent/tracing.py`
- `vendor_agent/cli.py`
- focused tests under `tests/`

Do not change the candidate source package.

## Acceptance Criteria

- CLI command writes a JSON decision packet for `case_003`.
- Packet validates against the Pydantic `DecisionPacket` schema.
- Packet includes parsed intake, quote, contract, questionnaire, policy/tool results, missing information, approval route, evidence, and trace.
- TalentPulse AI is classified as high risk.
- Packet status is blocked, not approved.
- Missing items include SOC 2 Type II, DPA, AI training opt-out, and SCIM provisioning answer.
- Finance findings include budget shortfall, CFO threshold, long term, and Net 90 payment terms.
- Legal/security findings include employee sensitive data, AI/model training, subprocessors outside the US, missing SOC 2 Type II, and non-standard liability.
- Approval route includes Business owner, Procurement manager, VP Finance, CFO, Legal, Security, and Executive sponsor.
- Trace includes parser/tool/policy steps with status, inputs, outputs, timing, and requirement IDs.

## Verification Plan

```bash
python3 -m pytest -q
python3 -m vendor_agent.cli run \
  --case data/source-package/Candidate_package/cases/case_003 \
  --out outputs/case_003.json
```

Then inspect:

- `outputs/case_003.json`
- derived trace output, if emitted separately

## Verification Result

Completed:

```bash
python3 -m pytest -q
python3 -m vendor_agent.cli run \
  --case data/source-package/Candidate_package/cases/case_003 \
  --out outputs/case_003.json
```

Result:

- `7 passed`
- `outputs/case_003.json` written
- `outputs/case_003.trace.json` written
- packet status is `blocked`

## Guardrails

- No LLM dependency in this slice.
- No final approval language.
- No send action.
- No spend commitment.
- No legal acceptance.
- No policy override.
- No new dependency unless required for parsing existing package files.
