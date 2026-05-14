# Final QA Assessment

Date: 2026-05-13

## Scope

This pass reviewed the implemented Accelerant take-home prototype end to end:

- Deterministic case ingestion and policy pipeline.
- CLI run and all-case eval harness.
- Streamlit review cockpit.
- Tests, docs, git hygiene, ignored artifacts, and GitHub-readiness.

## Issues Found And Fixed

1. README had stale setup guidance and a CLI command without `--out`.
   - Fixed by replacing the old planned-command block with current setup and working commands.

2. `.env.example` implied an OpenAI API key was required.
   - Fixed by documenting that the current prototype is deterministic and does not require an API key.

3. Local source zip could be accidentally committed.
   - Fixed by ignoring `data/source-package/*.zip`; extracted candidate files remain available for the repo.

4. Streamlit vendor name visually truncated in the top KPI area.
   - Fixed by replacing the cramped custom HTML metric-style vendor block with native Streamlit text above the metric row.

5. Dollar amounts in the overview summary were interpreted as Markdown/math delimiters.
   - Fixed by rendering the summary as escaped HTML text, preserving `$120,000`, `$20,000`, and `$0`.

6. Streamlit behavior was not covered by tests.
   - Fixed by adding `tests/test_streamlit_app.py` for default render, case switching, and Markdown brief generation.

7. GitHub push target was not configured locally.
   - Fixed by adding `origin` as `https://github.com/nicolairobles/accelerant-vendor-onboarding-agent.git`.

8. No CI existed for the GitHub repo.
   - Fixed by adding `.github/workflows/ci.yml` to run compile checks, unit tests, and deterministic evals on Python 3.11.

## Verification Completed

Automated checks:

```bash
python3 -m compileall -q app.py vendor_agent tests
python3 -m pytest -q
python3 -m vendor_agent.cli eval
```

Results:

- Compile check passed.
- Test suite passed: `13 passed`.
- Eval harness passed: `3/3 passed`.
- Evidence integrity script passed for all three cases.
- Secret scan found no committed keys, private keys, or credential assignments.
- ASCII scan found no non-ASCII text in committed source/docs added for this prototype.
- Runtime artifacts and source zip are ignored by git.

Browser/UI checks:

- Desktop isolated browser render at `1280x900`.
- Mobile isolated browser render at `390x844`.
- Default `case_003` shows blocked high-risk review with full vendor name, dollar amounts, missing information, approval route, downloads, and tabs.
- Case switch to `case_002` works and shows Workspace Depot, low risk, sufficient budget, two missing setup items, and the reduced human route.
- Drafts tab keeps message bodies disabled until the human-approval acknowledgment is checked.
- Markdown, JSON, and trace download controls are visible.

## Final Assessment

The prototype is in a strong take-home submission state. It directly addresses the exam objective: ingest a vendor onboarding package, normalize facts, run policy checks, surface evidence-backed blockers, route human review, produce draft follow-ups, and expose an auditable trace.

The strongest parts are the deterministic pipeline, explicit evidence IDs, Pydantic decision packet, all-case eval harness, and guardrail-oriented product UX. The main remaining limitation is scope: the parser is intentionally optimized for the supplied package structure, not arbitrary vendor packages.

## Residual Risks

- The app is not deployed yet; only local Streamlit and isolated browser smoke tests were completed.
- GitHub CI is configured locally but will only run after the first push.
- GitHub Issues, labels, and milestones have not been created from the requirements register.
- The prototype does not yet include screenshots or a reviewer walkthrough script.
- Chrome profile state became stale during hot-reload testing; isolated Playwright checks rendered the patched app correctly.

## Recommended Next Steps

1. Commit and push the repo to the public GitHub repository.
2. Confirm GitHub Actions passes on `main`.
3. Create GitHub milestones and issues from `docs/requirements/requirements-register.md`.
4. Deploy the Streamlit app and run the same smoke checks against the deployed URL.
5. Add README screenshots and a short reviewer walkthrough script for the Accelerant submission.
6. Keep the eval harness as the regression gate for any further agentic or LLM-assisted enhancements.
