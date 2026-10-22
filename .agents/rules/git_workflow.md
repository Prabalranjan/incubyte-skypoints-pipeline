# Git Workflow & Pull Request Policy

This rule is mandatory for the entire project:

1. **Never Push Directly to `main`**:
   - The `main` branch is protected and reserved for merged PRs.
   - All development must take place on dedicated feature branches (e.g., `feat/...`, `fix/...`, `test/...`).

2. **Issue First**:
   - Before starting any task, stage, or feature, create a GitHub Issue via `gh issue create`.
   - The issue should outline the scope, deliverables, and acceptance criteria.

3. **Branching**:
   - Create a clean branch from the latest `main`:
     ```bash
     git checkout -b feat/issue-<number>-<short-description>
     ```

4. **Incremental Commits**:
   - Make atomic, well-described commits using conventional commit messages (e.g., `feat: ...`, `test: ...`, `docs: ...`).

5. **Push and Raise Pull Request**:
   - Push the feature branch to origin:
     ```bash
     git push -u origin <branch-name>
     ```
   - Raise a Pull Request via `gh pr create`:
     - Reference and link the issue (`Closes #<issue_number>`).
     - Detail the changes, test results, and verification steps in the PR description.
