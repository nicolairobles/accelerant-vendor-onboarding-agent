# Productionization Plan

## Production Goal

Turn the prototype into an internal procurement triage service that helps human owners review vendor onboarding requests faster without reducing approval rigor.

## System Of Record Integrations

Prototype files would be replaced by controlled integrations:

- Intake source: procurement intake form, ticket, or workflow system.
- Vendor registry: ERP, procurement platform, or vendor master.
- Budget lookup: finance planning system or ERP.
- Contracts: CLM/document repository.
- Security materials: GRC or vendor-risk platform.
- Approvals: workflow/ticketing system with role-aware signoffs.

The decision packet should remain the interface contract between the workflow engine and any UI or downstream system.

## Controls And Guardrails

Production controls should include:

- role-based access to vendor packets
- no autonomous approval or external send actions
- explicit human signoff states
- immutable audit log for packet generation and human overrides
- policy version attached to each run
- evidence references for every blocker and route trigger
- model-generated fields clearly labeled if LLM synthesis is added
- schema validation before any packet is shown or exported

## Evaluation And Regression

The current `python3 -m vendor_agent.cli eval` command should become a CI gate.

Production evals should include:

- seeded historical cases
- edge cases for low-risk vendors
- edge cases for duplicate vendors
- high-risk AI/data-processing vendors
- budget shortfall cases
- missing document cases
- legal term triggers
- negative tests proving the system does not approve, send, or override policy

Metrics to track:

- eval pass rate
- parser failure rate
- missing-evidence rate
- human override rate
- false blocker rate
- missed blocker rate
- time to triage
- model cost and latency if LLM synthesis is added

## Observability

Every production run should emit:

- run ID
- case/vendor ID
- policy version
- tool calls
- parser status
- evidence IDs
- decision status
- approval route
- validation result
- human override events
- latency and error metrics

The local `trace` structure in this prototype is the seed for that audit log.

## Security And Privacy

Vendor onboarding packages can contain confidential commercial terms, personal data, security questionnaires, and contract language.

Production should enforce:

- least-privilege access
- encryption in transit and at rest
- secret management through platform secrets
- no raw sensitive content in broad application logs
- retention policy for generated packets and traces
- prompt-injection handling if LLM synthesis is added
- review of vendor-provided text as untrusted input

## LLM Addition Path

If an LLM is added, it should be limited to:

- concise summary phrasing
- draft vendor follow-up
- draft internal ticket/note
- reviewer-friendly explanation of deterministic findings

The LLM must not:

- decide risk tier
- decide required approvals
- mark a case ready
- remove blockers
- approve spend or contract terms
- send communications

Implementation guardrails:

- pass only normalized facts/evidence, not arbitrary raw documents where possible
- require structured output
- validate output with Pydantic
- reject outputs that contain approval/send/commitment language
- compare output quality with evals before switching models or prompts

## Deployment Path

Submission deployment:

1. Keep repo private.
2. Verify `python3 -m pytest -q`.
3. Verify `python3 -m vendor_agent.cli eval`.
4. Deploy Streamlit app privately.
5. Configure secrets only if LLM synthesis is added.
6. Smoke test all three sample cases in the deployed app.
7. Smoke test upload mode with a zip and with missing-file validation.

Production deployment:

1. Containerize the service.
2. Split parser/policy/eval code from UI runtime.
3. Add CI for tests, evals, type/lint checks, and secret scanning.
4. Add environment-specific config for integrations.
5. Add audit-log persistence.
6. Add human approval workflow integration.
7. Add monitoring dashboards and regression alerts.

## Known Prototype Limits

- Source package format is synthetic and stable.
- Upload mode supports packages that contain the same file types and schema shape as the exercise cases.
- Policy logic is Python-coded rather than managed through a policy admin surface.
- Streamlit is acceptable for the take-home but not the final enterprise workflow UI.
- Eval dataset has three cases only.
- No LLM synthesis is included yet.
- No external system writes are implemented, by design.
