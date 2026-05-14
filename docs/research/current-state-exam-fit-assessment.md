# Current-State Exam Fit Assessment

## Bottom Line

Current submission readiness: 20%.

Design readiness: 80%.

Implementation readiness: 5%.

The work so far is strong as preparation: the repo is clean, the package is in the right place, the architecture direction is sound, the UX target is much sharper than the original memo, and the Kanban board gives us a credible build path.

It is not yet a viable take-home submission. The original exam asks for a working prototype or runnable repo, deployed somewhere others can use, with setup instructions, an architecture note, and productionization explanation. Right now we have a scaffold plus strong research docs. The core system does not parse files, run tools, produce a decision packet, expose human-in-the-loop controls, run evals, or deploy.

That is not a failure yet; it is the correct pre-build state. But the next work must be implementation, not more strategy.

## Exam Requirement Fit

| Exam requirement | Current status | Fit score | Assessment |
|---|---:|---:|---|
| Build a small AI agent prototype | Not met | 1/10 | `app.py` is a placeholder. No agent loop, deterministic pipeline, model call, or decision packet exists yet. |
| Realistic internal operations workflow | Strongly planned | 8/10 | The product framing as procurement triage is correct and matches the source package. |
| Read intake form, vendor email, quote, security questionnaire, contract excerpt | Not met | 0/10 | Source files are copied into `data/source-package`, but no parser exists. |
| Produce concise intake summary | Not met | 1/10 | Desired output is specified, but no generated summary exists. |
| Identify missing information | Planned | 3/10 | Missing docs are manually understood in research, but no automated missing-info check exists. |
| Check fit against internal policies | Planned | 3/10 | Policy-rule functions are specified, but not implemented. |
| Produce structured output | Planned | 3/10 | A target schema is described, but there is no `DecisionPacket` model or JSON output. |
| Include tools or function calls | Planned | 3/10 | Tool names and trace format are specified, but no tool functions or traces exist. |
| Embed human-in-the-loop controls and signoffs | Strongly designed, not implemented | 4/10 | UX spec has the right controls and language. The app does not implement them. |
| Working prototype or runnable repo | Not met | 1/10 | The app technically imports and displays a placeholder, but it does not do the exam task. |
| Deployed environment usable by others | Not met | 0/10 | Deployment strategy exists; no deployment exists. |
| README with setup instructions | Partially met | 3/10 | README has planned commands, but several commands point to modules that do not exist yet. |
| Short architecture note | Partially met | 6/10 | Strategy memo contains architecture guidance, but a reviewer-facing `ARCHITECTURE.md` should be created. |
| Brief productionization explanation | Partially met | 6/10 | Strategy memo has a good productionization section, but it should become a concise `PRODUCTIONIZATION.md`. |
| Practical execution over polish | Planned well, not executed | 4/10 | The plan is practical. Execution has not started. |

## Overall Quality By Dimension

### 1. Repository Setup

Score: 7/10.

What is good:

- The standalone repo is outside Career OS, which is the right confidentiality and sharing boundary.
- The repo is initialized on `main`.
- The original source package is present under `data/source-package`.
- `.gitignore`, `.env.example`, `requirements.txt`, `README.md`, and package directories exist.
- The Obsidian Kanban board provides a visible work breakdown.

What is weak:

- No initial commit yet.
- `requirements.txt` is broad and not yet tied to actual imports.
- The README lists commands that will fail once executed beyond `streamlit run app.py` because `vendor_agent.cli` does not exist.
- `app.py` is a placeholder rather than a vertical slice.

Fix:

- Build the vertical slice before committing or publishing.
- Keep the source package private.
- Replace planned README commands with verified commands once implemented.

### 2. Understanding Of The Exam

Score: 9/10.

The research correctly identifies the exam's real purpose:

- They are testing practical agent-building, not generic AI enthusiasm.
- The workflow is about procurement-owner triage, not autonomous vendor approval.
- The key product outcome is an auditable decision packet.
- The safest architecture is deterministic extraction and policy tooling first, LLM synthesis second.
- Human-in-the-loop is not decoration; it is a requirement.

