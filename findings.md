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

