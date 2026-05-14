# Upload Mode Final QA

Date: 2026-05-13

## Scope

This QA pass covered the repository after adding uploaded vendor package support:

- Sample-case Streamlit flow.
- Uploaded multi-file package flow.
- Uploaded zip package flow.
- Missing-file validation flow.
- CLI, eval harness, evidence integrity, docs, requirements tracking, and git hygiene.

## Implementation Summary

The current submit flow stages reviewer-provided files into the same canonical package shape used by the seeded requests, then calls the same deterministic `run_case()` pipeline and adds a new request record to the session queue. The app accepts either five files or a zip containing the required files:

- intake workbook
- quote CSV
- contract PDF
- security questionnaire
- vendor email

Policy docs and mock internal-system data still come from the bundled candidate package so uploaded cases are evaluated against the same controls.

## Issues Found And Fixed

1. The previous app could only run bundled sample cases.
   - Fixed by adding `vendor_agent/uploads.py` and the Streamlit `Submit New Request` flow.

2. The pipeline required canonical case filenames.
   - Fixed by staging uploaded files as `uploaded_case_<required_suffix>` before calling `run_case()`.

3. Reviewers could reasonably upload a zip instead of individual files.
   - Fixed by adding safe zip expansion with path traversal checks.

4. Missing-file errors were initially rendered inside a collapsed status container during browser QA.
   - Fixed by storing upload validation feedback and rendering it visibly outside the status panel.

5. Requirements tracking did not include reviewer-driven upload testing.
   - Fixed by adding `REQ-018` and updating the acceptance matrix, README, productionization notes, progress, and Kanban.

## Verification Completed

Automated checks:

```bash
python3 -m compileall -q app.py vendor_agent tests
python3 -m pytest -q
python3 -m vendor_agent.cli eval
```

Results:

- Compile check passed.
- Test suite passed: `16 passed`.
- Eval harness passed: `3/3 passed`.
- Evidence integrity passed for all sample cases.
- Secret scan found no committed keys, private keys, or credential assignments.
- ASCII scan found no non-ASCII text in committed source/docs.
- Runtime outputs and the original source zip remain ignored by git.

Upload tests:

- Renamed multi-file upload stages correctly and runs through the real pipeline.
- Zip upload stages correctly and runs through the real pipeline.
- Missing required files are reported before triage.
- Upload role labels are reviewer-readable.

Browser checks:

- Desktop sample mode renders the default high-risk case.
- Desktop multi-file upload renders TalentPulse AI through the uploaded package path.
- Desktop zip upload renders Workspace Depot through the uploaded package path.
- Desktop missing-file validation visibly reports the missing contract, security questionnaire, and vendor email.
- Switching back from upload mode to sample mode works.
- Mobile layout exposes upload mode, file uploader, and human-gate language through the sidebar.

## Final Assessment

The prototype now better matches the realistic review scenario: a reviewer can open seeded vendor requests and can also submit a new package with files. This materially improves exam fit because the app is no longer just a fixed-case demo; it demonstrates a reusable ingestion and policy workflow.

The strongest properties remain deterministic policy routing, evidence-backed findings, human approval gates, and reproducible evals. Upload mode preserves those strengths because it does not fork the logic.

The main limitation is that uploaded packages must follow the same schema shape as the exercise cases. That is acceptable for the take-home, but production would need more flexible document classification, extraction fallbacks, and reviewer correction workflows.

## Recommended Next Steps

1. Commit and push the repo to the private GitHub repository.
2. Confirm GitHub Actions passes on `main`.
3. Deploy privately with Streamlit Community Cloud.
4. Run deployed smoke tests for all three sample cases, multi-file upload, zip upload, and missing-file validation.
5. Add README screenshots and a short reviewer walkthrough.
6. Consider optional LLM synthesis for summaries and drafts only, behind structured-output validation and the existing eval gate.