This aligns well with Venkat's interview rubric: scalable systems, cross-functional filtering, and technical depth.

### 3. Architecture Strategy

Score: 8/10.

What is strong:

- App plus CLI plus eval harness is the right shape.
- Single orchestrated agent is better than a multi-agent swarm for this task.
- Deterministic rules for approvals, budget, risk, and missing documents are the right boundary.
- LLM should not decide Legal/Finance/Security routing.
- Evidence preservation and trace output are central, which is exactly what a human reviewer needs.
- Deployment and GitHub sharing strategy are sensible.

What needs tightening:

- The architecture is still prose, not code.
- There is no explicit module dependency graph.
- There is no documented schema versioning plan.
- There is no real trace implementation.
- There is no clear fallback path if LLM call is disabled, beyond the idea of deterministic fallback.

Fix:

- Create `ARCHITECTURE.md` from the strategy memo.
- Implement `schemas.py` first so every other module has a contract.
- Build deterministic output before integrating an LLM.

### 4. Product And UX Strategy

Score: 8.5/10.

This is the biggest improvement over the original strategy memo.

What is strong:

- The product is framed as a decision-support cockpit, not a chat interface.
- The first screen is defined around status, next actions, approval route, and evidence.
- The UX distinguishes procurement-owner needs from Jay/Venkat reviewer needs.
- Case-specific UX targets are clear, especially the need not to over-escalate Workspace Depot.
- Human approval gates are specific: draft labels, no send button, no approval language.
- Loading, empty, and error states are addressed.
- Accessibility and shared-screen readability are considered.

What is still weak:

- No actual rendered UI exists.
- The wireframe is text-only.
- There is no screenshot or Playwright/browser validation.
- There is no user-task checklist embedded in the app.

Fix:

- Implement a minimal Streamlit version that matches the spec.
- Run it locally and take screenshots during verification.
- Keep the interface operational and dense; avoid marketing-page styling.

### 5. Ingestion Plan

Score: 8/10 as a plan, 0/10 as implementation.

The ingestion plan is technically sound:

- Excel with `openpyxl`, using `Field Key`.
- Quote CSV with money normalization and line-item preservation.
- PDF extraction with page-level evidence.
- Markdown section parsing.
- Vendor email as untrusted evidence.
- Document checklist cross-checked against actual files.

The key missing implementation risk is PDF parsing. The provided PDFs are simple enough that `pypdf` will probably work, but the parser should fail loudly and include page evidence if a field cannot be extracted.

Fix:

- Implement parsers as pure functions.
- Add tests for one expected extracted fact per file type per case.
- Save source evidence IDs with every extracted field.

### 6. Policy And Tooling Plan

Score: 8/10 as a plan, 0/10 as implementation.

The proposed tools map well to the exam's process-flow image:

- `validate_required_documents`
- `lookup_budget`
- `check_existing_vendor`
- `calculate_total_contract_value`
- `classify_data_sensitivity`
- `determine_required_approvals`
- `draft_vendor_followup`
- `escalate_to_human`

The planned policy boundaries are correct. In particular, the tool should route and recommend, not approve.

Potential issue:

- Risk tier and approval routing can become ambiguous if we try to encode all policies perfectly. The correct prototype move is to encode the clear triggers in the provided docs and flag ambiguity explicitly.

Fix:

- Implement deterministic policy rules directly from the policy docs.
- Add an `evidence` list to every policy finding.
- Treat each rule as testable business logic.

### 7. Evaluation Plan

Score: 8/10 as a plan, 0/10 as implementation.

The eval direction is strong:

- Use the three provided cases as seed cases.
- Include deterministic hard checks for money math, missing docs, approvers, evidence, and prohibited actions.
- Include human/rubric checks for concise usefulness.
- Write reports to stable and timestamped paths.

The biggest gap:

- No `evals/seed-cases.json`, no baseline expected outputs, no runner, no tests.

Fix:

- Create baselines after deterministic pipeline works.
- Use evals before adding LLM synthesis, not after.
- Add a "false ready for approval" blocker as a hard fail.

### 8. Safety And Human-In-The-Loop

