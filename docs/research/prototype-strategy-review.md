# Prototype Strategy Research Review

## Overall Assessment

Score: 7.5/10.

The original strategy memo is directionally strong on architecture, safety, deployment, and evaluation. It correctly recommends an app plus CLI/eval harness, grounds the recommendation in Venkat's success rubric, and avoids the two biggest traps: a shallow demo app with no reliability story, or a technically respectable CLI that does not show adoption/product judgment.

The main miss is product specificity. The memo says "Streamlit app" and names broad UI sections, but it does not yet define the actual review experience: what the procurement owner sees first, how they know what to do next, how evidence is scanned, how trust is calibrated, and how drafts are edited or gated. That gap matters because this role is explicitly about turning prototypes into adopted internal products.

## What Worked

- Clear app-vs-CLI decision.
- Strong fit to the interview signal: scalable systems, cross-functional filtering, technical depth.
- Good deterministic-first architecture.
- Correct separation between policy decisions and LLM synthesis.
- Strong evaluation harness direction.
- Appropriate deployment recommendation: clean private repo, private Streamlit or Render app.
- Good safety posture: no autonomous approvals, sends, spend commitments, or legal acceptance.

## What Was Underdeveloped

- No concrete first-screen wireframe or information hierarchy.
- No explicit user journey from "new vendor packet received" to "decision packet ready."
- No definition of the procurement owner's primary job-to-be-done.
- No specific UX behavior for high-risk vs low-risk cases.
- No interaction model for reviewing evidence, editing drafts, or acknowledging human approval gates.
- No accessibility or mobile/responsive considerations.
- No error/empty/loading-state design.
- No guidance on visual hierarchy beyond "compact and operational."
- No product metrics specific to the UI, such as time-to-decision, action clarity, or reviewer correction rate.

## Source Quality

The first memo used credible sources for agent architecture, structured output, evals, deployment, and security. It did not use enough product-design sources. The product/UX addendum should explicitly incorporate:

- Nielsen Norman usability heuristics for status visibility, real-world language, error prevention, recognition over recall, and minimalist design.
- Google People + AI guidance on trust calibration and explanations.
- Microsoft HAX and overreliance guidance for AI UX.
- Streamlit docs for layout, status, tabs, expanders, dataframes, and downloads.
- W3C accessibility principles for perceivable, operable, understandable interfaces.

## Revised Bar For The Prototype

The prototype should not merely "display results." It should let a reviewer answer five questions within the first 10 seconds:

1. What is this request?
2. Is it blocked, routable, or low-risk?
3. What are the next actions?
4. Who needs to review it?
5. Why should I trust the recommendation?

If the app cannot answer those quickly, the product layer is not doing enough work.

## Concrete Improvement Needed

Add a product/UX spec before implementation. It should define:

- Primary persona and workflow.
- Screen architecture.
- Component-level layout.
- Evidence and trust model.
- Human approval controls.
- Case-specific expected views.
- Acceptance criteria for usability.

