# Review PRD

Multi-perspective PRD review using isolated sub-agents for fresh-eyes feedback.

## Contract

**Pre-conditions:**
- PRD file exists at the specified path
- Area's `templates_examples/` folder exists with `prd-template.md` (optional — reviewer adapts)

**Post-conditions:**
- Review feedback appended to the PRD file (or written as companion file)
- Open questions in the PRD are updated with reviewer-surfaced questions
- State file tracks review progress for recovery
- ACTION_LOG.md updated

**Errors:**
- PRD file not found → abort with path error
- Sub-agent fails → log failure, continue with remaining reviewers
- Session interrupted → state persisted for recovery

## Triggers

| Command | Action |
|---------|--------|
| "review PRD" | Run on most recent PRD draft |
| "review PRD {path}" | Run on specified file |
| "review PRD for {project}" | Find and review PRD in project folder |
| (auto) | Triggered by draft-prd.md at Phase 4 |

## Design Principles

**Context isolation is the core technique.** Each reviewer sub-agent receives ONLY:
1. The PRD document
2. The template (for structural reference)
3. Example PRDs from the area's `templates_examples/`
4. Their role-specific review rubric (below)
5. NO conversation history — completely fresh perspective

**Why this works:**
- Eliminates anchoring bias from the drafting conversation
- Each reviewer applies their own lens without being influenced by others
- Mimics a real review cycle where different stakeholders read the doc cold
- Different model choices (Opus, Sonnet, or external models in Cursor) add genuine diversity

**Model selection:**
- Default: Use `opus` for all reviewers (strongest reasoning, best for substantive critique)
- In Cursor: Can use GPT-5.2 or other models for additional diversity
- Each reviewer runs as an independent sub-agent via the Task tool

## Reviewers

### 1. Tech Lead / Engineering Manager

**Persona:** Senior engineer who has built and shipped complex systems. Skeptical of hand-waving. Wants to know what breaks, what's missing, and what's going to be harder than the PM thinks.

**Review focus:**

| Dimension | Key questions |
|-----------|---------------|
| **Feasibility** | Can each requirement be mapped to a known implementation pattern? Are there hidden spikes? |
| **Architecture impact** | What data model changes, new services, or API changes are implied but not stated? |
| **Dependencies** | What external teams, services, or vendors are needed? Are they listed with owners? |
| **Edge cases & failure modes** | Are happy path, error path, and degraded-state paths all described? |
| **Non-functional requirements** | Security, performance targets, observability, compliance — stated or missing? |
| **Scope discipline** | Are requirements independently testable? Can engineering estimate from what's written? |
| **Operability** | Feature flags, rollback plan, monitoring, incident response — addressed? |
| **Estimation readiness** | Could an engineer write a technical design doc from this PRD without guessing? |

**Red flags to call out:**
- Vague performance expectations ("fast", "responsive", "scalable")
- Missing data volume or scale assumptions
- Unstated migration or backward-compatibility needs
- Requirements that assume capabilities the current stack doesn't have
- No rollback plan for production issues

**Output format:**
```markdown
## Tech Lead Review

### Summary
{2-3 sentence overall assessment}

### Strengths
- {What's well-specified}

### Concerns (blocking)
- {Must be addressed before engineering kickoff}

### Suggestions (non-blocking)
- {Would improve the PRD but not required}

### Questions for the PM
- {Specific questions that need answers}

### Missing sections or details
- {What's absent that engineering needs}
```

---

### 2. Head of Product

**Persona:** Experienced product leader who evaluates whether this is the right thing to build, scoped correctly, and will move the metrics that matter. Pushes back on scope creep and vague success criteria. Thinks in terms of bets and trade-offs.

**Review focus:**

| Dimension | Key questions |
|-----------|---------------|
| **Strategic alignment** | Does this tie to a stated company objective? Is "why now" compelling? |
| **Problem validation** | Is the problem grounded in evidence, or opinion? Are user quotes/data cited? |
| **Success criteria quality** | Is there a primary metric? Is it measurable? Are targets specific with timelines? |
| **Scope discipline** | Is the MVP the smallest thing that tests the hypothesis? Is out-of-scope substantive? |
| **User story completeness** | Do primary use cases cover 80%+ of expected usage? Are JTBDs stated? |
| **Competitive context** | Is differentiation articulated? Is this table stakes or a differentiator? |
| **Opportunity cost** | What are we NOT doing by doing this? Is that acknowledged? |
| **Document quality** | Is language precise? Are assumptions labeled? Are open questions owned? |

**Red flags to call out:**
- Success criteria that aren't measurable ("improve engagement")
- No evidence for the problem (opinion-driven)
- Scope that grows across milestones without clear gates
- Missing "out of scope" section or one that's just filler
- Vague language: "simple", "intuitive", "seamless" without definition
- No competitive context when competitors exist

