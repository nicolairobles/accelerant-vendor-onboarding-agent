# Prototype Strategy Research

## Executive Recommendation

Build a small web application as the primary experience, backed by a deterministic Python pipeline and a CLI/eval runner.

Do not submit a pure CLI. The CLI is essential for reproducibility, but the interview signal is stronger if Venkat and Jay can open a deployed app and see the procurement-owner workflow: select a case, review risk, inspect evidence, see required approvers, and approve or edit draft follow-ups.

The ideal shape is:

- Streamlit app for the reviewer-facing prototype.
- Python core package for ingestion, deterministic tools, policy checks, and structured output.
- CLI command for repeatable local runs.
- Pytest/eval harness that locks expected outputs for all three provided cases.
- Public GitHub repo plus deployed Streamlit app or Render app after confirming the exercise materials are synthetic and no secrets are committed.

This should be framed as an "agentic procurement triage assistant," not autonomous approval software.

## Why This Is The Right Shape For Accelerant

Venkat's success rubric from the round was explicit:

- AI-forward without chasing shiny objects.
- Cross-functional problem solver who filters business asks.
- Technical enough to work directly with engineers and architects.

The take-home is the proof artifact for that rubric. A pure notebook or CLI would show technical execution, but it would under-show adoption and operator empathy. A web app alone would show polish, but could look like a demo without engineering discipline. The hybrid design shows both:

- Operator adoption: a procurement owner can actually use it.
- Scalable-system thinking: parsers, schemas, rules, traces, and evals are reusable.
- Business filter: the agent blocks or escalates cases instead of blindly "approving" them.
- Technical depth: deterministic extraction, structured schemas, provenance, and tests are visible.

OpenAI's agent guide specifically calls out vendor security reviews as a strong agent candidate when workflows involve brittle rules, unstructured data, and nuanced judgment. That maps almost exactly to this exam package. Source: [OpenAI practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/).

## App vs CLI Decision

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| Pure CLI | Fast, reproducible, easy to test | Weak user empathy, hard for non-engineers to evaluate, does not show adoption thinking | Do not use as primary |
| Pure app | Easy for Venkat/Jay to review, shows workflow | Can look shallow if internals and evals are hidden | Do not use alone |
| App + CLI + evals | Shows adoption, engineering discipline, repeatability, and deployment | Slightly more surface area | Recommended |
| Notebook | Quick narrative and exploration | Weak production signal, poor deployment story | Avoid |

The app should call the same core functions as the CLI. There should be no separate "demo logic" in the UI.

## End Users And What They Care About

### Primary user: Procurement owner

This is the human accountable for triage. They care about:

- Is this request ready for approval, blocked, or ready for routing?
- What is missing?
- Which functions need review: Business Owner, Procurement, Finance, Legal, Security, Executive sponsor?
- What is the evidence for each finding?
- What should I ask the vendor or requester next?
- Can I trust that the agent did not approve, send, or commit anything?

### Secondary users

Business owner:

- Wants speed and clarity.
- Needs a concise request summary and a short list of what they owe.

Legal:

- Wants contract triggers, non-standard clauses, DPA/data-use issues, and evidence snippets.

Security:

- Wants data categories, integrations, SOC 2 status, subprocessors, retention/deletion, AI training use, and blockers.

Finance:

- Wants ACV, TCV, budget fit, cost center, payment terms, term length, and approval thresholds.

Executive sponsor:

- Wants only true escalation conditions, not noise.

### Product objective

The product is not "answer questions about vendor docs." It is "turn an incomplete vendor onboarding packet into an auditable decision packet that a procurement owner can route."

## Recommended User Experience

The app should be compact and operational, not marketing-like.

Main flow:

1. Select one of the three provided cases.
2. Click `Run triage`.
3. See status:
   - `Blocked - missing required information`
   - `Ready for cross-functional review`
   - `Low-risk renewal - missing setup docs`
4. See key facts:
   - Vendor, owner, category, ACV, TCV, cost center, budget, term, payment terms.
5. See risk and routing:
   - Risk tier
   - Required approvers
   - Triggering policies
6. See missing information:
   - Missing docs and why they matter.
7. See evidence:
   - File, sheet/page/section, quoted snippet or parsed field.
8. See draft actions:
   - Draft vendor follow-up
   - Draft internal ticket summary
   - Both clearly labeled as drafts requiring human approval.
