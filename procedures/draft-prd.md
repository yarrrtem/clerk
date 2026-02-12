# Draft PRD

Collaboratively draft a PRD through context gathering, structured interviewing, and iterative refinement.

**References:** @.clerk/config/prd-config.md · @.clerk/references/interview-heuristics.md · @.clerk/references/prd-evidence-guide.md

## Contract

**Pre-conditions:**
- User provides initial context (brain dump, meeting, Linear project, Slack thread, any combination)
- Target area exists in SCHEMA.md (or user specifies one)

**Post-conditions:**
- Project folder at `{area}/projects/{project-kebab}/`
- PRD at `{area}/projects/{project-kebab}/PRD-{project-kebab}.md`
- State file at `_state/prd-draft-{project-kebab}.md` (removed on completion)
- ACTION_LOG.md updated

**Errors:**
- Area not in SCHEMA.md → ask user
- PRD already exists → offer to continue or start fresh
- Session interrupted → state persisted for recovery on any device

## Triggers

| Command | Action |
|---------|--------|
| "draft PRD" | Run this workflow |
| "new PRD" | Run this workflow |
| "draft PRD for X" | Run with project name X |
| "draft PRD for X (lean\|deep)" | Run with explicit mode |
| "help me write a PRD" | Run this workflow |

## Runtime Protocol

### 0. Init

```
parse: project_name, target_area, mode (default: standard)
check: _state/prd-draft-{project}.md → resume if exists
create project: run @.clerk/procedures/create-project.md (if needed)
load: {area}/templates_examples/prd-template.md (if exists)
load: {area}/templates_examples/example-prd-*.md (if any)
load: {area}/_config.md → tool role mappings + context hints (if exists)
detect: probe each configured tool role for availability (see prd-config.md § Capability Detection)
init: state file
```

### 1. Gather → Digest

Pull context from available tools (per `{area}/_config.md`). Compress each into digest format.

**Source checklist** — walk configured tool roles, skip any that are offline:
- [ ] User's raw input (always available)
- [ ] **meetings** — if referenced (transcript, notes, summary)
- [ ] **issue_tracker** — if referenced (project descriptions, milestones, specs)
- [ ] **chat** — if referenced (threads, prior decisions)
- [ ] **knowledge_base** — search for project keywords
- [ ] **feedback_board** — search for similar user requests
- [ ] Area folder → related files via Glob/Grep (always available)
- [ ] **codebase** — explore via sub-agent if available (**foreground only** — needs file permissions)
- [ ] **web** — fetch external URLs if referenced

**After each fetch, verify the result** (see SYSTEM.md § Failure Escalation Policy):

```
for each source attempted:
    if result is error, empty, or permission-denied:
        log: ✗ {role}: {error reason}
        tell user immediately — offer paste/skip/retry
    else:
        log: ✓ {role}: {N findings}
        compress into digest

Present fetch summary before proceeding to Map phase:
    "Gathered context from {N} sources. {M} failed:"
    - {failed source}: {reason} — paste content or skip?

Do NOT proceed to Map until user has seen and resolved all failures.
```

**Output:** Context digest in state file (~2-10K tokens depending on mode). Keep source pointers, not full content.

### 2. Map → Draft

For each template section:
1. Extract relevant digest fragments
2. Score confidence: **high** | **medium** | **low** | **none** (see prd-config.md)
3. Write content — be opinionated, mark evidence tags: `[source: X]`, `[inferred]`, `[assumption]`
4. Leave sections genuinely empty only if confidence = none

Generate open questions from **low** and **none** confidence sections. Questions must be:
- Specific and answerable (not "what's the business value?")
- Reference available context ("You mentioned X — is the primary driver Y or Z?")
- Suggest a hypothesis when possible

**Write the PRD file.** Write open questions into the Open Questions section (find by heading, don't hardcode section number).

**Present to user:**
```
Mapped context to PRD. Coverage:
- Strong: {sections}
- Partial: {sections} [assumption-tagged]
- Gaps: {sections}
- Open questions: {N}

Walk through questions together, or keep them open?
```

**Quality gate:** Check section confidence against mode minimums (prd-config.md § Draft Quality Gate). Warn if below threshold.

### 3. Interview

One question at a time. Build on previous answers. See @.clerk/references/interview-heuristics.md for question generation by round.

**Loop per round (max rounds per mode):**

```
for each question (up to 5 per round):
    present question
    await answer
    if skip/keep-open → leave in open questions, continue
    if answered:
        update affected PRD sections
        tag new content with evidence type
        generate ≤2 follow-up questions (respect question debt limit)
        write PRD to disk
        update state file

after round:
    recompute section confidence scores
    check quality gate
    ask: "Continue interviewing, or finalize?"
```

**Limits (from prd-config.md):**
- Max follow-ups per answer: 2
- Max total open questions: 15
- Question debt limit: 10 — prune lowest-priority if exceeded

### 4. Finalize

```
1. Remove confirmed [assumption] tags
2. Make open questions actionable: add suggested owner + next step
3. Generate "must-resolve before kickoff" checklist from remaining gaps
4. Apply quality gate — warn if sections below minimum
5. Write final PRD
6. Present summary:
   - Sections filled: N/total
   - Open questions: N (with owners)
   - "Ready for review? I can run Tech Lead, Head of Product, and Design Lead reviews."
7. If approved → run @.clerk/procedures/review-prd.md
8. Clean up state file
9. Append to ACTION_LOG.md
```

## Recovery

State persists in `_state/prd-draft-{project}.md`. PRD persists in project folder. Re-triggering detects state and resumes. Another model/device can pick up — all context is in the digest + state, not conversation memory.

## Examples

**"draft PRD for Contact Edits under amplemarket"**
→ Creates project, gathers from Featurebase + Linear + KB, maps to template, interviews 2 rounds, finalizes, offers review.

**"draft PRD for Contact Edits (lean)"**
→ Same setup, 1 interview round, 3 questions max, 1 reviewer (HoP only).

**Meeting transcript pasted + "help me write a PRD"**
→ Extracts project name + area from content, uses transcript as primary source, proceeds normally.

**Resume on different device:** "draft PRD for Contact Edits"
→ Detects state file, reports phase + open questions, resumes.
