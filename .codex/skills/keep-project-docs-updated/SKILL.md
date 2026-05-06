---
name: keep-project-docs-updated
description: Use whenever changing code, APIs, workflows, architecture, tests, configuration, or behavior in this repo. Ensures the README/documentation of the affected project is updated in the same change.
---

# Keep Project Docs Updated

This repo contains multiple related projects. Any implementation change must keep the corresponding documentation current.

## Rule

When changing a project, update that project's docs in the same functional change if the work affects:

- API endpoints, request/response schemas, status codes, or examples.
- Architecture, phases, flows, Mermaid diagrams, or module responsibilities.
- Configuration, environment variables, ports, CLI commands, Docker usage, or startup instructions.
- SIH workflows, report generation, report locations, or execution flow.
- CAG/RAG behavior, retrieval strategy, scoring, sources, or dashboard semantics.
- Test commands, required runtimes, or validation expectations.

## Project Doc Targets

- Root overview: `README.md`
- Estimator CAG project: `estimator-cag/README.md`
- SIH Smart Analysis project: `sih-smart-analysis/README.md`

Update the narrowest relevant README first. Update the root README only when the relationship between projects, ports, phases, or repo-level flow changes.

## Workflow

1. Identify which project(s) the code change affects.
2. Before finishing, compare changed behavior against the relevant README.
3. Update examples, endpoint counts, Mermaid diagrams, and commands when they drift.
4. Run tests or the closest available validation.
5. Mention the doc update in the final summary.

Do not add separate documentation churn when behavior did not change.

