# Productization UX Audit

Date: 2026-05-13

## Scope

This audit reviewed the Streamlit prototype against:

- the original technical exercise prompt
- the provided process-flow PNG
- procurement, finance, legal, security, data handling, vendor risk, and communication policies
- the current requirements register and acceptance matrix
- the running reviewer UI

## Findings

The backend workflow was broadly aligned with the exam scope, but the main case view exposed too much implementation framing. The sidebar text `Mode: Deterministic policy workflow` and `Human gate: No approvals...` was accurate but not useful at that location. It created the impression of an agent demo rather than a procurement triage product.

The previous `Next Actions` checkboxes were a product defect because they did not change workflow state, route the packet, or persist completion. They looked actionable but were only display elements.

The workflow panel showed function-call names too prominently. The prompt asks for tools/function calls, but a procurement reviewer first needs stage status and outcome. Function names belong in trace, exports, or progressive disclosure.

The dashboard metric labeled `Missing Items` was factually correct but could be misread as ten separate vendor requests. The reviewer needs to understand that it is a queue-wide count of unresolved document or answer requests across the three sample cases.

The export buttons were useful for the exam submission but competed with the primary review task when rendered as four always-visible controls near the top of the case page.

## Fixes Implemented

- Removed implementation-mode sidebar copy.
- Replaced inert `Next Actions` checkboxes with `Required Follow-up` action rows showing action, owner, reason, and evidence.
- Renamed `Required Human Route` to `Human Review Route` and moved the human-safety boundary into that decision context.
- Renamed `Agent Workflow` to `Triage Workflow`.
- Showed workflow stage, status, and result by default, with function calls behind an expander.
- Renamed the dashboard count to `Missing Items` and clarified that it is queue-wide.
- Moved packet, trace, brief, and workbook downloads into an `Export decision packet` expander.
- Kept the Drafts acknowledgement checkbox because it gates editing and therefore has a real effect; subject and body are both disabled until acknowledgement.
- Added regression coverage so missing-info actions are not rendered as checkboxes.

## Follow-Up Action Cockpit Pass

The next product issue was that the case page still exposed too much packet detail before making the reviewer's job clear. The page now starts with an `Action Cockpit` that shows the decision, next action, and owner. The case page then shows the reviewer brief, required vendor follow-up, internal review route, and editable `AI-Assisted Drafts`.

## Request Queue Recalibration

The later product issue was that the app still exposed a builder-centric split between sample review and upload modes. That has been corrected: the three exam cases now appear as seeded vendor requests in one queue, uploaded packages create new session request records, request rows open details, and request records can be deleted during the demo session.

The request detail view now leads with `Decision`, required vendor follow-up, internal route, and reviewer brief. Drafts, upload intake details, staged mapping, evidence, workflow, trace, and exports are behind disclosure so the first viewport is less noisy.

Detailed policy findings, evidence, workflow, trace, and export controls now live under `Audit details`. This preserves exam traceability without making the primary review path feel like a debug page.

## Final Assessment

The app now better matches the original exam objective: it produces a structured, evidence-backed recommendation for a human procurement owner. It is still a prototype, but the main path now reads as a decision-and-draft workflow instead of a collection of internal implementation artifacts.

## Verification

- `python3 -m compileall -q app.py vendor_agent tests scripts` passed.
- `python3 -m pytest -q` passed: 30 tests after the synthesis follow-up pass.
- `python3 -m vendor_agent.cli eval` passed: 3/3 cases.
- Local Streamlit browser smoke passed for dashboard, sample-case review, upload landing, and mobile dashboard.
- Browser checks confirmed the old sidebar mode/human-gate copy is absent, missing-info actions are not rendered as checkboxes, request details lead with `Decision`, `Required Vendor Follow-up`, `Internal Review Route`, and `Audit details`, and the local OpenAI mode renders `Synthesis source: gpt-4o-mini-2024-07-18`.
- Updated screenshot: `docs/assets/screenshots/productized-sample-case.png`.

Remaining product limitations:

- It does not persist reviewer decisions or assignments.
- It does not create tickets or send drafts.
- Uploaded support artifacts are recognized but not deeply extracted.
- The deployed app still needs a clean post-redeploy smoke from an authenticated reviewer browser after these local UX changes are pushed and redeployed.
