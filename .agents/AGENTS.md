# Project Guidelines & Workflow

This document defines the strict operational rules for AI agents operating in the `lively-hubble` repository.

## GitHub Workflow Rules
1. **Never commit directly to `main`**. All changes MUST go through a Pull Request.
2. When creating new features or fixing bugs:
   - Create a new branch: `git checkout -b feature/<name>` or `fix/<name>`
   - Make your commits.
   - Push the branch: `git push -u origin <branch>`
   - Create a Pull Request using the GitHub CLI: `gh pr create --title "..." --body "..."`
3. The user must manually approve and merge the PR (or instruct you to merge it via `gh pr merge`).

## Documentation Rules
1. **README Updates:** Every time a new feature is added, or architectural changes are made, you MUST update the `README.md` file accordingly.
2. **Interview God File Updates:** This project serves as a flagship portfolio piece for the user. Whenever you face an engineering challenge, resolve a major bug, or make an architectural decision, you MUST document the "Problem", "Solution", and "Why" inside `INTERVIEW_GOD.md`. Never let this file fall out of date.
