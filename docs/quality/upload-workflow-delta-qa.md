# Upload Workflow Delta QA

Date: 2026-05-13

## Scope

This pass addressed the product confusion around uploaded files and bundled sample cases, then was superseded by a stronger request-queue model.

The intended model is now explicit:

- seeded exam cases appear as existing vendor requests in one queue
- `Submit New Request` creates a new request record in the current Streamlit session
- uploaded files do not modify seeded requests
- matched uploads can still show baseline comparison inside upload intake details
- net-new uploads appear as new queue rows with no matching seeded baseline

## Changes Verified

- Sidebar navigation now uses `Vendor Requests` and `Submit New Request`.
- Submit copy now states that uploads add a new request to the queue.
- Uploaded request details keep baseline comparison and uploaded file mapping behind disclosure.
- Upload intake details show required files, support artifacts, remaining requests, remaining blockers, matched baseline, resolved missing-information items, and uploaded file mapping.
- `Staged package mapping` is available behind disclosure for audit/debug needs.
- Added `net_new_supportflow_complete` packet to test a vendor that is not one of the bundled sample cases.
- Requirements, acceptance matrix, product UX spec, README, Kanban, findings, and progress notes were updated.
- Replaced the separate sample-review/upload navigation with a single `Vendor Requests` queue and `Submit New Request` action.
- Added request open/delete lifecycle for the current Streamlit session.
- Moved drafts, upload intake details, staged mapping, evidence, workflow, trace, and exports behind disclosure to reduce first-viewport noise.

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

Request queue recalibration verification:

- Full compile check passed.
- Full test suite passed: `37 passed`.
- Deterministic eval passed: `3/3 passed`.
- Whitespace diff check passed.

## Browser Smoke

Local Streamlit was started at `http://localhost:8510`.

Verified in the Codex in-app browser:

- Dashboard renders the seeded vendor request queue.
- Sidebar shows `Vendor Requests`, `Submit New Request`, and `Restore Seeded Requests`.
- Queue rows open request details.
- Request detail renders `Decision`, `Required Vendor Follow-up`, `Internal Review Route`, `Drafts`, and `Audit details`.
- `Delete request` removes the request from the session queue and updates request metrics.
- `Submit New Request` renders the file uploader and queue-creation guidance.

Browser limitation:

- The in-app browser exposed the file uploader but did not support `setInputFiles` for this Streamlit file input, so uploaded-file execution was verified through automated staging, packet, and Streamlit regression tests instead of an interactive browser file upload.

## Final Assessment

This fixes the main product drift. A reviewer should no longer infer that there are separate "sample case" and "upload" worlds. The app now behaves like a lightweight procurement queue: existing vendor requests are already present, new valid packages become request records, and request details lead with decisions rather than internals.

Remaining production limitation: uploaded support artifacts are recognized and reflected in checklist state, but their contents are not deeply parsed beyond role recognition.
