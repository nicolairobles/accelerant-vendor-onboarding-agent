# Dashboard And Upload Guardrail QA

Date: 2026-05-13

## Scope

This pass covered the product and guardrail adjustments made after reviewing the original exam prompt and the provided process-flow PNG.

Covered areas:

- Dashboard-first Streamlit homepage.
- Sample case review workspace.
- Uploaded package workspace.
- Triage workflow panel.
- XLSX triage workbook export.
- Upload role matching, optional support-artifact handling, and edge-case guardrails.
- Requirements, acceptance criteria, architecture, UX spec, roadmap, README, Kanban, and persistent planning notes.

## Changes Verified

- App home now opens on a vendor case queue instead of a single default case.
- Case details retain the procurement review cockpit but add a triage workflow panel aligned to the source flow image.
- Export controls now include JSON, trace JSON, Markdown brief, and XLSX triage workbook.
- Upload staging now applies stricter confidence thresholds for required artifacts.
- Policy docs and arbitrary markdown are not accepted as security questionnaires.
- Optional support artifacts are mapped separately and update matching checklist rows.
- Mixed-vendor zip packages are blocked before triage.
- Prompt-injection text in vendor email does not override deterministic policy routing or human gates.

## Verification

Commands run:

```bash
python3 -m compileall -q app.py vendor_agent tests
python3 -m pytest -q
python3 -m vendor_agent.cli eval
git diff --check
```

Results:

- Compile check passed.
- Full test suite passed: `22 passed`.
- Deterministic eval passed: `3/3 passed`.
- Whitespace diff check passed.

Browser smoke:

- Started Streamlit locally at `http://127.0.0.1:8501`.
- Verified dashboard homepage renders `Vendor Case Queue` and `Queue Priorities`.
- Verified review workspace renders TalentPulse AI with `Triage Workflow` and triage workbook export.
- Verified upload workspace renders `New Vendor Package` and file uploader.
- Refreshed README screenshots for dashboard, sample case workflow, and upload workspace.
- Added generated sample upload packets and zips for valid low-risk, high-risk support-doc, prompt-injection, policy-doc decoy, mixed-vendor, and malformed quote scenarios.
- Verified sample packets with `tests/test_sample_upload_packets.py`.

## Issue Found And Fixed

The local Streamlit runtime rejected the `max_upload_size` keyword on `st.file_uploader`. The fix removed that UI argument and retained backend file-count and total-size enforcement in `vendor_agent.uploads`.

## Final Assessment

This pass materially improves exam fit. The app now behaves more like a procurement workbench than a fixed-case demo, the upload path is less brittle, and the visible workflow better reflects the source process-flow image.

Remaining production limitations:

- Optional support artifacts are recognized and reflected in the checklist, but their document contents are not deeply parsed.
- Uploaded packages still need the same core schema shape as the exercise cases.
- The deployed Streamlit app should be redeployed and smoke-tested after this local change set is pushed.