Score: 8/10 as design, 0/10 as implementation.

The design handles the major safety issues:

- Vendor docs are untrusted evidence.
- No external sending.
- No final approval.
- No spend commitment.
- No legal acceptance.
- Drafts require human approval.
- Trace/evidence supports auditability.

Missing implementation:

- No UI controls.
- No schema field such as `human_approval_required`.
- No tests verifying prohibited actions are absent.

Fix:

- Put `human_approval_required: true` into draft outputs.
- Add tests that fail if output contains final approval language.
- Avoid button labels that imply external actions.

### 9. Deployment And Submission

Score: 7/10 as a plan, 0/10 as execution.

The deployment plan is correct:

- Private GitHub repo.
- Streamlit Community Cloud as primary.
- Render as fallback.
- Secrets via deployment environment, not committed.

Missing:

- No remote GitHub repo.
- No deployed app.
- No verified dependency install.
- No README deployment section.

Fix:

- Do not deploy until the app actually handles all three cases.
- When ready, publish the repo for frictionless reviewer access after confirming no secrets or real vendor data are committed.
- Add a deployed URL and a "run locally" path.

## How Well It Addresses Venkat's Rubric

### AI-forward without shiny-object behavior

Current quality: strong.

The plan avoids unnecessary multi-agent architecture and avoids vector RAG for a tiny policy corpus. That restraint is a major positive signal. It shows the "what is real vs hype" judgment Venkat explicitly asked for.

Risk:

- If implementation adds a flashy LLM layer before deterministic checks, this advantage disappears.

### Cross-functional problem solving

Current quality: strong.

The product and policy framing covers Procurement, Finance, Legal, Security, Business Owner, and Executive Sponsor. The UX spec also separates findings by function, which makes the tool usable for each stakeholder.

Risk:

- If output becomes one generic AI summary, it will fail the cross-functional bar.

### Technical enough for Jay Shah panel

Current quality: good in plan, absent in code.

The planned architecture gives Jay good probe surfaces:

- parsers
- Pydantic schemas
- deterministic tools
- trace
- eval harness
- model fallback
- deployment path

But none of those exist in implementation yet.

Risk:

- A panel walkthrough of docs only would not be credible.

## What Would Be A Strong Final Submission

A strong submission would let Venkat or Jay do this:

1. Open deployed app.
2. Select `case_003`.
3. Click `Run triage`.
4. Immediately see:
   - `Blocked - high-risk AI/employee-data vendor`
   - ACV `$120,000`, TCV `$360,000`, one-time fees `$20,000`
   - Budget issue for `PEOPLE-010`
   - Required Legal, Security, Finance/CFO, Executive sponsor routing
   - Missing DPA, SOC 2 Type II, AI opt-out, SCIM answer
   - Evidence from intake, quote, contract, questionnaire, policies, budget CSV
5. Open `Evidence` tab and verify source snippets.
6. Open `Drafts` tab and see a safe vendor follow-up marked as draft.
7. Download `decision_packet.json` and `trace.json`.
8. Run `python -m vendor_agent.cli eval` locally and see passing results.

That would address the exam directly and create a strong panel conversation.

## Biggest Gaps To Close

Ordered by importance:

1. No working ingestion pipeline.
2. No schemas.
3. No deterministic policy tools.
4. No decision packet output.
5. No Streamlit triage experience.
6. No eval runner.
7. No tests.
8. No reviewer-ready README.
9. No architecture and productionization docs in final submission shape.
10. No deployment.

## Recommended Build Sequence

### Phase 1: Deterministic vertical slice

Goal: one command produces a correct JSON packet for one case.

Tasks:

- Implement `schemas.py`.
- Implement parsers for Excel, CSV, PDF, markdown, and text.
- Implement tools for budget, duplicate vendor, TCV, data sensitivity.
- Implement policy findings.
- Implement `DecisionPacket`.
- Run on `case_003` first because it exercises the most risk logic.

Acceptance:

- `python -m vendor_agent.cli run --case case_003` writes valid JSON.

### Phase 2: All cases and evals

Goal: all three cases produce expected packets and pass hard checks.

Tasks:

