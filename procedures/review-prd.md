# Review PRD

Multi-perspective PRD review using isolated sub-agents for fresh-eyes feedback.

**References:** @.clerk/config/prd-config.md · @.clerk/references/review-rubrics.md

## Contract

**Pre-conditions:**
- PRD file exists at the specified path

**Post-conditions:**
- Review synthesis appended/written to PRD or companion file
- Open questions updated with reviewer-surfaced questions
- "Must-fix before kickoff" checklist generated
- ACTION_LOG.md updated

**Errors:**
- PRD not found → abort with path error
- Sub-agent fails → log, continue with remaining reviewers
- Session interrupted → state persisted for recovery

## Triggers

| Command | Action |
|---------|--------|
| "review PRD" | Run on most recent draft |
| "review PRD {path}" | Run on specified file |
| "review PRD for {project}" | Find PRD in project folder |
| "review PRD (lean\|deep)" | Run with explicit mode |
| (auto) | Triggered by draft-prd.md at Phase 4 |

## Runtime Protocol

### 0. Init

```
resolve: prd_path (from input, state, or project folder search)
read: PRD content
load: {area}/templates_examples/prd-template.md (if exists)
load: {area}/templates_examples/example-prd-*.md (if any)
detect: mode (lean | standard | deep — default: standard)
check: _state/prd-review-{project}.md → resume if exists
init: state file
```

### 1. Structural Pre-scan

Before launching reviewers, do a quick structural check:

```
for each template section:
    coverage: filled | partial | empty
    evidence_tags: count of [source], [inferred], [assumption]
    untagged_claims: count

output: section_coverage_map + weak_sections list
```

This focuses reviewers — in **standard** mode, reviewers get the coverage map so they can prioritize weak areas. In **deep** mode, they do a full review regardless.

### 2. Launch Reviewers

Each reviewer is an isolated sub-agent receiving ONLY:
1. The PRD document
2. The template (structural reference)
3. Example PRDs — **only if pre-scan found low structural confidence** (lean/standard); always included in deep mode
4. Their role-specific rubric (from @.clerk/references/review-rubrics.md)
5. Section coverage map (standard/deep only)
6. **NO conversation history**

**Reviewer roster by mode:**

| Mode | Reviewers |
|------|-----------|
| lean | Head of Product only |
| standard | Tech Lead + Head of Product + Design Lead |
| deep | All 3 + adjudication pass (confirm with user first — see §2a) |

Model preference per prd-config.md § Platform Notes (default: strongest available, fallback chain: opus → sonnet → haiku).

### 2a. Cost-control checkpoint (deep mode only)

Before launching reviewers in deep mode, confirm with the user:

```
Deep review will launch 3 parallel reviewers (full rubric, all examples)
+ adjudication pass if disagreements arise.
This uses significantly more context than standard review.

Proceed with deep review, or switch to standard?
```

If auto-triggered from `draft-prd.md` Phase 4, inherit the mode from the draft — but still confirm if deep.

**Sub-agent prompt structure:**

> You are a {role} reviewing a PRD cold — no prior context.
> Review using the rubric below. Be substantive and specific.
> Challenge content, not just format. Map every concern to a
> specific PRD section with severity (blocking | non-blocking).
>
> After your prose review, emit a structured concerns list
> using the **Reviewer Output Schema** (see prd-config.md § Reviewer Output Schema).
>
> {ROLE_RUBRIC from review-rubrics.md}
>
> PRD: {content}
> Template: {template}
> Examples: {examples — include only if pre-scan shows low structural confidence, or if deep mode}
> Coverage map: {section_coverage_map}

Launch reviewers in parallel via Task tool.

```
✓ Verify: at least 1 review returned
✗ On fail: retry failed reviewer once, then continue without
```

### 3. Synthesize

```
1. Parse structured YAML blocks from each reviewer response (see prd-config.md § Reviewer Output Schema)
2. Deduplicate: concerns raised by 2+ reviewers → elevate as cross-cutting
3. Categorize: blocking vs. non-blocking
4. Each concern already has: section + severity + owner + action (from schema)
5. Extract new questions from reviewers
6. Generate "must-fix before kickoff" checklist:
   - Feasibility blockers (from Tech Lead)
   - Missing/unmeasurable metrics (from HoP)
   - Rollout risks (from Tech Lead + HoP)
   - Dependency owners unassigned (from Tech Lead)
   - User flows incomplete (from Design Lead)
```

**Deep mode only — Adjudication pass:**
When reviewers disagree on severity or recommendation, run a short synthesis sub-agent that:
- Lists the conflicting positions
- Recommends a resolution with reasoning
- Flags genuine trade-offs for user decision

### 4. Present

```
## PRD Review: {project_name}

### Cross-cutting themes (flagged by 2+ reviewers)
{elevated issues}

### Must-fix before kickoff
- [ ] {concern — section — owner}

### Blocking concerns ({N})
{prioritized, with section + reviewer source}

### Suggestions ({N})
{non-blocking improvements}

### New questions ({N})
{from reviewers, with suggested owner}

Options:
1. Address blocking concerns now (I'll update the PRD)
2. Add reviewer questions to open questions
3. See full review from a specific reviewer
4. Export all reviews as companion doc
```

### 5. Incorporate (if user chooses)

Walk through blocking concerns one at a time. For each:
- Present concern with context
- Await user input
- Update PRD section + tag evidence
- Write to disk immediately

Update open questions in PRD with reviewer-surfaced questions.

### 6. Log & Clean Up

```
append ACTION_LOG.md:
    ### {date} Review PRD
    - Reviewed: {prd_path}
    - Mode: {mode}
    - Reviewers: {list}
    - Blocking: {N} / Addressed: {N}
    - New questions: {N}

delete _state/prd-review-{project}.md
```

## Recovery

State file tracks which reviewers completed, which concerns are addressed. Resume re-runs only failed/pending reviewers.

## Platform Notes

**Claude Code:** Sub-agents via Task tool. Model preference per prd-config.md.

**Cursor:** Each reviewer prompt is self-contained. Use different models per reviewer for diversity. All prompts work without conversation context — copy prompt + rubric + PRD content.
