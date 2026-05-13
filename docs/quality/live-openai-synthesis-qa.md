# Live OpenAI Synthesis QA

Date: 2026-05-13

## Scope

This QA pass covered the optional live OpenAI synthesis provider added behind the validated `DecisionPacket`.

The provider is used only for reviewer-facing text:

- executive reviewer brief
- vendor follow-up draft
- internal routing note

It does not decide status, risk tier, budget status, missing information, approval route, legal acceptance, spend commitment, or external send behavior.

## Key Design Checks

- Live provider is opt-in through `OPENAI_SYNTHESIS_PROVIDER=openai`.
- API key is read from environment or platform secrets, never source code.
- Normal tests and deterministic evals run without the API key.
- OpenAI output must conform to `SynthesisDraft`.
- Output is converted to `SynthesisBundle`.
- Evidence IDs must exist in the deterministic packet.
- Missing information must be preserved.
- Approval, spend, terms-acceptance, and external-send language is rejected.
- Provider failures or validation failures fall back to deterministic synthesis.

## Issues Found And Fixed

1. Live smoke produced valid structured output, but one generation failed post-validation because missing-item wording could drift.
   - Fix: strengthened the system instruction to require exact `expected_missing_items` values in the vendor follow-up draft.
   - Fix: added `expected_missing_items`, `known_evidence_ids`, and explicit validation requirements to the compact LLM payload.
   - Fix: set `temperature=0`.
   - Fix: added fail-closed fallback if OpenAI output validates as failed.

2. Docs still described synthesis as future-only.
   - Fix: updated README, architecture, productionization notes, requirements, and acceptance matrix to reflect the optional live provider.

## Verification

- `python3 -m compileall -q app.py vendor_agent tests scripts` passed.
- `python3 -m pytest -q` passed: 32 tests.
- `python3 -m vendor_agent.cli eval` passed: 3/3 cases.
- Live OpenAI smoke passed for `case_003`:
  - mode: `openai_responses_structured_output`
  - model: `gpt-4o-mini-2024-07-18`
  - validation: `passed`
  - vendor follow-up includes human-review language
  - cited evidence IDs returned
- Browser smoke passed with Streamlit running in live-provider mode:
  - dashboard rendered `Open Requests`
  - sample case rendered `Reviewer Brief`, `Required Follow-up`, `Human Review Route`, and `Triage Workflow`
  - old implementation-mode sidebar copy and inert missing-item checkboxes were absent

## Remaining Deployment Note

The local key is stored in ignored `.env.local`. Streamlit Community Cloud will need the same values configured as app secrets before deployed live synthesis runs:

```text
OPENAI_API_KEY = "..."
OPENAI_SYNTHESIS_PROVIDER = "openai"
OPENAI_SYNTHESIS_MODEL = "gpt-4o-mini-2024-07-18"
```

The key value should be copied through Streamlit's secrets UI, not committed to the repository.
