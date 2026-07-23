---
name: session-branch-workflow
description: Prepare, integrate, and start master-course session or exercise branches in this repository. Use before beginning any numbered session, pre-work, post-session exercise, or sequential training delivery that depends on earlier session branches.
---

# Session Branch Workflow

Use this workflow before editing session work.

1. Inspect `git status`, the current branch, local and remote session branches, and worktrees.
2. Synchronize the current tracking branch. Do not edit if the pull reveals divergence or conflicts.
3. Identify the immediately preceding session branch and check whether it is already an ancestor of `main`.
4. If prior work is not integrated, report the exact branch and diff to the user and obtain explicit approval before merging it into `main`.
5. Refresh `main` from `origin/main`; create the new branch from that refreshed `main` only after the preceding work is integrated.
6. Reuse the established branch family. For current exercises, prefer `session-<nn>/pre-exercise` when that matches the preceding branches.
7. Create or use a dedicated worktree for the new branch. Keep unrelated uncommitted files in their original worktree.
8. Record the base commit, prior integration decision, branch name, and validation result in the delivery summary.

Never create a new session branch from another session branch, a detached head, or a dirty worktree. Never silently merge a prior session into `main`.