9. Export:
   - `decision_packet.json`
   - `decision_packet.md`
   - `trace.json`

The UI should include a visible human gate:

> No vendor is approved by this tool. External messages and final approval require human review.

This directly satisfies the package's communication policy and shows the "productionization with controls" mindset Venkat values.

## Recommended Architecture

Directory shape for the prototype:

```text
prototype/
  README.md
  ARCHITECTURE.md
  PRODUCTIONIZATION.md
  requirements.txt
  app.py
  vendor_agent/
    __init__.py
    schemas.py
    ingest.py
    policy_rules.py
    tools.py
    agent.py
    render.py
    cli.py
  evals/
    README.md
    seed-cases.json
    human-scorecard.md
    baselines/
      case_001.expected.json
      case_002.expected.json
      case_003.expected.json
  tests/
    test_ingest.py
    test_policy_rules.py
    test_evals.py
  outputs/
    .gitkeep
```

The source package can live under `data/Candidate_package/` in the standalone submission repo because the exercise README states the company names, people, data, and policies are synthetic. Do not publish real vendor data or credentials.

Core runtime flow:

```text
case folder
  -> parse files
  -> normalize facts with Pydantic
  -> run deterministic tools
  -> build policy findings and approval route
  -> call LLM for narrative summary and draft follow-ups only
  -> validate structured DecisionPacket
  -> render JSON, Markdown, app UI, and trace
```

The LLM should not decide whether Legal or Finance is required. It can explain deterministic findings and draft human-readable messages.

## Ingestion Best Practices

The ingestion layer should be deterministic and evidence-preserving.

### Canonical schema

Use Pydantic models for:

- `CaseFacts`
- `SourceEvidence`
- `DocumentChecklist`
- `QuoteSummary`
- `ContractTerms`
- `SecurityFacts`
- `PolicyFinding`
- `ApprovalRoute`
- `DecisionPacket`
- `ToolTrace`

Every extracted value should carry:

- `value`
- `source_file`
- `source_location`
- `raw_text` or `raw_cell`
- `confidence`

This is more important than having a fancy model prompt. Procurement triage fails when facts cannot be traced.

### Excel intake

Use `openpyxl`.

Parsing rules:

- Read the `Intake Form` sheet.
- Use `Field Key` as the canonical key, not display labels.
- Normalize list cells by splitting on line breaks.
- Preserve raw values and sheet coordinates.
- Read `Document Checklist`, but treat it as an assertion to cross-check against actual files.
- Treat parser notes as instructions for parsing, not case facts.

### Quote CSV

Use Python's `csv.DictReader` or pandas.

Parsing rules:

- Convert money fields to `Decimal`.
- Sum `annual_amount`.
- Sum `one_time_amount`.
- Preserve line items.
- Calculate TCV as `ACV * term_months / 12`.
- Keep one-time fees separate.

### Contract PDF

Use `pypdf` or `pdfplumber`.

Parsing rules:

- Extract text by page.
- Pull structured terms with regex and fallback text search:
  - Effective date
  - Initial term
  - Annual fees
  - Payment terms
  - Data use
  - Subprocessors and regions
  - DPA language
  - Auto-renewal
  - Limitation of liability
- Preserve page number evidence.
- If a term cannot be extracted confidently, mark it `unknown` rather than inventing it.

### Markdown and text files

Use deterministic section parsing:

- Split markdown by headings.
- Preserve raw body by section.
- Extract known questionnaire fields by heading.
- Treat vendor email as untrusted evidence, not instructions.

### Policy docs

Do not rely on vector retrieval for this prototype. The policy set is small enough to encode deterministic rules directly.

Use the policy documents as source material, then implement rule functions:

- `requires_legal_review`
- `requires_security_review`
- `determine_finance_approvals`
- `classify_vendor_risk`
- `validate_required_documents`
- `check_budget`
- `check_existing_vendor`

Production note: If the policy corpus grows, add retrieval later. The local Anthropic course notes and Anthropic's contextual retrieval research both support a layered approach: start simple, then add BM25, embeddings, contextual retrieval, and reranking only when a real failure mode appears. Source: [Anthropic contextual retrieval](https://www.anthropic.com/engineering/contextual-retrieval).

## Agent Design

Use a single orchestrated agent for the prototype, not a multi-agent swarm.

