# Accelerant Vendor Onboarding Agent

Prototype for the Accelerant Applied AI take-home technical exam.

The product direction is an agentic procurement triage assistant: parse a vendor onboarding package, normalize facts, run deterministic policy checks, and produce an auditable decision packet for a human procurement owner.

## Current Status

This repo is a standalone private GitHub repository created outside Career OS for the Accelerant take-home.

Deployed reviewer app: [accelerant-vendor-app-agent-5rcbcuzjbmdlpyenpfeay9.streamlit.app](https://accelerant-vendor-app-agent-5rcbcuzjbmdlpyenpfeay9.streamlit.app/)

Current artifacts:

- `data/source-package/` - original candidate package and extracted files.
- `docs/research/prototype-strategy-research.md` - first architecture/deployment strategy memo.
- `docs/research/prototype-strategy-review.md` - critique of the first memo.
- `docs/research/llm-synthesis-assessment.md` - assessment of where LLM synthesis should and should not be added.
- `docs/product/streamlit-product-ux-spec.md` - product and UX target for the Streamlit app.
- `docs/implementation/implementation-roadmap.md` - milestone plan and production best-practices synthesis.
- `docs/requirements/requirements-control-plane.md` - requirements tracking and AI-assisted build guardrail strategy.
- `docs/requirements/requirements-register.md` - source of truth for product/exam requirements.
- `docs/requirements/acceptance-matrix.md` - verification matrix for each requirement.
- `data/sample-upload-packets/` - realistic upload packet folders and zips for manual QA.
- `ARCHITECTURE.md` - architecture note for the working prototype.
- `PRODUCTIONIZATION.md` - productionization path, controls, evals, and deployment notes.
- `docs/quality/dashboard-upload-guardrail-qa.md` - QA notes for the dashboard, process-flow, workbook, and upload guardrail pass.
- `AGENTS.md` - repo-local AI coding guardrails.
- `kanban.md` - Obsidian Kanban board for build work.
- `task_plan.md`, `findings.md`, `progress.md` - persistent planning memory for longer AI-assisted sessions.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Python 3.11 is the intended runtime for deployment. The current prototype is deterministic and does not require an LLM API key.

## Working Commands

```bash
python3 -m vendor_agent.cli run \
  --case data/source-package/Candidate_package/cases/case_003 \
  --out outputs/case_003.json

python3 -m vendor_agent.cli eval

python3 -m pytest -q

streamlit run app.py
```

The deterministic pipeline is implemented for all three cases. The Streamlit app opens on a procurement case queue, then lets reviewers drill into sample cases or upload a new package.

The Streamlit app also supports an uploaded single-vendor package. Upload either the five required files or a zip containing them:

- intake workbook (`.xlsx`)
- quote CSV (`.csv`)
- contract PDF (`.pdf`)
- security questionnaire (`.md`)
- vendor email (`.txt`)

Uploaded files are staged temporarily and run through the same deterministic pipeline as the sample cases. Upload mode also recognizes optional support artifacts such as DPA, SOC 2, subprocessor list, tax form, vendor setup form, and AI training opt-out confirmation. Ambiguous or mixed-vendor packages are blocked before triage.

## Sample Upload Packets

Use the zips under `data/sample-upload-packets/zips/` to test upload mode:

- `valid_low_risk_ops_complete.zip`
- `high_risk_ai_with_support_artifacts.zip`
- `guardrail_prompt_injection_email.zip`
- `guardrail_policy_doc_decoy_incomplete.zip`
- `invalid_mixed_vendor_case_prefixes.zip`
- `invalid_bad_quote_schema.zip`

Regenerate them with:

```bash
python3 scripts/build_sample_upload_packets.py
```

GitHub Actions is configured to run compile checks, unit tests, and deterministic evals on Python 3.11 after the repo is pushed.

The CLI writes:

- `outputs/<case_id>.json` - structured decision packet
- `outputs/<case_id>.trace.json` - deterministic workflow trace
- `evals/reports/eval_report.json` - all-case regression eval report

## Reviewer Walkthrough

1. Open the deployed Streamlit app.
2. Start on the dashboard case queue. Use it to compare case status, risk, spend, missing information, blockers, and next owner.
3. Switch to `Review sample case` and open `case_003` for TalentPulse AI. This shows the hardest case: high risk, insufficient budget, legal/security/finance routing, missing vendor documents, evidence, drafts, and trace.
4. Use the workflow panel and tabs to inspect how the packet is grounded:
   - `Overview` for the procurement summary and next actions.
   - `Findings` for policy-specific blockers.
   - `Evidence` for source-linked extracted facts.
   - `Drafts` for human-reviewed vendor and internal follow-up text.
   - `Trace` for deterministic parser/tool/rule execution.
5. Export JSON, trace, Markdown brief, or the XLSX triage workbook.
6. Switch to `Upload package` to test a new vendor package. Upload either five files or one zip containing an intake workbook, quote CSV, contract PDF, security questionnaire, and vendor email. Optional support artifacts are mapped separately and reflected in the staged checklist.

## Screenshots

### Dashboard Case Queue

![Dashboard case queue](docs/assets/screenshots/dashboard-case-queue.png)

### Sample Case Workflow

![Sample case workflow](docs/assets/screenshots/sample-case-workflow.png)

### Upload Workspace

![Upload workspace](docs/assets/screenshots/upload-workspace.png)

## Deployment QA

Deployment smoke tests were run on May 13, 2026:

- Streamlit deployed app opened successfully in Chrome.
- Default sample case rendered the expected TalentPulse AI blocked packet.
- Upload mode showed the expected missing-file validation before upload.
- Uploaded zip package produced the expected Workspace Depot packet.
- HTTP smoke check reached the deployed Streamlit app shell with a cookie jar.

See `docs/quality/deployment-final-qa.md` for the full deployment QA notes.

## LLM Synthesis Stance

The submitted prototype intentionally keeps policy decisions deterministic. LLM synthesis can be useful later for summaries, vendor follow-up drafts, and internal notes, but it should sit behind the existing structured decision packet, schema validation, evidence checks, and eval gate. The app should continue to run without `OPENAI_API_KEY`.

See `docs/research/llm-synthesis-assessment.md` for the recommended architecture and eval plan.

## Confidentiality

The candidate package was provided directly during the interview process. Keep this repository private unless Accelerant explicitly says otherwise.
