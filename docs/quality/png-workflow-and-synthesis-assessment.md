# Process Flow PNG And Synthesis Assessment

Date: 2026-05-13

## Source Workflow Assessment

The provided PNG describes a vendor onboarding triage workflow:

| PNG stage | Current implementation | Assessment |
| --- | --- | --- |
| Start: vendor onboarding case package | Dashboard sample cases plus `Triage new package` mode | Covered |
| Parse and extract inputs | Intake workbook, vendor email, quote CSV, security questionnaire, contract PDF, policy docs, budget and vendor-register data | Covered |
| Validate package | Required upload artifacts and case inventory validation | Covered |
| Complete enough for triage? | Upload mode blocks missing core files; packet status and open requests show not approval-ready cases | Covered, but production would need persisted reviewer correction state |
| Identify missing or incomplete items | `missing_information` plus `Required Follow-up` UI | Covered |
| Draft vendor follow-up | Drafts tab and synthesis follow-up draft, both human-gated | Covered |
| Escalate to human | `Human Review Route`, prohibited actions, and draft acknowledgement | Covered |
| Normalize case facts | `CaseFacts` typed object | Covered |
| Run deterministic helper tools | Budget lookup, duplicate vendor check, TCV, data sensitivity | Covered |
| Determine approvals and risk tier | Policy findings and approval route | Covered |
| Prepare outputs | JSON packet, trace, Markdown brief, XLSX workbook, reviewer synthesis | Covered |
| Human approval gate | UI states routing recommendation only; no approval/send action | Covered |
| End: decision packet ready for routing | Exportable packet and reviewer route | Covered |

The current build is on track with the PNG. The main remaining gap is not a missing algorithmic step; it is workflow state. In production, the app would persist the human owner's edits, signoffs, assignments, and final routing decisions.

## LLM Synthesis Assessment

The PNG does not explicitly require an LLM. It names deterministic helper tools and draft/output generation. However, LLM synthesis is a good fit inside the `Prepare outputs` layer because the reviewer needs a digestible summary and draft language.

The safe boundary is:

1. Parse and validate files first.
2. Run deterministic policy and tool checks.
3. Produce the evidence-backed `DecisionPacket`.
4. Generate reviewer-facing synthesis from that packet only.
5. Validate synthesis before showing it.

The LLM must not determine risk, budget, missing information, required approvals, approval status, legal acceptance, spend commitment, or external sending.

## Implemented This Pass

- Added `SynthesisBundle` to the packet schema.
- Added `vendor_agent.synthesis` with deterministic packet-grounded synthesis and validation.
- Added a compact `build_llm_synthesis_payload()` for optional OpenAI synthesis; it excludes raw source documents by default.
- Added `prepare_reviewer_synthesis` to the trace.
- Added `Reviewer Brief` to the Overview tab.
- Added synthesis output to Markdown and workbook exports.
- Added regression tests for grounded synthesis, evidence citations, missing-info preservation, and payload boundaries.

This remains deterministic-safe. The repository still works without `OPENAI_API_KEY`; when `OPENAI_SYNTHESIS_PROVIDER=openai` and a key are configured, the provider uses structured output and falls back if validation fails.

## Recommendation

The optional OpenAI-backed synthesis provider now exists behind the `SynthesisBundle` contract. The next production step is to add deployed Streamlit secrets and broaden synthesis eval cases before relying on it in front of reviewers.

Keep deterministic evals as the release gate. Add synthesis evals only when the live provider is enabled:

- schema validity
- evidence ID integrity
- missing-information preservation
- no approval/spend/terms/send language
- no changes to risk, budget, status, or approval route

## Verification

- `python3 -m compileall -q app.py vendor_agent tests scripts` passed.
- `python3 -m pytest -q` passed: 30 tests.
- `python3 -m vendor_agent.cli eval` passed: 3/3 cases.
- `git diff --check` passed.
- Local Streamlit browser smoke confirmed `Reviewer Brief`, `Synthesis validation`, `Required Follow-up`, and `Triage Workflow` render, with old sidebar implementation copy still absent.