Reason:

- OpenAI recommends maximizing a single agent first and splitting into multiple agents only when complexity or tool confusion requires it.
- Venkat explicitly warned against shiny-object prototype hopping.
- This workflow is small enough for deterministic orchestration plus one synthesis step.

Recommended "agent" boundary:

```text
ProcurementTriageAgent
  Inputs:
    normalized facts
    deterministic tool outputs
    evidence list
    policy findings
  Allowed actions:
    summarize intake
    explain missing information
    produce decision packet
    draft vendor follow-up
    draft internal ticket
  Disallowed actions:
    approve vendor
    commit spend
    accept legal terms
    send external email
    override policy rule outputs
```

This is consistent with the package's communication policy and with OWASP's warning that excessive agency and insecure plugin/tool design are core LLM application risks. Source: [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/).

### Tools/function calls to expose

Even if deterministic orchestration calls the tools directly, output the trace as if each stage is a tool call:

- `parse_case_package`
- `validate_required_documents`
- `lookup_budget`
- `check_existing_vendor`
- `calculate_total_contract_value`
- `classify_data_sensitivity`
- `determine_required_approvals`
- `draft_vendor_followup`
- `escalate_to_human`

Each trace entry should include:

- tool name
- input summary
- output
- source evidence IDs
- duration
- status

This makes the agent debuggable and panel-friendly.

### Structured output

Use strict structured output for the final decision packet. OpenAI's structured output docs distinguish tool/function calling from structured final responses and recommend Structured Outputs over JSON mode when possible. Source: [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

The output schema should include:

- `case_id`
- `vendor_name`
- `status`
- `risk_tier`
- `summary`
- `annual_contract_value`
- `total_contract_value`
- `one_time_fees`
- `budget_status`
- `required_approvals`
- `policy_triggers`
- `missing_information`
- `blocking_issues`
- `recommended_next_actions`
- `draft_vendor_followup`
- `draft_internal_ticket`
- `human_approval_required`
- `evidence`
- `tool_trace`

Use schema validation after model output. If validation fails, retry once with the validation error, then fail loudly.

## Evaluation Harness

