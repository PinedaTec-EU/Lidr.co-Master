---
name: make-functional-commits
description: Use whenever preparing git history, staging work, committing, or splitting completed work in this repo. Enforces small functional commits with coherent scope and validation.
---

# Make Functional Commits

This repo should evolve through functional commits: each commit must represent one coherent, reviewable unit of behavior.

## Rule

Create commits by functional scope, not by file type or by broad work sessions.

A functional commit should usually include:

- The code change.
- Its tests or closest validation.
- Documentation updates required by that change.
- Related SIH workflow/report fixture changes only when they are part of the same behavior.

## Commit Boundaries

Prefer separate commits for:

- A new API capability.
- A behavior fix.
- A documentation-only correction.
- A test-only hardening change.
- Generated SIH reports, when kept intentionally as evidence.

Avoid commits that mix unrelated project areas, such as `estimator-cag` behavior and `sih-smart-analysis` refactors, unless the change is explicitly cross-project.

## Workflow

1. Inspect `git status --short` before staging.
2. Separate unrelated existing user changes from your own work.
3. Stage only files belonging to the intended functional scope.
4. Run relevant tests before committing when possible.
5. Use a concise imperative commit message, for example:
   - `Add SIH report analysis API`
   - `Document CAG and RAG project phases`
   - `Support real SIH report normalization`

Never revert unrelated user changes to make a commit clean. If unrelated dirty files exist, leave them unstaged.

