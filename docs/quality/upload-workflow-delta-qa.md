# Upload Workflow Delta QA

Date: 2026-05-13

## Scope

This pass addressed the product confusion around uploaded files and bundled sample cases.

The intended model is now explicit:

- sample cases are locked reference cases
- `Triage new package` creates a temporary standalone case
- uploaded files do not modify sample cases
- matched uploads show a baseline comparison
- net-new uploads show no matching sample baseline

## Changes Verified

- Sidebar label changed from upload-oriented copy to `Triage new package`.
- Upload sidebar copy now states that uploads create a temporary standalone case and do not modify sample cases.
- Uploaded runs now show `Package Delta` before the full case review cockpit.
- `Package Delta` shows required files, support artifacts, remaining requests, remaining blockers, matched baseline, resolved missing-information items, and uploaded file mapping.
- `Staged package mapping` is available behind disclosure for audit/debug needs.
- Added `net_new_supportflow_complete` packet to test a vendor that is not one of the bundled sample cases.
- Requirements, acceptance matrix, product UX spec, README, Kanban, findings, and progress notes were updated.

## Automated QA

Commands run:

```bash
python3 scripts/build_sample_upload_packets.py
python3 -m pytest -q tests/test_sample_upload_packets.py tests/test_streamlit_app.py
python3 -m compileall -q app.py vendor_agent tests scripts
git diff --check
python3 -m pytest -q
python3 -m vendor_agent.cli eval
```

Results:

- Targeted upload and Streamlit tests passed: `14 passed`.
- Full compile check passed.
- Whitespace diff check passed.
- Full test suite passed: `36 passed`.
- Deterministic eval passed: `3/3 passed`.

## Browser Smoke

Local Streamlit was started at `http://localhost:8503`.

Verified in the Codex in-app browser:

- Dashboard renders the sample queue.
- Sidebar shows `Dashboard`, `Review sample case`, and `Triage new package`.
- `Triage new package` renders the file uploader and standalone-case guidance.

Browser limitation:

- The in-app browser exposed the file uploader but did not support `setInputFiles` for this Streamlit file input, so uploaded-file execution was verified through automated staging, packet, and Streamlit regression tests instead of an interactive browser file upload.

## Final Assessment

This fixes the main product drift. A reviewer should no longer infer that uploading TalentPulse files updates the TalentPulse sample. The upload flow is now framed as a standalone triage run, and the first visible uploaded-case section answers what changed, what was recognized, and what still blocks routing.

Remaining production limitation: uploaded support artifacts are recognized and reflected in checklist state, but their contents are not deeply parsed beyond role recognition.
