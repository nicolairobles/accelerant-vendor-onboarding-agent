# Streamlit Product UX Spec

## Product Positioning

This is a decision-support cockpit for a procurement owner, not a general chat interface and not a data dashboard.

The user should feel: "I can understand this vendor packet, see what is blocking it, and route it confidently without hunting through five files."

The product promise:

> Convert a mixed vendor onboarding package into a structured, evidence-backed decision packet that a human procurement owner can review, correct, and route.

## UX Principles

### 1. Show status before details

Nielsen Norman's first usability heuristic is visibility of system status: users should know what is going on and what happened after their actions. In this app, the first visible result after a run must be a status banner, not a long summary.

Implementation:

- Top banner: `Blocked`, `Ready for cross-functional review`, or `Low-risk renewal - setup docs missing`.
- Include one sentence explaining the status.
- Use `st.status` during parsing/checking so the reviewer sees the pipeline advancing.

Source: [NN/g 10 usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/), [Streamlit st.status](https://docs.streamlit.io/develop/api-reference/status/st.status).

### 2. Use procurement language, not AI language

The user thinks in terms of vendor, request, owner, ACV, TCV, budget, missing docs, approvers, blockers, and next actions. The UI should not lead with "agent trace," "model output," "RAG," or "confidence."

Implementation:

- Main tabs: `Overview`, `Findings`, `Evidence`, `Drafts`, `Trace`.
- Use "Why flagged" instead of "model rationale."
- Use "Source evidence" instead of "context chunks."

Source: [NN/g 10 usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/).

### 3. Make verification easy

Microsoft's overreliance guidance says AI UX should make it easy to spot mistakes and reduce cognitive load when verifying outputs. Google PAIR similarly emphasizes trust calibration and explanations tied to user decisions.

Implementation:

- Every blocker and approval trigger links to evidence.
- Evidence table has columns: finding, source file, location, snippet, policy.
- Do not show raw model confidence percentages. Use evidence completeness and deterministic status instead.
- Highlight unknown or low-confidence extractions as "Needs human check."

Sources:

- [Microsoft overreliance guidance](https://learn.microsoft.com/en-us/ai/playbook/technology-guidance/overreliance-on-ai/overreliance-on-ai)
- [Google PAIR Explainability + Trust](https://pair.withgoogle.com/guidebook-v2/chapter/explainability-trust/)

### 4. Use progressive disclosure

The app should be scan-first and drill-down second. Procurement owners need quick action; Jay/Venkat need proof the internals are sound.

Implementation:

- Overview tab shows only status, key facts, top blockers, required approvers, and next actions.
- Findings tab expands policy triggers by function.
- Evidence tab shows the source table.
- Trace tab is available but not prominent.
- Use `st.tabs` for major views and `st.expander` for secondary explanations. Do not nest expanders.

Sources:

- [Streamlit layouts and containers](https://docs.streamlit.io/develop/concepts/design/layouts-and-containers)
- [Streamlit st.expander](https://docs.streamlit.io/develop/api-reference/layout/st.expander)

### 5. Prevent unsafe action

The app must never imply that the agent can approve a vendor, accept terms, commit spend, or send email.

Implementation:

- Draft messages are displayed in editable text areas labeled `Draft - requires human approval`.
- Buttons say `Copy draft` or `Export packet`, not `Send`.
- Approval route is shown as "required human route," not "approved."
- Show human-safety notices only where they affect routing, draft editing, exports, or prohibited actions. Do not use the sidebar for implementation-mode warnings.

Source: candidate package communication policy, plus [NN/g error prevention heuristic](https://www.nngroup.com/articles/ten-usability-heuristics/).

### 6. Design for accessibility and professional review

The app will be judged in a panel setting. It should be readable on a shared screen and usable without color alone.

Implementation:

- Do not encode risk only by color; include text labels.
- Use clear labels for buttons and controls.
- Keep tables readable with pinned/short columns where possible.
- Avoid dense paragraphs and tiny text.

Source: [W3C WAI accessibility principles](https://www.w3.org/WAI/fundamentals/accessibility-principles/).

## Target Information Architecture

```text
Sidebar
  Workspace selector
    Dashboard
    Review sample case
    Triage new package
  Case selector or uploader by workspace

Main
  Header: Vendor Onboarding Triage
  Dashboard: vendor case queue
  Upload detail: package delta for matched baseline or net-new vendor
  Status banner
  Key metrics row
  Required follow-up panel
  Human review route panel
  Triage workflow progress
  Tabs
    Overview
    Findings
    Evidence
    Drafts
    Trace
```

## First Screen Wireframe

```text
+---------------------------------------------------------------+
| Vendor Onboarding Triage                                      |
| Procurement case queue and evidence-backed review packets.     |
+----------------------+----------------------------------------+
| Sidebar              | Vendor Case Queue                      |
| Workspace            | Cases  Blocked  High Risk  Open Reqs   |
| [Dashboard v]        | 3      3        2          10          |
|                      +----------------------------------------+
|                      | Case     Vendor       Status  Next     |
|                      | 001      Northstar    Blocked Legal    |
|                      | 002      Workspace    Blocked Proc     |
|                      | 003      TalentPulse  Blocked Finance  |
|                      +----------------------------------------+
|                      | Required Follow-up                    |
|                      | 1. Request SOC 2 Type II               |
|                      | 2. Request DPA                         |
|                      | 3. Confirm AI data-use opt-out         |
|                      | 4. Review duplicate vendor match       |
|                      +----------------------------------------+
| Exports              | Approval Route                         |
| JSON / MD / Trace    | Business Owner -> Procurement ->       |
|                      | VP Finance -> Legal -> Security        |
+----------------------+----------------------------------------+
| Tabs: Overview | Findings | Evidence | Drafts | Trace          |
+---------------------------------------------------------------+
```

## Overview Tab

Purpose: answer "what is this and what do I do next?"

Components:

- One-paragraph case summary.
- Key facts as metrics:
  - Vendor
  - ACV
  - TCV
  - Budget status
  - Term
  - Payment terms
  - Risk tier
- `Top blockers` list.
- `Required follow-up` action list with owner, reason, and evidence.
- `Approval route` as an ordered list or horizontal stepper-style display.
- Human guardrails where they affect routing, drafts, or prohibited actions.
- `Reviewer Brief` generated from the validated packet. If a live LLM is added later, label it and show validation status.

Product rule:

- The Overview tab must not contain raw file text or long policy excerpts.

## Dashboard

Purpose: answer "what needs attention first?"

Components:

- Case queue with status, risk, ACV, TCV, budget status, missing-info count, blocker count, and next owner.
- Queue metrics for total cases, blocked cases, high-risk cases, and queue-wide open information requests.
- Priority list that turns the first missing item or blocker into the next procurement action.

Product rule:

- The app should not land on a single default case. A single case can be the default only after the reviewer chooses the review workspace.

## Triage Workflow Panel

Purpose: make the provided process-flow image visible in the running product.

Stages:

- Parse and extract inputs.
- Validate package.
- Normalize case facts.
- Run deterministic helper tools.
- Determine approvals and risk tier.
- Prepare outputs.
- Human approval gate.

The panel should show stage status and tool names without requiring the reviewer to inspect raw trace JSON.

Product rule:

- Show reviewer-friendly stage status and result by default.
- Keep raw function/tool names in Trace or behind progressive disclosure.
- Do not use checkboxes or other controls unless they perform a real action.
- Treat synthesis as part of output preparation, not as the decision maker.

## Findings Tab

Purpose: help each reviewing function see their slice.

Sections:

- Procurement
- Finance
- Legal
- Security
- Business owner
- Executive sponsor

Each finding row:

- Severity: blocker / review required / informational.
- Trigger.
- Why it matters.
- Required owner.
- Evidence count.

Use `st.dataframe` with column configuration for readable tables. Streamlit's column config supports formatting number, link, list, and other column types, which can make evidence and money fields easier to scan.

Source: [Streamlit column configuration](https://docs.streamlit.io/develop/api-reference/data/st.column_config).

## Evidence Tab

Purpose: make the agent auditable.

Table columns:

- Finding
- Source type
- Source file
- Location
- Snippet
- Parsed value
- Policy reference

Filters:

- Function: Legal, Security, Finance, Procurement.
- Severity.
- Source file.

UX rule:

- Evidence is visible by default for blockers.
- Non-blocking evidence can be collapsed.

## Drafts Tab

Purpose: turn the recommendation into action without crossing safety boundaries.

Sections:

- Draft vendor follow-up.
- Draft internal ticket.
- Draft procurement owner note.

Controls:

- Editable text areas.
- `Copy draft` button.
- `Export packet` button.
- No `Send` button.
- Checkbox: `I understand this is a draft and requires human approval` before copying could be enabled.

This is where product sense matters: the app should save the procurement owner from composing from scratch, but it should not pretend to complete the workflow autonomously.

## Trace Tab

Purpose: panel/reviewer/debug view.

Show:

- Tool call sequence.
- Inputs and outputs.
- Runtime.
- Deterministic vs LLM-generated fields.
- Model used.
- Schema validation status.

This tab proves the architecture without overwhelming the primary user.

## Triage Workbook Export

Purpose: create the artifact a procurement owner can hand to Finance, Legal, Security, or a business owner.

Workbook sheets:

- Summary.
- Missing Info.
- Findings.
- Approval Route.
- Trace.

The workbook is a human-routing artifact, not a system-of-record writeback.

## Case-Specific UX Targets

### Case 001: Northstar Analytics

First-screen story:

- Status: `Blocked - cross-functional review and missing security/legal materials`.
- Next actions:
  - Request SOC 2 Type II.
  - Request DPA.
  - Confirm data-use opt-out/account recommendation tuning.
  - Review likely duplicate vendor record.
- Approval route:
  - Business owner, Procurement, VP Finance, Legal, Security.

### Case 002: Workspace Depot

First-screen story:

- Status: `Low-risk renewal - setup docs missing`.
- Next actions:
  - Request W-9/tax form.
  - Request updated vendor setup form.
  - Confirm existing active vendor record.
- Approval route:
  - Business owner, Procurement.
- UX nuance:
  - Do not over-escalate this case. Showing restraint is a product signal.

### Case 003: TalentPulse AI

First-screen story:

- Status: `Blocked - high-risk AI/employee-data vendor`.
- Next actions:
  - Do not route for approval until AI data-use, DPA, SOC 2 Type II, SCIM, and deletion terms are resolved.
  - Escalate to Legal, Security, Finance/CFO, and Executive sponsor.
  - Flag budget shortfall.
- Approval route:
  - Business owner, Procurement, VP Finance, CFO, Legal, Security, Executive sponsor.
- UX nuance:
  - Make the safety boundary visually obvious. This is the case that proves judgment.

## Empty, Loading, And Error States

### Empty state

Message:

> Select a case and run triage to produce a decision packet.

Do not show explanatory marketing copy.

### Loading state

Use `st.status` with steps:

- Parsing intake workbook
- Reading quote and contract
- Checking policy triggers
- Running mock internal tools
- Building decision packet

### Error state

Use plain language:

- `Contract PDF could not be parsed. The decision packet is incomplete.`
- `Budget lookup did not find cost center PEOPLE-010. Route to Finance before approval.`

Never silently continue as if the case is complete.

## Visual Design

Use a restrained operations-tool aesthetic:

- White or near-white background.
- Dark neutral text.
- Limited semantic colors:
  - Red: blocker
  - Amber: review required
  - Green: low-risk/complete
  - Blue/gray: informational
- No decorative hero, gradients, or marketing layout.
- Tables and checklists should do most of the work.

The target is "internal risk review cockpit," not "AI landing page."

## Acceptance Criteria

The app passes the product bar if a procurement owner can answer these within 10 seconds of a completed run:

- What is the vendor asking for?
- Is this blocked or routable?
- What are the top three reasons?
- Who needs to review it?
- What should I ask the vendor/requester next?

The app passes the trust bar if a reviewer can answer these within 60 seconds:

- Which fields came from which files?
- Which findings are deterministic policy checks?
- Which content was LLM-generated?
- Which external actions are blocked pending human approval?
- Can I export a packet and reproduce the result?

## Implementation Notes For Streamlit

Use:

- `st.sidebar` for case controls and human-gate notice.
- `st.status` for run progress.
- `st.columns` and `st.metric` for key facts.
- `st.tabs` for major views.
- `st.expander` for details, but do not nest expanders.
- `st.dataframe` with `st.column_config` for findings and evidence.
- `st.download_button` for JSON, Markdown, and trace exports.
- `st.session_state` for selected case and completed run result.

Sources:

- [Streamlit layouts and containers](https://docs.streamlit.io/develop/concepts/design/layouts-and-containers)
- [Streamlit st.metric](https://docs.streamlit.io/develop/api-reference/data/st.metric)
- [Streamlit st.dataframe](https://docs.streamlit.io/develop/api-reference/data/st.dataframe)
- [Streamlit st.download_button](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button)
- [Streamlit session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)

## Product Metrics For Production

Prototype metrics:

- All three cases produce expected status and route.
- Time from clicking run to visible packet.
- Number of unresolved/unknown extracted facts.
- Eval pass/fail.

Production metrics:

- Median procurement triage time per vendor.
- Percent of requests returned for missing information.
- First-pass routing accuracy by function.
- Reviewer correction rate by field.
- False-ready blocker count.
- Draft follow-up usage rate.
- Time from intake to first complete packet.
