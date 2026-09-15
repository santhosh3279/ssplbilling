# Repository working rules

## Commits around changes

- Before each logical code, configuration, or documentation change, inspect the Git working tree and create a checkpoint commit before editing.
- If the working tree is clean, use an empty checkpoint commit (`git commit --allow-empty`).
- If unrelated or pre-existing changes are present, do not include them without the user's authorization; keep them separate from the requested work.
- After completing and validating each logical change, commit only the files belonging to that change.
- Treat a related set of file edits as one logical change; do not commit every individual line edit.
- Do not push commits or publish artifacts unless the user authorizes that action.

## Completion report

- Include the before-change and after-change commit hashes.
- Summarize the changes in a table with columns for affected file, what changed, lines added, and lines removed.
- Obtain line counts from Git's diff for the completed change rather than estimating them.
- State what validation ran and any checks that could not be completed.