- Run all cases.
- Create expected baselines.
- Implement deterministic eval runner.
- Add pytest coverage.

Acceptance:

- `pytest` passes.
- `python -m vendor_agent.cli eval` passes.

### Phase 3: Streamlit UX

Goal: reviewer can use the prototype without reading code.

Tasks:

- Implement case selector.
- Implement run status.
- Implement overview metrics and next actions.
- Implement findings table.
- Implement evidence table.
- Implement drafts tab.
- Implement trace tab.
- Implement exports.

Acceptance:

- `streamlit run app.py` lets a reviewer triage all three cases.

### Phase 4: LLM synthesis

Goal: add value without giving the model policy authority.

Tasks:

- Add optional LLM-generated summary and draft follow-up.
- Validate output schema.
- Keep deterministic fallback.
- Mark generated fields clearly.

Acceptance:

- App still works without API key.
- Model output cannot override deterministic findings.

### Phase 5: Submission docs and deploy

Goal: reviewer-ready package.

Tasks:

- Write final README.
- Write `ARCHITECTURE.md`.
- Write `PRODUCTIONIZATION.md`.
- Add screenshots.
- Deploy privately.
- Add GitHub access instructions.

Acceptance:

- Fresh clone can run local app and evals from README.
- Deployed app URL works.

## Quality Risks

### Risk 1: Over-scoping the system

The strategy docs mention many good ideas. The final deliverable should not try to implement everything. The MVP is a vertical slice that handles three provided cases well.

Mitigation:

- No multi-agent framework until after deterministic pipeline is complete.
- No general file upload.
- No real integrations.
- No vector DB.

### Risk 2: UI that looks impressive but hides weak reasoning

An attractive Streamlit app can still fail if evidence is weak.

Mitigation:

- Evidence table is mandatory.
- Findings must cite source files.
- Trace output must be downloadable.

### Risk 3: Treating the LLM as the decision maker

This would be a serious product/safety failure.

Mitigation:

- LLM only synthesizes/drafts from deterministic findings.
- Tests check that policy outputs are deterministic.
- UI distinguishes deterministic findings from generated prose.

### Risk 4: Workspace Depot over-escalation

Case 002 is a restraint test. If the system treats it like case 003, the product judgment looks bad.

Mitigation:

- Low-risk renewal path should be clearly different.
- Missing setup docs should block readiness without triggering unnecessary Legal/Security review.

### Risk 5: README overpromises

The current README already lists commands that are not implemented yet.

Mitigation:

- Update README only with verified commands.
- Add "Current limitations" until final.

## Current Artifact Scores

| Artifact | Score | Notes |
|---|---:|---|
| `README.md` | 3/10 | Good orientation, but not final, not yet executable beyond placeholder app. |
| `kanban.md` | 8/10 | Useful work breakdown and Obsidian-compatible. Needs task sequencing by phase. |
| `docs/research/prototype-strategy-research.md` | 8/10 | Strong architecture and submission strategy. Too broad for final reviewer-facing doc. |
| `docs/research/prototype-strategy-review.md` | 8/10 | Honest and accurate critique of missing UX depth. |
| `docs/product/streamlit-product-ux-spec.md` | 8.5/10 | Strong product target. Needs implementation validation and screenshots later. |
| `app.py` | 1/10 | Placeholder only. |
| `requirements.txt` | 4/10 | Reasonable starter dependencies, but not verified against real implementation. |
| `data/source-package/` | 9/10 | Correct source package placement. Keep private. |

## Final Assessment

The work so far has done the right thinking before coding. It has converted a vague take-home into a clear product and architecture target:

- an internal procurement triage assistant;
- deterministic first;
- evidence-backed;
- human-gated;
- app plus CLI plus evals;
- private deployment;
- reviewer-friendly UI.

That is good product management and good technical framing.

The remaining risk is execution. The exam is not asking for a strategy memo. It is asking for a working prototype or runnable repo. From here, every additional planning artifact has diminishing returns unless it directly supports implementation.

The next best move is a deterministic vertical slice for `case_003`, then expand to all three cases, then put the Streamlit UI on top.
