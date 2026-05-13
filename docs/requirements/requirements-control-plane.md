# Requirements Control Plane For AI-Assisted Build

## Recommendation

Keep the Obsidian Kanban, but stop treating it as the source of truth for requirements.

For a vibe-coded project, the stronger system is four linked layers:

1. `requirements-register.md` - what must be true for the product and exam.
2. `acceptance-matrix.md` - how each requirement is verified.
3. `kanban.md` or GitHub Issues - what work is currently being executed.
4. `AGENTS.md`, issue forms, and PR templates - operating guardrails for AI-assisted changes.

The Kanban should answer "what are we working on next?" The requirements register should answer "why does this exist, what does done mean, and how do we prove it?"

## Why This Matters For Vibe-Coded Projects

AI-assisted coding fails differently from normal coding. The main risks are not just syntax errors; they are drift, plausible-but-wrong implementation, silent scope expansion, unreviewed dependencies, tests that confirm the wrong behavior, and code that no one can later explain.

Current guidance converges on the same pattern:

- Keep project context lean and specific.
- Plan before larger changes.
- Provide explicit files, constraints, and examples.
- Review diffs and run tests after accepted changes.
- Track AI-generated work with normal or stronger software governance.
- Use auditability, traceability, security scanning, and human review.

Sources:

- [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- [Roadmap.sh vibe coding best practices](https://roadmap.sh/vibe-coding/best-practices)
- [TechTarget: vibe coding security risks and mitigations](https://www.techtarget.com/searchSecurity/tip/Vibe-coding-security-risks-and-how-to-mitigate-them)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST SP 800-218A secure software development for generative AI](https://csrc.nist.gov/pubs/sp/800/218/a/final)
- [GitHub Issues and Projects](https://github.com/features/issues)
- [GitHub Issue Forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [VibeGuard: A Security Gate Framework for AI-Generated Code](https://arxiv.org/abs/2604.01052)
- [Is Vibe Coding Safe? Benchmarking Vulnerability of Agent-Generated Code](https://arxiv.org/abs/2512.03262)

## Operating Model

### 1. Requirement IDs Are Mandatory

Every implementation task should cite one or more requirement IDs:

```text
REQ-003 Evidence Model
REQ-006 Policy Findings
REQ-013 Eval Harness
```

No requirement ID means the task is discovery, cleanup, or out of scope.

### 2. Acceptance Criteria Come Before Code

Each requirement must define:

- user-facing outcome
- structured output or UI behavior
- deterministic verification
- allowed model behavior
- disallowed model behavior
- evidence needed to prove correctness

This protects against "it looks right" implementation.

### 3. Verification Is A First-Class Artifact

For this prototype, the verification hierarchy is:

1. Schema validation.
2. Unit tests for parsers and rules.
3. Eval cases for end-to-end decision packets.
4. Streamlit smoke test.
5. Human review of evidence, drafts, and trace.

The AI can write tests, but tests are not trusted until they are checked against the requirement and source package.

### 4. Traceability Beats Task Volume

Each requirement should eventually link to:

- source exam requirement
- implementation file(s)
- test/eval file(s)
- UI surface
- output artifact
- known risks or open questions

A small number of traceable requirements is better than a large backlog of vague tasks.

### 5. Guardrails Are Enforced In Three Places

Use the same guardrails in:

- `AGENTS.md` for AI agent behavior inside the repo
- GitHub issue forms for task creation
- PR template for review and merge readiness

This makes the desired behavior repeatable across sessions and tools.

## Recommended Local File System

```text
AGENTS.md
kanban.md
task_plan.md
findings.md
progress.md
docs/
  implementation/
    implementation-roadmap.md
  requirements/
    requirements-control-plane.md
    requirements-register.md
    acceptance-matrix.md
.github/
  ISSUE_TEMPLATE/
    requirement.yml
    config.yml
  pull_request_template.md
```

## Recommended GitHub Setup Later

When this becomes a private GitHub repo:

- Use GitHub Issues as executable work items.
- Use issue forms so every task captures requirement ID, acceptance criteria, tests/evals, risk, and out-of-scope notes.
- Use milestones for delivery phases:
  - `M1 - Deterministic core`
  - `M2 - Policy routing and evals`
  - `M3 - Streamlit review cockpit`
  - `M4 - LLM synthesis and guardrails`
  - `M5 - Submission packaging and deploy`
- Use labels:
  - `area:ingestion`
  - `area:policy`
  - `area:ui`
  - `area:evals`
  - `area:docs`
  - `area:deploy`
  - `risk:blocker`
  - `risk:security`
  - `type:test`
  - `type:cleanup`

GitHub Projects can be added only if we need a visual roadmap. GitHub Issues plus milestones are enough for this take-home.

## Change Control Rule

Any material change should update at least one of these files:

- `requirements-register.md` if the product requirement changes
- `acceptance-matrix.md` if verification changes
- `kanban.md` if execution state changes
- `implementation-roadmap.md` if sequencing changes
- `AGENTS.md` if AI operating rules change

If a change touches code but none of these files, it should be intentionally small and clearly tied to an existing requirement.

