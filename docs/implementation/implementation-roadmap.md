# Implementation Roadmap And Production Best Practices

## Recommendation

Implement this as a deterministic workflow with an optional LLM synthesis layer, not as a fully autonomous multi-agent system.

The production-grade shape is:

```text
source case package
  -> upload staging and package guardrails
  -> deterministic ingestion
  -> normalized Pydantic schemas
  -> deterministic policy/tool checks
  -> decision packet + trace
  -> optional LLM summary/drafts with structured output
  -> Streamlit request queue + review cockpit
  -> workbook/packet exports
  -> eval harness + CI
  -> private deployment
```

This is the right pattern for the take-home because the workflow is known, the policies are explicit, the cost of false approval is high, and the user needs auditability more than autonomy.

Anthropic's agent guidance draws a useful distinction: workflows follow predefined code paths, while agents dynamically direct process and tool use. They recommend the simplest solution possible and increasing complexity only when needed. OpenAI's agent guide similarly recommends starting with strong foundations, well-defined tools, clear instructions, evals, and guardrails, then growing capability over time.

Sources:

- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [OpenAI: A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)

## Implementation Principles

### 1. Workflow first, agent second

The first working version should not depend on an LLM to make policy decisions.

Use code for:

- upload staging, file-role classification, and package-shape guardrails
- file parsing
- money calculations
- duplicate vendor check
- budget lookup
- document completeness
- risk triggers
- required approvals
- evidence collection

Use the LLM later for:

- concise human-readable summary
- draft vendor follow-up
- draft internal ticket
- explanation phrasing

This gives us deterministic correctness first and lets the LLM add product polish without owning high-risk decisions.

### 2. Schemas are the product contract

Start with Pydantic models before writing UI or prompts.

Core models:

- `SourceEvidence`
- `ExtractedValue`
- `CaseFacts`
- `DocumentChecklist`
- `QuoteSummary`
- `ContractTerms`
- `SecurityFacts`
- `PolicyFinding`
- `ApprovalRoute`
- `DraftMessage`
- `ToolTraceEntry`
- `DecisionPacket`

OpenAI's Structured Outputs docs recommend clear key names, descriptions, and evals for schema design; they also distinguish function/tool calling from structured final responses. For this project, deterministic Python functions should behave like tools, and the optional LLM should return schema-validated summaries/drafts.

