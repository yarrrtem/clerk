# Analyze Corrections

**Goal:** Surface patterns from corrections and propose checklist updates.

**Inputs:** @../ACTION_LOG.md entries with corrections

**Trigger:** Weekly, or after N corrections logged (e.g., 10)

**Outcome:** Proposed updates to classification signals in @../SCHEMA.md

## Procedure

1. Read @../ACTION_LOG.md entries that have corrections (original classification ≠ final classification)

2. Identify patterns:
   - Which signals led to misclassification?
   - Which words/patterns were missing from the checklist?

3. Generate proposed updates:
   - "Add 'consider' to task signals? (Misclassified 5x as #note, was #task)"
   - "Remove 'review' from note signals? (Often a task)"

4. Present proposals to user for approval

5. User approves or rejects each proposal

6. Approved changes are written to @../SCHEMA.md
