---
name: commit
description: Create a git commit in this repo using the project's message format (title is the feature name, followed by "# change" lines). Use whenever the user asks to commit, make a commit, or write a commit message.
---

# Commit

## Message format
```
<featureName>
# <change 1>
# <change 2>
```
- Line 1 is the feature name: a short camelCase name for what the commit is about, nothing else (e.g. `secretScanning`, `batteryStatusCard`). Pick it from the diff; ask the user if it's unclear.
- One `# ` line per logical change: short, imperative, no trailing period (e.g. `# add gitleaks pre-commit hook`).
- No Co-Authored-By or other trailers.

## Steps
1. Run `git status` and `git diff` (plus `git diff --cached`) to see what changed.
2. Stage only files that belong to this change, adding them by name. Never stage `.env` or other secrets.
3. Write one `# ` line per change, then commit with a heredoc:
   ```bash
   git commit --cleanup=whitespace -F - <<'EOF'
   featureName
   # change 1
   # change 2
   EOF
   ```
4. Check the result with `git log -1 --format=%B`.

## Gotchas
- **Don't drop `--cleanup=whitespace`.** Git treats lines that start with `#` as comments and deletes them whenever it opens an editor. Passing the message with `-F` plus this flag keeps them.
- **Pre-commit hooks** (gitleaks, `no-env-files`) run on every commit. If one fails, fix the cause, re-stage and commit again. Never use `--no-verify`, and never amend just to get past a failed hook.
- **pre-commit needs a recent git.** If it fails with `unknown option 'deduplicate'`, the old git in `/usr/local/bin` (2.23) is first on PATH. Prefix the command with `PATH=/usr/bin:$PATH`.
- Only commit when the user asks. Don't push unless asked.
