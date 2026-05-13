# Findings

## Requirements And Guardrails Research

- Kanban alone is too weak for AI-assisted builds because it tracks task state but not requirement provenance, acceptance criteria, verification, or code traceability.
- Current AI coding guidance emphasizes precise context, scoped prompts, planning for larger changes, diff review, tests after accepted changes, and lean project instruction files.
- Vibe-coded projects have distinctive risks: context drift, plausible wrong code, unreviewed generated changes, hidden security issues, excessive dependencies, and tests that validate the wrong behavior.
- Security guidance recommends treating AI output as a draft, preserving auditability and traceability, scanning/testing generated code, and using human review.
- For this take-home, the best lightweight system is a requirements register plus acceptance matrix, backed by Kanban/GitHub Issues and enforced through `AGENTS.md`, issue forms, and PR templates.

## Sources

- Claude Code best practices: https://code.claude.com/docs/en/best-practices
- Roadmap.sh vibe coding best practices: https://roadmap.sh/vibe-coding/best-practices
- TechTarget vibe coding security risks: https://www.techtarget.com/searchSecurity/tip/Vibe-coding-security-risks-and-how-to-mitigate-them
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- NIST SP 800-218A: https://csrc.nist.gov/pubs/sp/800/218/a/final
- GitHub Issues: https://github.com/features/issues
- GitHub Issue Forms: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
- VibeGuard: https://arxiv.org/abs/2604.01052
- Is Vibe Coding Safe?: https://arxiv.org/abs/2512.03262

## 2026-05-13 Productization Audit Findings

- The original exam asks for a prototype that reviews a vendor onboarding package and produces a structured recommendation for a human procurement owner. The UI should therefore optimize for procurement reviewer decisions: status, missing information, policy fit, evidence, route, drafts, and exports.
- The provided process-flow PNG frames the app as a case-package triage flow: parse/extract, validate package, branch on complete enough for triage, normalize facts, run deterministic tools, determine approvals/risk, prepare outputs, then human approval gate.
- Current UI issue: sidebar copy such as `Mode: Deterministic policy workflow` and `Human gate: No approvals...` explains implementation constraints rather than helping the reviewer. It should be removed from the primary navigation and represented only where it affects action: required human route, drafts, and prohibited actions.
- Current UI issue: Next Actions uses checkboxes that do not trigger state changes or workflow transitions. That is a false affordance. Replace with static action rows that show action, owner, why, and evidence, with no clickable control unless it performs a real action.
- Current UI issue: the workflow table shows tool-call names prominently in the main review path. The exam requires tools/function calls, but the product should show reviewer-friendly workflow status first and leave raw tool names in Trace/export or an expander.
- Policy alignment: the Communication Policy prohibits autonomous approval, spend commitment, term acceptance, or external sends. The UI should state that the packet is a routing recommendation and drafts require human approval, but this should not be sidebar clutter.
- Policy alignment: Procurement, Legal, Finance, Security, Data Handling, and Vendor Risk policies all make missing information and approval routing the primary user decisions. The Overview should lead with follow-up requests and required route rather than generic "inspect evidence" tasks.

## 2026-05-13 Process Flow And Synthesis Findings

- The provided PNG does not explicitly require a live LLM step. It requires parse/extract, package validation, missing-item branching, deterministic helper tools, approvals/risk determination, output preparation, draft follow-up, escalation, and a human approval gate.
- The current implementation is on track with the PNG. The main production gap is persisted workflow state for assignments, edits, signoffs, and final routing decisions.
- LLM synthesis is still valuable inside the PNG's `Prepare outputs` stage because the human procurement owner needs a concise reviewer brief and draft language.
- The safe synthesis boundary is downstream of the structured decision packet. The synthesis may rewrite summaries and drafts, but it must not change status, risk, budget, missing information, approval route, or prohibited actions.

## 2026-05-13 Live OpenAI Synthesis QA Findings

- The live OpenAI call is correctly scoped to drafting and synthesis. It is not part of policy, risk, budget, missing-information, or approval-route decisions.
- First live smoke showed a realistic risk: even with structured output, the model may paraphrase required missing-item labels. Exact-label preservation is important because the packet is used for procurement follow-up.
- The implemented fix is to require exact missing item labels, set temperature to 0, validate the output, and fall back to deterministic synthesis if validation fails.
- Deployment still needs Streamlit secrets for live synthesis. The repository must not commit `.env.local` or any plaintext key.
