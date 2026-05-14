# Deployment Final QA

Date: May 14, 2026

Deployed app: https://accelerant-vendor-app-agent-5rcbcuzjbmdlpyenpfeay9.streamlit.app/

## Scope

This pass covered the final submission path after GitHub push and Streamlit deployment:

- public GitHub repository setup
- Streamlit Community Cloud deployment
- deployed app smoke checks
- upload-mode browser validation
- README screenshots and walkthrough
- LLM synthesis placement assessment

## Checks Completed

| Check | Result | Evidence |
| --- | --- | --- |
| GitHub repository is public | Passed | `gh repo view` reported `visibility: PUBLIC`. |
| Initial commit pushed to GitHub | Passed | `main` pushed to `nicolairobles/accelerant-vendor-onboarding-agent`. |
| GitHub Actions CI | Passed | Latest run completed with `success`. |
| Streamlit deployment created | Passed | App opened at the deployed URL. |
| Deployed request queue | Passed | App rendered `Vendor Requests`, three seeded records, `Missing Items`, and queue priorities. |
| Deployed request detail | Passed | Workspace Depot rendered `Decision`, reviewer brief, required follow-up, internal route, drafts disclosure, and audit disclosure without implementation-mode copy. |
| Deployed submit/upload path | Passed | Uploaded `net_new_supportflow_complete.zip`; app created a SupportFlow Assist request record with upload details behind disclosure. |
| HTTP deployed smoke | Passed with session cookies | `curl -L -c cookiejar -b cookiejar` reached HTTP 200 and the Streamlit app shell. |
| README screenshots | Passed | Automated local Playwright screenshots saved under `docs/assets/screenshots/`. |
| Productized primary view | Passed | Chrome verified implementation-mode copy and primary synthesis provider details are absent from the first reviewer view. |
| OpenAI synthesis deployed smoke | Passed | Chrome verified optional OpenAI synthesis is configured while provider details stay out of the primary reviewer view. |

## Issues Found

1. GitHub access initially created review friction.
   - Fix: after secret scan and synthetic-data review, the submission repo was made public for frictionless Accelerant access.

2. Streamlit pages initially rendered blank in Chrome.
   - Fix: confirmed uBlock Origin Lite was set to no filtering for Streamlit and refreshed the page. The app then rendered normally.

3. Plain `curl -L` without a cookie jar can loop through Streamlit's auth/session redirect.
   - Assessment: not an application bug. With cookies enabled, the app shell returns HTTP 200. Browser access works.

## Residual Risks

- Before sending the final submission, confirm the public GitHub link and public Streamlit link both open from a clean browser.
- Upload mode supports the exercise package shape. Production would need broader document classification, extraction fallback, and reviewer correction workflows.
- Policy decisions remain deterministic. OpenAI synthesis is enabled only for reviewer brief and editable draft text, with deterministic fallback if validation fails.

## Final Assessment

The prototype now addresses the take-home scope with a working deployed review surface, deterministic pipeline, upload testing path, evidence model, trace, exports, tests, evals, and productionization narrative.

The remaining highest-value step before sending to Accelerant is a final human walkthrough using the email draft and public links.
