# Architecture

## Product Shape

This prototype is a deterministic vendor onboarding triage workflow with a human review cockpit. It is intentionally not an autonomous approval agent.

The system ingests a mixed vendor package, normalizes source facts into typed schemas, runs deterministic policy/tool checks, preserves evidence, and produces a structured decision packet for a procurement owner.

## Flow

```text
case package
  -> inventory check
  -> deterministic parsers
  -> Pydantic decision schemas
  -> budget/vendor/risk tools
  -> policy findings
  -> missing-info detection
  -> approval route
  -> draft messages
  -> trace + decision packet
  -> CLI / Streamlit review cockpit
```

## Key Modules

| Module | Responsibility |
| --- | --- |
| `vendor_agent.inventory` | Verifies expected source files exist for each case. |
| `vendor_agent.parsers` | Parses Excel intake, quote CSV, contract PDF, security questionnaire, vendor email, and policy docs. |
| `vendor_agent.schemas` | Defines the product contract for evidence, facts, findings, approval route, drafts, trace, and decision packet. |
| `vendor_agent.tools` | Implements deterministic tool-like checks: budget lookup, duplicate vendor lookup, TCV calculation, and risk classification. |
| `vendor_agent.policies` | Applies deterministic procurement, finance, legal, security, and vendor-risk rules. |
| `vendor_agent.tracing` | Records workflow steps, inputs, outputs, timing, requirement IDs, and evidence IDs. |
| `vendor_agent.pipeline` | Orchestrates one case into a `DecisionPacket`. |
| `vendor_agent.evaluator` | Runs all seeded cases against expected baselines. |
| `app.py` | Streamlit review cockpit over the same `DecisionPacket` contract. |

## Why Deterministic First

Procurement onboarding has explicit policies, financial thresholds, evidence requirements, and high-risk human approvals. The model should not own those decisions.

The current prototype uses deterministic code for:

- parsing source files
- extracting facts
- calculating ACV, one-time fees, and total contract value
- checking budget
- checking existing vendors
- classifying preliminary risk
- detecting missing information
- determining approval route
- preserving evidence and trace

An LLM can be added later for concise summaries or better draft wording, but only after deterministic facts and policy outputs exist. Model output should validate against the same schemas and must not override policy checks.

## Decision Packet Contract

Each run emits:

- `case_id`
- `status`
- `status_reason`
- `summary`
- normalized `facts`
- `missing_information`
- policy `findings`
- `approval_route`
- draft messages
- source `evidence`
- workflow `trace`

This structure is used by both CLI and Streamlit, so UI behavior and reproducible command-line output stay aligned.

## Evidence Model

Every extracted fact and policy finding links to evidence where practical:

- source file
- source type
- location such as sheet cell, CSV row, PDF page, markdown section, or email body
- snippet
- parsed value

The trace also carries evidence IDs for parser, tool, policy, approval-route, and draft steps.

## Human-In-The-Loop Boundary

The system may:

- summarize the vendor request
- identify missing information
- recommend review routing
- create draft vendor follow-ups
- create draft internal notes
- export packet and trace

The system must not:

- approve a vendor
- commit company spend
- accept legal terms
- send external communications
- bypass Procurement, Finance, Legal, Security, or executive approvals

## Current Coverage

The deterministic pipeline currently covers:

- `case_001`: Northstar Analytics, high-risk SaaS/customer-data AI vendor, duplicate vendor review, missing SOC 2 Type II and DPA, data-use opt-out confirmation needed.
- `case_002`: Workspace Depot, low-risk office-supplies renewal, setup documents missing, no unnecessary Legal/Security escalation.
- `case_003`: TalentPulse AI, high-risk employee-data AI vendor, budget shortfall, missing legal/security materials, AI training opt-out issue, CFO/Legal/Security/executive route.