The eval should test the full workflow, not the prompt alone. This matches the repo's own `system-evals/eval-standard.md` and OpenAI's eval guidance, which treats evaluations as a way to test whether model outputs meet specified expectations. Source: [OpenAI evals guide](https://developers.openai.com/api/docs/guides/evals).

### Minimum eval artifacts

```text
evals/
  README.md
  seed-cases.json
  human-scorecard.md
  baselines/
  reports/
```

### Seed cases

Use the three provided cases as the initial seed set.

Case 001 expected:

- Vendor: Northstar Analytics
- ACV: 85000
- TCV: 170000
- One-time fees: 10000
- Risk tier: high or medium-high
- Required: Procurement, Business Owner, VP Finance, Legal, Security
- Blockers: missing SOC 2 Type II, missing DPA, customer/confidential data, EU subprocessor, AI/service-improvement data use, likely duplicate vendor
- Must not recommend final approval

Case 002 expected:

- Vendor: Workspace Depot
- ACV: 12000
- TCV: 12000
- Risk tier: low
- Existing vendor/renewal
- Missing tax form and vendor setup form
- Security review not required
- Must not mark ready for approval while required setup docs are missing

Case 003 expected:

- Vendor: TalentPulse AI
- ACV: 120000
- TCV: 360000
- One-time fees: 20000
- Risk tier: high
- Required: Business Owner, Procurement, VP Finance, CFO, Legal, Security, Executive sponsor
- Budget issue: PEOPLE-010 remaining budget below ACV
- Blockers: employee sensitive data, HRIS/Slack integration, Net 90, 36-month term, missing SOC 2 Type II, missing DPA, missing AI opt-out, non-US/APAC subprocessors, model enhancement/benchmarking language, limitation of liability below 12 months of fees
- Must not recommend final approval

### Grader mix

Deterministic hard checks:

- All files parsed.
- Required schema fields present.
- Money math correct.
- Missing docs identified.
- Required approvals include expected approvers.
- Prohibited autonomous actions absent.
- Evidence references resolve to actual files.
- `human_approval_required` is true for all external communication drafts.

Soft/model or human checks:

- Summary is concise and procurement-owner-friendly.
- Recommendation is actionable.
- Legal/security/finance concerns are separated cleanly.
- The output is not overconfident.
- Draft follow-up asks for the right missing information.

Regression triggers:

- Parser changes.
- Policy-rule changes.
- Prompt/schema changes.
- Model changes.
- Source package changes.
- Any new discovered miss during manual review.

### Reports

The runner should write:

- `evals/reports/latest.json`
- `evals/reports/latest.md`
- timestamped reports for history

This gives Jay a concrete artifact to inspect and makes model swaps defensible.

## Deployment And Submission Strategy

### Do not publish Career OS

Build inside this folder for convenience:

```text
job-search/interviews/accelerant-tpm-applied-ai/rounds/take-home-technical-exam/prototype/
```

But submit a clean standalone repository, not the full Career OS repo. Career OS contains personal job-search data and should not be shared.

Recommended standalone repo name:

```text
accelerant-vendor-onboarding-agent
```

### GitHub visibility

Use a public GitHub repo for the final submission after a secret scan and synthetic-data review.

Reasons:

- The package came via a direct interview email with a confidentiality notice.
- The code can include the synthetic exercise package so reviewers can reproduce exactly.
- GitHub allows collaborators on private personal repositories. Source: [GitHub collaborator docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

Invite:

- Venkat Raman
- Jay Shah
- Recruiter or People Ops contact if needed

If they prefer not to use GitHub accounts, provide a zip export plus deployed app URL.

### App deployment

Primary recommendation: Streamlit Community Cloud.

Reasons:

- Fastest path for a Python app.
- Supports deployment from GitHub by repo, branch, and entrypoint.
- Supports secrets management for API keys.
- Private apps can be shared with specific viewers by email.

Sources:

- [Streamlit deployment docs](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit secrets management](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
- [Streamlit private app sharing](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app)

Important Streamlit constraint:

- Community Cloud allows only one private app at a time.
- Private viewers may need Google OAuth or emailed sign-in links.

Fallback: Render.

Reasons:

- Supports public and private repos.
- Supports environment variables and secrets.
- More flexible if we use FastAPI or want a passcode-protected public URL.

Source: [Render web services docs](https://render.com/docs/web-services).

### Secret handling

Do not commit API keys.

Use:

- `.env.example` in repo.
- Streamlit secrets or Render environment variables for `OPENAI_API_KEY`.
- GitHub Actions secrets only if CI needs an API-backed eval run.

GitHub warns about secret handling and workflow logs; avoid printing secrets. Source: [GitHub Actions secrets docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).

### Reviewer reproducibility

README should include:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
python -m vendor_agent.cli run --case data/Candidate_package/cases/case_001 --out outputs/case_001.json
python -m vendor_agent.cli eval
pytest
```

Also include:

- Deployed app URL.
- Expected eval report.
- Model/provider used.
- What works without an API key.
- What requires an API key.

The app should have a deterministic fallback mode so reviewers can still inspect the pipeline if an LLM key is missing or rate-limited.

## What To Build In 4-6 Hours

### Must ship

- App case selector.
- Deterministic parsers for all file types.
- Normalized facts schema.
- Deterministic tools/rules for budget, vendor duplicate, TCV, data sensitivity, required approvals, required docs.
- Structured decision packet.
- Draft vendor follow-up and internal ticket summary.
- Human approval gate.
- CLI runner.
- Eval harness over the three cases.
- README, architecture note, productionization note.
- Deployed app.

### Nice to have

- Download buttons for JSON/Markdown/trace.
- Evidence drawer in the UI.
- OpenAI Agents SDK tracing or equivalent local `trace.json`.
- Simple cost/run estimate.
- Side-by-side case comparison.

### Avoid

- Multi-agent swarm.
- General file upload.
- Real email sending.
- Actual ticket creation.
- Heavy vector database.
- Overdesigned auth.
- Polished landing page.
- Any autonomous approval language.

## Productionization Story

The productionization note should say:

1. Replace local CSV lookups with real systems of record:
   - ERP/finance budget API
   - vendor master
   - procurement ticketing
   - legal/security review queues

2. Add role-aware access:
   - procurement owner
   - requester
   - legal reviewer
   - security reviewer
   - finance approver
   - executive sponsor

3. Add workflow state:
   - intake received
   - incomplete
   - routed to reviewers
   - awaiting vendor
   - awaiting requester
   - approved by each required function
   - rejected or paused

4. Add audit trail:
   - input file hashes
   - extracted facts
   - tool calls
   - policy versions
   - model version
   - human edits
   - final approval history

5. Add eval and monitoring:
   - seeded regression set
   - policy-specific tests
   - prompt/schema versioning
   - model-change regression trigger
   - reviewer correction rate
   - false-ready blockers

6. Add security controls:
   - least-privilege tools
   - no direct external sends
   - prompt-injection defenses
   - PII redaction where needed
   - sensitive trace controls
   - data retention policy

7. Add platform fit:
   - expose as a role-aware agent in Accelerant GPT Agent Hub
   - make tools reusable across Legal, Security, Finance, Procurement
   - support build-vs-buy governance for third-party procurement tools

NIST frames AI risk management around incorporating trustworthiness considerations into design, development, use, and evaluation. That is the right language for productionization. Source: [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework).

## Product Success Criteria

For the prototype:

- Correctly parses all three cases.
- Correctly calculates ACV, TCV, one-time fees, budget fit, and payment/term triggers.
- Correctly identifies missing docs and blockers.
- Correctly routes to Legal, Security, Finance, Procurement, Business Owner, and Executive sponsor where required.
- Never approves a vendor.
- Never sends external communication.
- Produces an auditable decision packet with evidence.
- Runs from README instructions.
- Deploys to a URL reviewers can access.
- Eval harness passes.

For production:

- Reduces procurement triage time.
- Reduces back-and-forth caused by missing intake information.
- Improves first-pass routing accuracy.
- Reduces legal/security/finance review thrash.
- Maintains zero tolerance for false "ready for approval" on blocked vendors.
- Keeps reviewer correction rate measurable.
- Keeps cost/run and latency bounded.
- Preserves auditability.

## Talking Points For Jay/Venkat Panel

Use this framing:

> I made the UI simple because the user is a procurement owner, not an AI engineer. The important design choice is that the model does not decide policy. The system parses the package, normalizes facts, runs deterministic tools, and then uses the LLM for synthesis and drafting. The output includes evidence and a tool trace so a human can trust, correct, or reject it.

If asked why not multi-agent:

> I would not start with multiple agents here. The policy boundaries are more important than model autonomy. In production, I would split Legal, Security, and Finance into specialized agents only after the tool surface and review queues became large enough that one orchestrator became brittle.

If asked why no vector database:

> The policy corpus is tiny, so retrieval would be performative. I encoded deterministic policy checks and preserved evidence. In production, once policies and historical reviews grow, I would add hybrid retrieval and reranking where evals show the simple approach missing context.

If asked about safety:

> Vendor docs are treated as untrusted evidence. They cannot change policy or instruct the agent. The only actions are draft outputs, and external messages require human approval.

## Source Notes

Local sources used:

- `rounds/venkat-raman-video/transcript/transcript-complete-summary.md`
- `rounds/venkat-raman-video/transcript/questions.md`
- `rounds/take-home-technical-exam/prep.md`
- `courses/anthropic/claude-in-amazon-bedrock/summaries/course-summary.md`
- `courses/anthropic/claude-in-amazon-bedrock/notes/2026-04-03-module-03-reflection.md`
- `courses/anthropic/claude-in-amazon-bedrock/notes/2026-04-05-module-04-reflection.md`
- `courses/anthropic/claude-in-amazon-bedrock/notes/2026-04-09-module-07-reflection.md`
- `system-evals/eval-standard.md`

External sources used:

- [OpenAI practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI evals guide](https://developers.openai.com/api/docs/guides/evals)
- [OpenAI Agents SDK tracing](https://openai.github.io/openai-agents-python/tracing/)
- [OpenAI Agents SDK quickstart](https://openai.github.io/openai-agents-python/quickstart/)
- [Anthropic prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview)
- [Anthropic eval tool](https://platform.claude.com/docs/en/test-and-evaluate/eval-tool)
- [Anthropic contextual retrieval](https://www.anthropic.com/engineering/contextual-retrieval)
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [Streamlit deployment docs](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit secrets management](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
- [Streamlit private app sharing](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app)
- [Render web services docs](https://render.com/docs/web-services)
- [GitHub collaborator docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository)
- [GitHub Actions secrets docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
