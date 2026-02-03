# Version Control

Commit vault changes to git with privacy protection and user approval.

## Contract

**Pre-conditions:**
- Git repository initialized in vault root
- .gitignore configured with privacy rules

**Post-conditions:**
- All changes committed (if approved) or skipped (if declined/no changes)
- ACTION_LOG.md updated with commit summary

**Errors:**
- Git not initialized → abort with setup instructions
- Secrets detected → abort, show findings, do not commit
- User declines → skip commit, log "declined"

## Privacy Protection (4 Layers)

| Layer | Protection |
|-------|------------|
| 1. Private folder | `_private/` is never tracked |
| 2. Naming convention | `*.private.md`, `*.secret.md` ignored |
| 3. Pre-commit review | Show diff summary, user approves |
| 4. Secret detection | Gitleaks scan (if available) |

## Procedure

### 1. Check git status

```bash
git status --porcelain
```

```
✓ If empty: "No changes to commit" → procedure complete
✓ If changes: continue to step 2
✗ On fail: "Git not initialized. Run: git init"
```

### 2. Stage changes

```bash
git add -A
```

```
✓ Verify: changes staged
✗ On fail: abort with git error
```

### 3. Secret detection (optional)

```bash
# Only if gitleaks is installed
gitleaks detect --staged --no-git
```

```
✓ If clean: continue
✗ If secrets found: STOP, show findings, abort procedure
✗ If gitleaks not installed: skip this step, continue
```

### 4. Generate diff summary

```bash
git diff --cached --stat
```

Present to user:
```
Changes to commit:

 _system/procedures/new-proc.md | 50 +++
 work/bookmarks.md              | 12 +-
 BACKLOG.md                     |  3 -
 3 files changed, 53 insertions(+), 12 deletions(-)
```

### 5. Request approval

Ask user:
```
Commit these changes as "Daily snapshot: {YYYY-MM-DD}"?
- Yes, commit
- No, skip
- Show full diff
```

**If "Show full diff":**
```bash
git diff --cached
```
Then re-ask approval.

**If "No, skip":**
```bash
git reset HEAD
```
Log: "Version control: skipped by user"
Procedure complete.

**If "Yes, commit":**
Continue to step 6.

### 6. Commit

```bash
git commit -m "Daily snapshot: {YYYY-MM-DD}"
```

```
✓ Verify: commit created
✗ On fail: abort with git error
```

### 7. Log & confirm

Append to ACTION_LOG.md:
```markdown
### {date} Version Control
- Committed: {N} files changed, {insertions} insertions, {deletions} deletions
- Message: "Daily snapshot: {YYYY-MM-DD}"
```

Return to user:
```
Committed {N} files. (Daily snapshot: {YYYY-MM-DD})
```

## Triggers

| Command | Action |
|---------|--------|
| "commit vault" | Run this procedure |
| "git commit" | Run this procedure |
| "save changes" | Run this procedure |
| (first check-in of day) | Auto-triggered by check-in workflow |

## Examples

**Normal commit:**

1. User: "commit vault"
2. Status: 5 files changed
3. Gitleaks: clean
4. Summary shown
5. User: "Yes, commit"
6. Committed as "Daily snapshot: 2026-01-20"

---

**No changes:**

1. User: "commit vault"
2. Status: nothing to commit
3. "No changes to commit."

---

**Secrets detected:**

1. User: "commit vault"
2. Status: 3 files changed
3. Gitleaks: FOUND api_key in config.md
4. "Secret detected! Cannot commit. Please remove the secret from config.md before committing."
5. Procedure aborts (no commit)

---

**User declines:**

1. User: "commit vault"
2. Status: 2 files changed
3. Summary shown
4. User: "No, skip"
5. Changes unstaged
6. "Skipped commit."