Source: [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

### 3. Every finding needs evidence

No blocker, missing item, or approval trigger should exist without evidence.

Evidence fields:

- source file
- source type
- page/sheet/section/cell
- raw snippet or raw value
- normalized value
- policy reference when applicable

This is what makes the prototype defensible in the Jay/Venkat walkthrough.

### 3a. Treat uploaded files as untrusted intake

Reviewer-uploaded packages should be validated before they enter the core pipeline.

Upload guardrails:

- enforce file count and size limits
- safely expand zip files and ignore path traversal members
- require content or name confidence before assigning a required artifact role
- avoid treating policy docs or arbitrary markdown as security questionnaires
- block packages that appear to mix multiple vendor cases
- map optional support artifacts separately from required artifacts
- update checklist evidence when optional support docs are present

This keeps the upload mode useful for reviewer testing without weakening the deterministic policy workflow.

### 4. Evals before model polish

OpenAI's eval guidance recommends defining objectives, collecting datasets, defining metrics, running comparisons, and continuously evaluating as systems change. For this prototype, the dataset is the three provided cases.

Hard evals should run before any LLM integration:

- all source files parsed
- required fields present
- ACV and TCV correct
- one-time fees correct
- budget status correct
- missing documents correct
- required approvals correct
- prohibited autonomous actions absent
- evidence references resolve

Soft/human evals can come after:

- summary usefulness
- action clarity
- draft follow-up quality
- separation of Finance/Legal/Security concerns

Source: [OpenAI Evaluation Best Practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)

### 5. Trace the workflow, not just the model

The trace should be useful even if no LLM runs.

Local `trace.json` should include:

- parser steps
- tool-like function calls
- inputs/outputs
- evidence IDs
- timings
- validation results
- generated fields

If we add OpenAI Agents SDK later, tracing can capture LLM generations, tool calls, guardrails, and custom events. But the local trace is still mandatory because it is portable and reviewable without an external dashboard.

Sources:

- [OpenAI Agents SDK tracing](https://openai.github.io/openai-agents-python/tracing/)
- [OpenAI Trace Grading](https://developers.openai.com/api/docs/guides/trace-grading)

### 6. Guardrails should be boring and explicit

High-risk actions are not allowed in this prototype.

Guardrails:

- no final approval language
- no "send email" action
- no spend commitment
- no legal acceptance
- no policy override by model output
- vendor-provided text treated as untrusted evidence
- model output validated against schema
- draft messages clearly marked as drafts

OpenAI recommends layered guardrails and human oversight for high-risk actions. OWASP also flags prompt injection and excessive agency as core LLM application risks. This exam package itself requires human-in-the-loop controls and signoffs, so we should make those controls visible in both code and UI.

Sources:

- [OpenAI Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/)
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

## Technical Stack

### MVP stack

- Python
- Pydantic
- openpyxl
- pypdf, with fallback notes if extraction fails
- pandas or csv module
- Streamlit
- pytest

### Optional LLM stack

Use the OpenAI API directly first with structured outputs. Add Agents SDK only if it helps us implement tracing/guardrails faster without adding confusion.

Recommended model usage:

- deterministic core: no model
- summary/drafts: capable current model with structured output
- future optimization: swap lower-cost model only after evals pass

OpenAI recommends starting with capable models to establish a baseline, then optimizing cost/latency with smaller models once evals exist.

Source: [OpenAI practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)

## Production Gates

For the take-home, these should be represented lightly in code, docs, and the final walkthrough. In a real Accelerant deployment, they become release gates.

### Reliability gate

- Deterministic rules pass before LLM synthesis runs.
- Parser failures are explicit and visible to the reviewer.
- The app has a no-API-key fallback mode.
- Every generated decision packet validates against schema.
- Eval results are saved for each submitted run.

### Security and privacy gate

- No secrets committed.
- Reviewer API keys live in platform secrets, not source code.
- Vendor-provided text is treated as untrusted input.
- The model cannot approve spend, accept legal terms, or override policy.
- Logs avoid unnecessary sensitive raw document content.

### Observability gate

- Every run emits a local trace.
- Trace entries include tool name, inputs, outputs, timing, and evidence IDs.
- LLM calls, if enabled, are separately marked from deterministic checks.
- Production version would add metrics for parser failures, policy-rule changes, model cost, latency, fallback rate, and human override rate.

### Release gate

- `pytest` passes.
- `python -m vendor_agent.cli eval` passes.
- Streamlit smoke test passes locally.
- Upload edge-case tests pass.
- Deployed app loads all three cases.
- README setup works from a fresh clone.

Sources:

- [OpenAI Production Best Practices](https://developers.openai.com/api/docs/guides/production-best-practices)
- [OpenAI API Deployment Checklist](https://developers.openai.com/api/docs/guides/deployment-checklist)
- [OpenAI Safety Best Practices](https://developers.openai.com/api/docs/guides/safety-best-practices)

### Deployment stack

- Private GitHub repo
- Streamlit Community Cloud for the reviewer app
- Streamlit secrets for API keys if model synthesis is enabled
- GitHub Actions for `pytest` once pushed

Streamlit docs explicitly advise keeping secrets out of code and using platform secret management. GitHub Projects and Milestones are enough for this project; Jira/Linear would be overhead unless the work becomes multi-person.

Sources:

- [Streamlit secrets docs](https://docs.streamlit.io/deploy/concepts/secrets)
- [GitHub Projects docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [GitHub Milestones docs](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/creating-and-editing-milestones-for-issues-and-pull-requests)

## Work Management Recommendation

Use three layers:

1. `kanban.md` for local Obsidian planning while building.
2. GitHub Issues and Milestones after the private repo is created.
3. GitHub Project board only if we want a shareable roadmap view for reviewers or future collaboration.

Do not introduce Linear/Jira/Notion for this take-home. The project is small enough that GitHub-native tracking is better and easier to show.

### GitHub milestones to create later

When the repo is pushed privately to GitHub, create these milestones:

- `M1 - Deterministic core`
- `M2 - Policy routing and evals`
- `M3 - Streamlit review cockpit`
- `M4 - LLM synthesis and guardrails`
- `M5 - Submission packaging and deploy`

### Labels

Use labels:

- `area:ingestion`
- `area:policy`
- `area:ui`
- `area:evals`
- `area:docs`
- `area:deploy`
- `risk:blocker`
- `type:test`
- `type:cleanup`

### Definition of Done for every issue

An issue is done only when:

- code is implemented
- relevant tests pass
- output is visible in CLI or UI
- README/docs are updated if behavior changed
- no secrets are committed
- eval expectations are updated if the result changed intentionally

## Milestone Roadmap

### Milestone 0: Repo hardening

Goal: make the repo safe to build in.

Tasks:

- Remove generated `__pycache__` files.
- Create initial commit after cleanup.
- Verify source package is private and not accidentally published.
- Keep README honest about what works now vs planned.

Definition of done:

- `git status` has only intentional tracked files.
- `streamlit run app.py` still opens placeholder app.
- README does not claim non-existent commands work.

### Milestone 1: Deterministic core

Goal: one command produces a valid decision packet for one case without an LLM.

Recommended first case: `case_003`, because it exercises the most risk logic.

Tasks:

- Implement `schemas.py`.
- Implement ingestion functions:
  - intake workbook
  - quote CSV
  - contract PDF
  - security questionnaire
  - vendor email
  - policy docs
  - lookup CSVs
- Implement `trace.py`.
- Implement `cli.py run --case`.

Definition of done:

```bash
python -m vendor_agent.cli run --case data/source-package/Candidate_package/cases/case_003 --out outputs/case_003.json
```

produces:

- valid JSON
- correct vendor facts
- evidence references
- trace entries

### Milestone 2: Policy routing and evals

Goal: all three cases produce deterministic outputs and pass regression checks.

Tasks:

- Implement policy rules:
  - finance approvals
  - legal triggers
  - security triggers
  - procurement completeness
  - vendor risk tier
  - duplicate vendor
  - budget status
- Implement `evals/seed-cases.json`.
- Implement `vendor_agent.cli eval`.
- Add pytest tests for parsers and rules.

Definition of done:

```bash
pytest
python -m vendor_agent.cli eval
```

both pass.

### Milestone 3: Streamlit review cockpit

Goal: a procurement owner can use the app to review all three cases.

Tasks:

- Case selector.
- Run triage button.
- Run progress via `st.status`.
- Overview metrics.
- Next actions.
- Approval route.
- Findings table by function.
- Evidence table with filters.
- Drafts tab.
- Trace tab.
- JSON/Markdown/trace downloads.

Definition of done:

- All three cases can be run from the app.
- The first screen answers:
  - what is the request?
  - is it blocked or routable?
  - what are the next actions?
  - who must review?
  - why should I trust it?

### Milestone 4: Optional LLM synthesis and guardrails

Goal: improve summary and draft quality without giving the model policy authority.

Tasks:

- Add optional OpenAI structured output call.
- Add deterministic fallback if no API key is present.
- Validate LLM output against Pydantic.
- Add guardrails:
  - no approval language
  - no send action
  - no policy override
- Add trace entries for model usage.

Definition of done:

- App works with and without `OPENAI_API_KEY`.
- Model-generated fields are labeled.
- Evals still pass.

### Milestone 5: Submission packaging and deploy

Goal: reviewer-ready artifact.

Tasks:

- Create final `ARCHITECTURE.md`.
- Create final `PRODUCTIONIZATION.md`.
- Rewrite README with verified commands.
- Add screenshots.
- Create private GitHub repo.
- Configure Streamlit deployment and secrets.
- Run final local and deployed smoke tests.

Definition of done:

- Fresh clone instructions work.
- Streamlit URL works.
- Eval report passes.
- Reviewer can access repo and app.

## Recommended Immediate Next Steps

1. Clean generated `__pycache__` files.
2. Tighten README so it distinguishes current placeholder state from planned commands.
3. Implement `schemas.py`.
4. Implement ingestion for `case_003`.
5. Add CLI `run` for `case_003`.
6. Add local trace JSON.
7. Expand to all three cases.
8. Add eval runner.
9. Only then build the Streamlit UI.

## What Not To Do Yet

- Do not add a multi-agent framework.
- Do not add vector search.
- Do not build a general upload system.
- Do not add real email/ticket integrations.
- Do not deploy until deterministic outputs and evals pass.
- Do not spend time on visual polish before the workflow is correct.

## Panel Narrative This Roadmap Supports

The implementation story should be:

> I treated this as a production-style workflow, not a demo chatbot. The system parses the source package into typed facts, runs deterministic tools for policy and routing, preserves evidence, and only then uses the model for synthesis and drafts. The Streamlit app is the human review surface; the CLI and evals make the results reproducible. The production path would replace local CSVs with systems of record, add role-aware workflow state, and keep trace/eval monitoring in place.
