# Process Backlog

User-facing workflow to process all pending inputs from BACKLOG.md, _inbox/, and Todoist Inbox.

## Contract

**Pre-conditions:**
- User triggers with "process backlog", "triage", or similar
- At least one source has pending items (BACKLOG.md, _inbox/, or Todoist Inbox)

**Post-conditions:**
- All pending items are either committed (to Todoist/vault) or explicitly skipped
- PROCESSING.md is empty (all items processed)
- ACTION_LOG.md updated with session summary

**Errors:**
- Todoist API unavailable → abort after ensure-todoist-sync
- User aborts → state persisted in PROCESSING.md for recovery

## Triggers

| Command | Action |
|---------|--------|
| "process backlog" | Run this workflow |
| "process my backlog" | Run this workflow |
| "triage" | Run this workflow |

## Critical Rules

- **PROCESSING.md is the only interface** — never present items from memory
- **Max 5 items per review batch** — never overwhelm the user
- **Complete each step fully** — write state before proceeding
- **Each procedure must complete** before moving to the next

## Workflow

### Step 1: Ensure Todoist Sync

```
run @.clerk/procedures/ensure-todoist-sync.md
```

**Purpose:** Verify Todoist has all required projects before we route tasks.

```
✓ Verify: All area projects exist in Todoist
✗ On fail: User declined to create → abort workflow
```

### Step 2: Collect Inputs

```
run @.clerk/procedures/collect-inputs.md
```

**Purpose:** Gather items from all sources into PROCESSING.md.

```
✓ Checkpoint: Items exist in PROCESSING.md "Incoming" section
✗ On fail: No items to process → workflow complete (nothing to do)
```

### Step 3: Input Triage

```
run @.clerk/procedures/input-triage.md
```

**Purpose:** Classify items as #task, #note, or #instruction.

```
✓ Checkpoint: All items have classification tags (#task/#note/#instruction)
✓ Checkpoint: Classified items are #processing or #blocked
✗ On fail: Some items unclassified → will be handled in review-blocked
```

### Step 4: Process Categorized

```
run @.clerk/procedures/process-categorized.md
```

**Purpose:** Enrich classified items with metadata (destination, priority, etc.).

```
✓ Checkpoint: All #processing items are now #ready-to-review or #blocked
✗ On fail: Some items still #processing → continue (will retry)
```

### Step 5: Review Blocked

```
if has_blocked_items(PROCESSING_MD):
    run @.clerk/procedures/review-blocked.md
```

**Purpose:** Resolve any #blocked items with user input.

```
✓ Checkpoint: No #blocked items remain (all resolved or skipped)
✗ On fail: User skipped items → logged, continue
```

### Step 6: Review Categorized

```
run @.clerk/procedures/review-categorized.md
```

**Purpose:** Present processed items for user approval (batches of 5).

```
✓ Checkpoint: All #ready-to-review items are now #ready-to-commit or skipped
✗ On fail: User made corrections → items re-processed inline
```

### Step 7: Commit Reviewed

```
run @.clerk/procedures/commit-reviewed.md
```

**Purpose:** Execute approved actions (create tasks, write notes, run instructions).

```
✓ Checkpoint: PROCESSING.md "Ready to Commit" section is empty
✓ Checkpoint: ACTION_LOG.md updated with session summary
✗ On fail: Some items in #error → return to review-blocked
```

### Step 8: Handle Errors (if any)

```
if has_error_items(PROCESSING_MD):
    run @.clerk/procedures/review-blocked.md
    goto Step 7
```

### Step 9: Version Control

```
run @.clerk/procedures/version-control.md
```

**Purpose:** Commit vault changes to git with user approval.

```
✓ On commit: Changes committed as "Daily snapshot: YYYY-MM-DD"
✓ On skip: User declined, changes remain uncommitted
✓ On no changes: Nothing to commit
✗ On secrets detected: Abort commit, warn user
```

### Step 10: Complete

```
✓ Verify: PROCESSING.md has no items in any section
→ Workflow complete
```

## State Diagram

```
[Start]
    │
    ▼
[ensure-todoist-sync] ──(fail)──► [Abort]
    │
    ▼
[collect-inputs]
    │
    ▼
[input-triage]
    │
    ▼
[process-categorized]
    │
    ▼
[review-blocked] ◄────────────────┐
    │                             │
    ▼                             │
[review-categorized]              │
    │                             │
    ▼                             │
[commit-reviewed] ──(errors)──────┘
    │
    ▼
[version-control]
    │
    ▼
[Complete]
```

## Recovery

If workflow is interrupted at any point:

1. **State is preserved** — PROCESSING.md contains current state of all items
2. **Resume by re-running** — "process backlog" will pick up where it left off
3. **Manual recovery** — Individual procedures can be run directly if needed

### Recovery scenarios:

| Interruption Point | State in PROCESSING.md | Resume Behavior |
|--------------------|------------------------|-----------------|
| During collect | Some items in Incoming | Re-collect remaining sources |
| During triage | Items with #unclassified | Re-run triage |
| During processing | Items with #processing | Re-run process-categorized |
| During review | Items with #ready-to-review | Re-run review-categorized |
| During commit | Items with #ready-to-commit | Re-run commit-reviewed |
| After errors | Items with #error | Start with review-blocked |
| During version-control | PROCESSING.md empty | Re-run version-control |

## Examples

**Scenario:** Normal processing

1. User: "process backlog"
2. ensure-todoist-sync: All projects exist ✓
3. collect-inputs: 8 items collected from BACKLOG.md
4. input-triage: 6 tasks, 2 notes classified
5. process-categorized: All items enriched
6. review-blocked: 1 blocked item resolved
7. review-categorized: User approves batches of 5
8. commit-reviewed: 7 tasks created, 1 note written
9. version-control: User approves → committed as "Daily snapshot: 2026-01-20"
10. Complete: "Processed 8 items. Created 7 tasks, 1 note. Committed to git."

---

**Scenario:** Interrupted during review

1. User: "process backlog"
2. Steps 1-5 complete
3. User reviews first batch, approves
4. [Connection lost]
5. Later: User: "process backlog"
6. State recovered from PROCESSING.md
7. Resumes at review-categorized with remaining items

---

**Scenario:** No items to process

1. User: "process backlog"
2. ensure-todoist-sync: OK
3. collect-inputs: 0 items found
4. Complete: "No pending items to process."

---

**Scenario:** Todoist sync fails

1. User: "process backlog"
2. ensure-todoist-sync: Missing projects, user declines to create
3. Abort: "Cannot proceed without required Todoist projects."
