# Global Codex Instructions

## Git sync before edits

- Before modifying any file inside a Git repository, check the current branch and repository state, then synchronize the local branch with its remote using `git pull` when a remote tracking branch exists.
- During long sessions, repeat the sync before new blocks of edits if more than 30 minutes have passed since the last successful `git pull`, or if the work expands to additional files or modules.
- If `git pull` fails, creates conflicts, or reveals local/remote divergence that needs judgement, stop before editing and explain the repository state to the user.
- The reusable skill for this convention is `git-sync-before-edit`.

## Version bump after compile or validation

- If a repository defines a version bump tool, version bump command, or explicit version bump workflow, use it after any change that reaches a local compile or validation milestone.
- This rule applies even when the change is small, local, or apparently trivial.
- Typical milestones include commands such as `npm run compile`, `npm run build`, `npm test`, `npm run test`, `dotnet build`, `dotnet test`, or equivalent repository-specific compile, build, or validation commands.
- Do not defer the version bump to a later session.
- Do not batch the version bump with unrelated future changes.
- When the repository has an explicit commit convention for version bumps, follow it.
- When the repository does not define any version bump tool or workflow, do not invent one; follow the repository rules that exist.

## Session branch workflow

- Every new work session or exercise starts from a new branch created from `main`.
- Session branches follow the naming pattern `{nn}-session`, for example `05-session`.
- Before creating the new session branch, check whether the previous session branch still exists and contains pending work that must be integrated into `main`.
- If a previous session branch must be integrated, stop and ask the user for confirmation before performing the merge into `main`.
- Only after the previous session has been integrated into `main` may the new session branch be created, so it starts with all prior approved changes.
- Example workflow: if work is going to start on session 5 and `04-session` is still the previous session branch, first confirm with the user that `04-session` should be merged into `main`; after that merge, create `05-session` from the updated `main`.