**Output format:**
```markdown
## Head of Product Review

### Summary
{2-3 sentence overall assessment — is this a good bet?}

### Strategic fit
- {How well does this align with stated goals?}

### Strengths
- {What's compelling about this PRD}

### Concerns (blocking)
- {Must be addressed before greenlighting}

### Scope check
- {Is the scope right? Too big? Too small? What would you cut or add?}

### Success criteria assessment
- {Are the metrics right? Measurable? Time-bound?}

### Questions for the PM
- {Strategic and product questions}
```

---

### 3. Design Lead

**Persona:** Senior designer who thinks in user journeys, not feature lists. Advocates for the user's experience across the full flow — including the boring parts (onboarding, errors, empty states). Challenges the PRD to define what the user actually does, not just what the system does.

**Review focus:**

| Dimension | Key questions |
|-----------|---------------|
| **User journey completeness** | Are entry points, happy path, error path, and exit points all defined? |
| **Information architecture** | Where does this live in the product? How does it relate to existing features? |
| **Interaction patterns** | Are inputs, validation, feedback, and confirmation patterns specified? |
| **Edge cases & empty states** | Zero-data state? Permission-denied? Content overflow? First-time user? |
| **Accessibility** | WCAG level stated? Screen reader, keyboard nav, color contrast considered? |
| **Content & copy direction** | Tone specified? Microcopy needs identified? Error message guidance? |
| **Cross-platform** | Target platforms listed? Responsive behavior defined? |
| **Design feasibility** | Timeline allows design exploration? Design system components identified? |

**Red flags to call out:**
- No user flow or journey described — only system behavior
- Missing empty states and error states
- "Intuitive" used without definition of what makes it intuitive
- No mention of existing design patterns that should be reused
- Accessibility not mentioned at all
- No consideration of the transition from current → new experience

**10-Point UX Critique (assess each):**
1. **Usability:** Can the proposed flows be completed efficiently?
2. **Navigation:** Is the information hierarchy logical and discoverable?
3. **Consistency:** Do interactions align with existing product patterns?
4. **Feedback:** Are system responses to user actions clearly defined?
5. **Error Prevention:** Are safeguards against mistakes specified?
6. **Accessibility:** Are inclusive design requirements explicit?
7. **Visual Hierarchy:** Is content priority defined?
8. **Cognitive Load:** Is complexity appropriate for the audience?
9. **Responsiveness:** Are multi-device behaviors addressed?
10. **Delight:** Are there opportunities for meaningful microinteractions?

**Output format:**
```markdown
## Design Lead Review

### Summary
{2-3 sentence overall assessment — is this designable?}

### User journey assessment
- {Are the flows complete? What's missing?}

### Strengths
- {What gives design a clear starting point}

### Concerns (blocking)
- {Must be addressed before design begins}

### UX critique (10-point)
| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| Usability | {N} | {brief note} |
| ... | ... | ... |

### Missing from design perspective
- {States, flows, or considerations not addressed}

### Questions for the PM
- {UX and flow questions}
```

## Workflow

### Step 1: Load context

```python
# 1. Find the PRD
prd_path = resolve_prd_path(user_input)
prd_content = read(prd_path)

# 2. Find template and examples
area = extract_area_from_path(prd_path)
template = read({area}/templates_examples/prd-template.md) ?? None
examples = glob({area}/templates_examples/example-prd-*.md)

# 3. Check for existing review state
state_path = _state/prd-review-{project-kebab}.md
if exists(state_path):
    load state, resume where left off
```

### Step 2: Run reviewers in parallel

```python
# Spawn 3 independent sub-agents, each with isolated context
# Use 'opus' model for substantive critique

reviewers = {
    "tech_lead": {
        "model": "opus",
        "context": [prd_content, template, examples, TECH_LEAD_RUBRIC],
        "prompt": TECH_LEAD_REVIEW_PROMPT
    },
    "head_of_product": {
        "model": "opus",
        "context": [prd_content, template, examples, HOP_RUBRIC],
        "prompt": HOP_REVIEW_PROMPT
    },
    "design_lead": {
        "model": "opus",
        "context": [prd_content, template, examples, DESIGN_RUBRIC],
        "prompt": DESIGN_LEAD_REVIEW_PROMPT
    }
}

# Launch all 3 in parallel via Task tool
results = parallel_launch(reviewers)
```

**Sub-agent prompt template:**
```
You are a {role} reviewing a PRD written by a product manager.
You are reading this document cold — you have no prior context about
the conversations or decisions that led to this draft.

Review the PRD using the rubric below. Be substantive and specific.
Challenge the content, not just the format. If something is unclear,
say what's unclear and why it matters. If something is missing, say
what's missing and what problems that creates.

Reference the template for structural expectations, and the examples
for quality benchmarks.

{ROLE_SPECIFIC_RUBRIC}

PRD to review:
{prd_content}

Template:
{template}

Examples for reference:
{examples}
```

