# LLM Synthesis Assessment

## Recommendation

Do not move the prototype's decision logic into an LLM before submission.

The correct architecture is:

1. Parse source files into typed facts.
2. Run deterministic tools and policy checks.
3. Emit a schema-validated decision packet with evidence and trace.
4. Optionally ask an LLM to synthesize reviewer-facing text from that packet only.
5. Validate the LLM output before showing it, and keep the deterministic packet visible as the source of truth.

This keeps the exam response defensible: the system can explain why a case is blocked, which policy triggered, which evidence supports the finding, and which human route is required. An LLM can improve readability, but it should not own approval, risk, routing, or blocker decisions.

## What An LLM Should Add

Good candidates for optional synthesis:

- Executive summary rewritten for a procurement owner.
- Vendor follow-up draft that combines missing information into a concise email.
- Internal approval note that summarizes blockers and required reviewers.
- Plain-English explanation of the trace for a non-technical reviewer.
- Possible uploaded-file role hints, as long as deterministic validation still confirms required artifacts.

These are user-experience improvements. They make the packet easier to act on without changing the packet's facts or conclusions.

## What An LLM Must Not Do

The LLM must not:

- decide risk tier
- decide budget status
- decide required approvals
- remove blockers
- mark a case ready
- accept contract terms
- approve spend
- send vendor communications
- invent evidence
- cite evidence IDs that do not exist in the decision packet

This is especially important because vendor-provided emails, questionnaires, and contracts are untrusted input. A prompt-injection phrase in a vendor document should never be able to bypass procurement, finance, security, or legal rules.

## Proposed Contract

If synthesis is added, create a separate object such as `SynthesisBundle`:

```text
SynthesisBundle
- case_id
- model_name
- generated_at
- executive_summary
- vendor_follow_up_draft
- internal_note_draft
- cited_evidence_ids
- validation_status
- validation_errors
```

The LLM input should be a compact, structured view of `DecisionPacket`, not raw uploaded documents by default. The output should be rejected if:

- cited evidence IDs are not present in `DecisionPacket.evidence`
- it changes status, risk, budget, approval route, or missing information
- it uses prohibited approval or commitment language
- required fields are missing
- the JSON/schema validation fails

## UI Placement

The Streamlit app should keep deterministic output first:

- Overview, findings, evidence, and trace remain deterministic.
- LLM content appears in a clearly labeled section such as `LLM-assisted draft`.
- The UI should show model name, generation time, and validation status.
- Human reviewers should be able to ignore the generated text and still complete review from deterministic outputs.
- No generated draft should be sent from the app.

## Eval Plan

Before enabling synthesis by default, add evals that run against the three seed cases:

- Schema validity: every generation conforms to `SynthesisBundle`.
- Evidence integrity: every citation exists in the packet.
- Decision preservation: generated text does not alter status, risk, budget, blockers, or route.
- No agency breach: generated text does not approve, commit spend, accept terms, or say a blocker is resolved.
- Actionability: vendor draft lists the same missing information as the deterministic packet.
- Regression trigger: any prompt, model, parser, policy, or schema change must rerun the synthesis evals.

The deterministic eval remains the release gate. LLM evals become an additional gate only if synthesis is enabled.

## Deployment Implications

The app should continue to work without an LLM key. If synthesis is added:

- keep `OPENAI_API_KEY` optional
- configure it through Streamlit secrets, not source code
- hide the synthesis panel when no key is present
- fail closed if validation fails
- never persist uploaded raw documents in model logs or broad app logs

## Final Assessment

For the take-home, the deterministic system is the right default. It demonstrates product judgment and production judgment: evidence first, traceability, human-in-the-loop routing, reproducible evals, and no autonomous approvals.

LLM synthesis makes sense as a follow-on enhancement, but only behind the structured validation and eval harness already in the repo.
