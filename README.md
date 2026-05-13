# Accelerant Vendor Onboarding Agent

Prototype for the Accelerant Applied AI take-home technical exam.

The product direction is an agentic procurement triage assistant: parse a vendor onboarding package, normalize facts, run deterministic policy checks, and produce an auditable decision packet for a human procurement owner.

## Current Status

This repo is a standalone local workspace created outside Career OS so it can later become a clean private GitHub repository.

Current artifacts:

- `data/source-package/` - original candidate package and extracted files.
- `docs/research/prototype-strategy-research.md` - first architecture/deployment strategy memo.
- `docs/research/prototype-strategy-review.md` - critique of the first memo.
- `docs/product/streamlit-product-ux-spec.md` - product and UX target for the Streamlit app.
- `docs/implementation/implementation-roadmap.md` - milestone plan and production best-practices synthesis.
- `docs/requirements/requirements-control-plane.md` - requirements tracking and AI-assisted build guardrail strategy.
- `docs/requirements/requirements-register.md` - source of truth for product/exam requirements.
- `docs/requirements/acceptance-matrix.md` - verification matrix for each requirement.
- `ARCHITECTURE.md` - architecture note for the working prototype.
- `PRODUCTIONIZATION.md` - productionization path, controls, evals, and deployment notes.
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

The deterministic pipeline is implemented for all three cases. The Streamlit app defaults to the highest-friction case so reviewers can immediately inspect the full blocker, evidence, routing, draft, and trace experience.

The Streamlit app also supports an uploaded single-vendor package. Upload either the five required files or a zip containing them:

- intake workbook (`.xlsx`)
- quote CSV (`.csv`)
- contract PDF (`.pdf`)
- security questionnaire (`.md`)
- vendor email (`.txt`)

Uploaded files are staged temporarily and run through the same deterministic pipeline as the sample cases.

GitHub Actions is configured to run compile checks, unit tests, and deterministic evals on Python 3.11 after the repo is pushed.

The CLI writes:

- `outputs/<case_id>.json` - structured decision packet
- `outputs/<case_id>.trace.json` - deterministic workflow trace
- `evals/reports/eval_report.json` - all-case regression eval report

## Confidentiality

The candidate package was provided directly during the interview process. Keep this repository private unless Accelerant explicitly says otherwise.