```
✓ Verify: all 3 reviews returned
✗ On fail: log which reviewer failed, continue with available reviews
```

### Step 3: Synthesize feedback

```python
# 1. Compile all reviews
all_feedback = compile_reviews(results)

# 2. Deduplicate concerns across reviewers
#    If multiple reviewers flag the same issue, elevate it
cross_cutting = find_overlapping_concerns(all_feedback)

# 3. Extract new questions from all reviews
new_questions = extract_questions(all_feedback)

# 4. Categorize feedback
blocking = [f for f in all_feedback if f.severity == "blocking"]
suggestions = [f for f in all_feedback if f.severity == "non-blocking"]
```

### Step 4: Present to user

```python
# Present a synthesis, not raw dumps

present:
    "## PRD Review Complete: {project_name}"
    ""
    "### Cross-cutting themes"
    "{issues raised by multiple reviewers}"
    ""
    "### Blocking concerns ({N})"
    "{prioritized list}"
    ""
    "### Non-blocking suggestions ({N})"
    "{prioritized list}"
    ""
    "### New questions surfaced ({N})"
    "{questions from reviewers}"
    ""
    "Would you like to:"
    "1. Address blocking concerns now (I'll update the PRD)"
    "2. Add reviewer questions to the PRD's open questions"
    "3. See the full review from a specific reviewer"
    "4. Export all reviews as a companion document"
```

### Step 5: Incorporate feedback

```python
if user_wants_to_address:
    # Walk through blocking concerns one by one
    for concern in blocking:
        present concern with context
        answer = await_user_response()
        if answer:
            update_prd_sections(concern.affected_sections, answer)

    # Update open questions in PRD
    update_open_questions(prd_path, new_questions)

    # Write updated PRD
    write prd_path
```

### Step 6: Log & clean up

```python
append to ACTION_LOG.md:
    ### {date} Review PRD
    - Reviewed: {prd_path}
    - Reviewers: Tech Lead, Head of Product, Design Lead
    - Blocking concerns: {N}
    - Suggestions: {N}
    - New questions: {N}
    - Concerns addressed: {N}

delete _state/prd-review-{project-kebab}.md
```

## State File Format

`_state/prd-review-{project-kebab}.md`:

```markdown
# PRD Review State: {Project Name}

## Metadata
- prd_path: {path}
- started: {ISO date}
- phase: {launching-reviewers | synthesizing | presenting | incorporating}

## Reviews Completed
- [x] Tech Lead
- [x] Head of Product
- [ ] Design Lead

## Blocking Concerns
1. {concern} — addressed: yes/no
2. {concern} — addressed: yes/no

## New Questions Surfaced
1. {question} — added to PRD: yes/no
```

## Running in Cursor

This procedure is designed to work in both Claude Code and Cursor:

- **Claude Code:** Sub-agents use the Task tool with `model: "opus"` for isolated review
- **Cursor:** Can use any available model (GPT-5.2, Gemini, etc.) for reviewer diversity
  - Each reviewer prompt is self-contained — copy the prompt + rubric + PRD content
  - No dependency on conversation context
  - Consider using different models for each reviewer for maximum perspective diversity

**Recommended model pairing in Cursor:**
- Tech Lead → GPT-5.2 (strong at systematic analysis)
- Head of Product → Claude Opus (strong at strategic reasoning)
- Design Lead → Claude Opus or Gemini (strong at user experience reasoning)

## Recovery

1. State persists in `_state/prd-review-{project-kebab}.md`
2. Re-triggering "review PRD" detects state and resumes
3. Individual reviewer results are cached in state file
4. If only 1 of 3 reviewers failed, re-run just that one

## Examples

**Trigger:** "review PRD" (after drafting)

1. Picks up most recent PRD from state
2. Launches 3 reviewers in parallel
3. Synthesizes: 2 blocking concerns, 5 suggestions, 3 new questions
4. User addresses blocking concerns → PRD updated
5. New questions added to Section 2.3

---

**Trigger:** "review PRD amplemarket/projects/contact-edits/PRD-contact-edits.md"

1. Loads specified file
2. Finds template at `amplemarket/templates_examples/prd-template.md`
3. Loads example PRDs from `amplemarket/templates_examples/`
4. Runs full review cycle

---

**Trigger:** "review PRD for roles and permissions"

1. Searches for PRD file matching "roles-and-permissions"
2. Finds `amplemarket/projects/roles-and-permissions/PRD-roles-and-permissions.md`
3. Runs full review cycle
