# Profiles and decision interview

## Interview

Ask these questions in one compact exchange:

1. Is this a throwaway prototype, a real product, or a system with production/security/compliance consequences?
2. Does it have login, payments, personal data, external webhooks, background jobs, or deployment infrastructure?
3. Is there a user-facing web UI that needs accessibility, performance, and visual regression checks?
4. Does it have a relational database or schema migrations?
5. Should checks block a PR/merge, or only produce a local report?

Recommend `prototype` for a small, short-lived project with no sensitive data; `balanced` for a real application; and `production` for shared, deployed, security-sensitive, or migration-heavy systems.

## Quick choice

| Profile | Project fit | Main method | Skill stages | Expected output |
|---|---|---|---|---|
| `prototype` | Personal prototype/MVP, low-risk data | Fast Matt Pocock loop | grill → plan → implement → smoke test → review | Working demo and lightweight test evidence |
| `balanced` | Real app, small/medium team, public UI/API | Matt Pocock + executable quality gates | discover → design → plan → implement → tests → UI/security audit → PR review | Test, UI, security and dependency reports |
| `production` | Deployed product, many contributors, sensitive data | Matt Pocock + conditional Spec Kit + protected CI | spec → design → plan → implement → full audit → protected PR → release/retro | Traceable spec, audit artifacts, migration/security gates |

The installer displays this table when `--profile` is omitted. It only installs the selected profile's components; it does not install tools from the other profiles.

## Stage model

1. Discover: clarify the problem, constraints, non-goals, and acceptance criteria.
2. Design: inspect the repository and domain model; identify risks and boundaries.
3. Plan: split work into small tasks with verification commands.
4. Implement: make the smallest change, using tests and existing conventions.
5. Verify: run tests, type/lint checks, and profile-specific audits.
6. Review: produce reports, fix blockers, and record residual risk.
7. Ship/retro: prepare the PR and capture workflow improvements.

## Profile matrix

### prototype

Matt Pocock skills for grill/plan/implement/review; project-native formatter/linter, typecheck if available, unit/smoke tests, and optional Playwright smoke test.

### balanced

Matt Pocock is the sole workflow orchestrator. Add pre-commit, typecheck/lint/test, Playwright, axe-core, Lighthouse, Semgrep, Gitleaks, OSV-Scanner, SQLFluff when SQL exists, and Reviewdog in CI.

### production

Use Matt Pocock plus GitHub Spec Kit only for large feature specs; do not install Superpowers as a second orchestrator. Add all balanced gates, CodeQL, Trivy, Zizmor, visual regression, database migration diff/plan with Atlas or the existing ORM authority, protected CI gates, and artifact reports.

## Non-overlap rules

- Matt is the workflow coordinator. Spec Kit is conditional and only handles durable feature specifications.
- Playwright is the browser runner; axe-core is the accessibility engine; Lighthouse is the performance/SEO auditor.
- Semgrep is SAST; Gitleaks is secret detection; OSV-Scanner is dependency scanning; Trivy is container/IaC/filesystem scanning; CodeQL is deeper production analysis.
- SQLFluff is SQL linting. Atlas or the repository's existing ORM is the migration authority, never both as competing schema owners.
