# Draft PRD

Collaboratively draft a PRD through context mapping, structured interviewing, and iterative refinement.

## Contract

**Pre-conditions:**
- User provides initial context (brain dump, meeting link, Linear project, Slack thread, verbal description, or any combination)
- Target area exists in SCHEMA.md (or user specifies one)
- Area has a `templates_examples/` folder with `prd-template.md` (optional — falls back to generic structure)

**Post-conditions:**
- Project folder exists at `{area}/projects/{project-kebab}/`
- PRD file exists at `{area}/projects/{project-kebab}/PRD-{project-kebab}.md`
- PRD state file exists at `_state/prd-draft-{project-kebab}.md` (removed on completion)
- Open questions are persisted in the PRD itself (Section 2.3)
- ACTION_LOG.md updated

**Errors:**
- Area not in SCHEMA.md → ask user to specify area
- Project folder already exists with PRD → offer to continue editing or start fresh
- Session interrupted → state persisted in `_state/prd-draft-{project-kebab}.md` for recovery

## Triggers

| Command | Action |
|---------|--------|
| "draft PRD" | Run this workflow |
| "new PRD" | Run this workflow |
| "draft PRD for X" | Run this workflow with project name X |
| "help me write a PRD" | Run this workflow |

## Critical Rules

- **Persist early, persist often** — write to the PRD file after every significant change, not just at the end
- **State file is the recovery point** — tracks current phase, answered questions, and pending questions
- **One question at a time during interviews** — depth over breadth, follow valuable threads
- **Batch PRD updates in groups of up to 5 changes** — don't rewrite the whole doc every exchange
- **3 interview rounds max before offering to finalize** — then user can continue or move to review
- **Generate open questions before interviewing** — the first draft of questions lives in the PRD before any Q&A
- **The PRD should have substance even with zero answers** — use available context to form a real opinion

## Workflow

### Phase 0: Setup

```
1. Parse user input for:
   - project_name (ask if not provided)
   - target_area (infer from context, ask if ambiguous)
   - initial_context (everything the user provided)

2. Check for existing state:
   if exists(_state/prd-draft-{project-kebab}.md):
       load state, resume at saved phase
       inform user: "Found a draft in progress for {project_name}. Resuming."

3. Create project if needed:
   if not exists({area}/projects/{project-kebab}/):
       run @.clerk/procedures/create-project.md

4. Load templates and examples:
   template = read({area}/templates_examples/prd-template.md)
       ?? read generic PRD structure from this procedure's template section
   examples = glob({area}/templates_examples/example-prd-*.md)

5. Initialize state file:
   write _state/prd-draft-{project-kebab}.md with:
       - project_name
       - target_area
       - current_phase: "context-gathering"
       - raw_context: (initial user input)
       - questions_asked: []
       - questions_answered: []
       - questions_open: []
       - interview_round: 0
```

```
✓ Verify: project folder exists, state file exists
✗ On fail: abort with specific error
```

### Phase 1: Context Gathering

**Purpose:** Pull in all available context from tools and sources before writing anything.

```python
context_sources = []

# 1. User's raw input
context_sources.append(initial_context)

# 2. If a Granola meeting was referenced or linked:
if granola_link or meeting_reference:
    meeting = mcp_granola.get_meeting(meeting_id)
    transcript = mcp_granola.get_transcript(meeting_id)
    notes = mcp_granola.get_meeting_notes(meeting_id)
    context_sources.append(meeting, transcript, notes)

# 3. If a Linear project was referenced:
if linear_reference:
    project = mcp_linear.get_project(query, includeResources=True, includeMilestones=True)
    context_sources.append(project)

# 4. If Slack threads were referenced:
if slack_reference:
    thread = mcp_slack.slack_read_thread(channel_id, message_ts)
    context_sources.append(thread)

# 5. Check area's knowledge base (if available):
#    e.g., Amplemarket KB via Pylon MCP
if area_has_kb_tools:
    kb_articles = search_kb(project_name_keywords)
    context_sources.append(kb_articles)

# 6. Search Featurebase for related user requests:
if featurebase_available:
    similar = mcp_featurebase.get_similar_submissions(project_name)
    context_sources.append(similar)

# 7. Check area folder for existing related content:
related_files = glob({area}/**/*.md matching project keywords)
context_sources.append(related_files)

# 8. If codebase is available (checked out locally):
#    Use sub-agent to explore relevant code
if codebase_available:
    spawn explore_agent("Find code related to {project_name keywords}")
    context_sources.append(exploration_results)
```

```
✓ Verify: context_sources has at least one entry
✗ On fail: continue with user's raw input only
```

**Update state:**
```
state.raw_context = compiled_context
state.current_phase = "mapping"
```

### Phase 2: Context Mapping

**Purpose:** Map gathered context to template sections. Write the first draft.

```python
# 1. Read the template structure
template_sections = parse_template(template)

# 2. For each section, extract what we know:
mapped = {}
for section in template_sections:
    mapped[section] = extract_relevant_context(context_sources, section)
    # Use LLM reasoning to map context fragments to template sections
    # Be opinionated — make a best guess, mark assumptions

# 3. Identify gaps
gaps = [section for section in template_sections if not mapped[section]]
partial = [section for section in template_sections if mapped[section].confidence < 0.7]

# 4. Generate initial open questions
#    These are substantive questions, not "what do you want here?"
#    Bad: "What is the business value?"
#    Good: "You mentioned enterprise customers need X — is the primary driver
#           deal size expansion, or reducing churn in existing accounts?"
open_questions = generate_questions(gaps, partial, context_sources)

# 5. Write the first draft of the PRD
#    - Fill in what we know with substance and opinion
#    - Mark assumptions with [ASSUMPTION: ...]
#    - Leave sections genuinely empty only if zero signal
#    - Place open questions in Section 2.3

write PRD-{project-kebab}.md
```

**Present to user:**
```
Here's what I've mapped from the available context:

**Strong coverage:** {sections with good data}
**Partial coverage:** {sections with some data, marked assumptions}
**Gaps:** {sections with no data}

I've written {N} open questions into the PRD.
Want to walk through them together, or should I keep them open for now?
```

```
✓ Verify: PRD file written, open questions in Section 2.3
✗ On fail: write what we have, note failures in state
```

**Update state:**
```
state.current_phase = "interviewing"
state.interview_round = 0
state.questions_open = open_questions
```

### Phase 3: Structured Interview

**Purpose:** Walk through open questions one at a time, building on answers.

**Interview technique:** Each question should:
- Reference specific context ("You mentioned X in the meeting...")
- Be specific and answerable ("Is the primary user persona SDR managers or individual SDRs?")
- Build on previous answers ("Given that the audience is SDR managers, how should success be measured?")
- Suggest a hypothesis when possible ("I think the success metric might be X — does that resonate?")

```python
for round in range(1, 4):  # Max 3 rounds
    state.interview_round = round

    # Select up to 5 questions for this round
    # Prioritize: gaps in Problem Statement > Solution > Milestones > Roll-out
    batch = select_priority_questions(state.questions_open, limit=5)

    for question in batch:
        # Present one question at a time
        present_question(question)
        answer = await_user_response()

        if answer == "skip" or answer == "keep open":
            # Question stays in open questions
            continue

        # Process the answer
        state.questions_answered.append((question, answer))
        state.questions_open.remove(question)

        # Determine if answer changes existing sections significantly
        affected_sections = identify_affected_sections(answer, current_prd)

        if affected_sections:
            # Rewrite affected sections incorporating the new info
            update_prd_sections(affected_sections, answer)
            # Persist immediately
            write PRD-{project-kebab}.md

        # Generate follow-up questions if the answer opened new threads
        new_questions = generate_followups(answer, context)
        state.questions_open.extend(new_questions)

    # After each round of 5, update the full PRD
    rewrite_prd_with_all_new_context()
    write PRD-{project-kebab}.md

    # Update state
    state.current_phase = f"interview-round-{round}"
    write state file

    # Check if user wants to continue
    if round < 3:
        ask: "{N} open questions remain. Continue interviewing, or finalize?"
        if user_says_finalize:
            break
    else:
        inform: "3 rounds complete. Moving to finalization with {N} open questions remaining."
```

```
✓ Verify: PRD updated after each round, state persisted
✗ On fail: state file preserves progress for recovery
```

### Phase 4: Finalization

**Purpose:** Clean up the PRD, ensure open questions are actionable, and trigger review.

```python
# 1. Final PRD pass
#    - Remove [ASSUMPTION] markers where answers confirmed them
#    - Consolidate open questions with owners where possible
#    - Ensure milestones are sequenced logically
#    - Add "Next Steps" to open questions section
#    - Clean up formatting

# 2. Make open questions actionable
for question in state.questions_open:
    question.suggested_owner = infer_owner(question)
    question.suggested_action = infer_next_step(question)
    # e.g., "Needs technical discovery spike" or "Discuss with design in sync"

# 3. Write final PRD
write PRD-{project-kebab}.md

# 4. Present summary
present:
    "PRD draft complete for {project_name}."
    "Sections filled: {N}/{total}"
    "Open questions: {N} (with suggested owners and next steps)"
    ""
    "Ready for review? I can run a multi-perspective review with:"
    "- Tech Lead / EM perspective"
    "- Head of Product perspective"
    "- Design Lead perspective"

# 5. If user approves review:
run @.clerk/procedures/review-prd.md with path=PRD-{project-kebab}.md

# 6. Clean up state
delete _state/prd-draft-{project-kebab}.md

# 7. Log
append to ACTION_LOG.md:
    ### {date} Draft PRD
    - Created: {area}/projects/{project-kebab}/PRD-{project-kebab}.md
    - Interview rounds: {N}
    - Questions answered: {N}
    - Questions remaining open: {N}
    - Review: {triggered | skipped}
```

```
✓ Verify: PRD file is complete, state file cleaned up
✗ On fail: keep state file for recovery
```

## State File Format

`_state/prd-draft-{project-kebab}.md`:

```markdown
# PRD Draft State: {Project Name}

## Metadata
- project: {project-kebab}
- area: {area}
- phase: {context-gathering | mapping | interview-round-N | finalizing | review}
- created: {ISO date}
- updated: {ISO date}

## Raw Context
{All gathered context, compiled}

## Questions Asked
1. {question} → {answer summary}
2. {question} → {answer summary}

## Questions Open
1. {question} — suggested owner: {person/role}
2. {question} — suggested owner: {person/role}

## Sections Updated
- [x] 1.1 Business Value (round 1)
- [x] 1.2 Audience (round 2)
- [ ] 2.1 Solution Approach
- ...
```

## Interview Question Generation Guidelines

Questions should follow progressive depth:

**Round 1 — Problem framing:**
- Validate the core problem ("Is the primary pain point X or Y?")
- Clarify the audience ("When you say enterprise customers, do you mean...")
- Test assumptions from gathered context ("The meeting transcript suggests Z — is that still the direction?")
- Surface hidden constraints ("Are there compliance, timeline, or resource constraints I should know about?")
- Quantify impact ("Do you have data on how often this problem occurs?")

**Round 2 — Solution shaping:**
- Challenge the approach ("Have you considered alternative X? What made you lean toward Y?")
- Probe milestone boundaries ("Where's the line between M1 and M2?")
- Test success criteria ("Would you consider it successful if only metric X moved?")
- Surface competitor context ("How do competitors handle this?")
- Identify risks ("What's the biggest thing that could go wrong?")

**Round 3 — Sharpening:**
- Scope discipline ("Is X truly needed for v1, or could it wait?")
- Operational readiness ("How will you roll this out?")
- Stakeholder gaps ("Who else needs to weigh in before this is final?")
- Edge cases ("What happens when a user does X in situation Y?")
- Dependencies ("What needs to be true for this to ship?")

## Recovery

If session is interrupted:
1. State persists in `_state/prd-draft-{project-kebab}.md`
2. PRD persists in `{area}/projects/{project-kebab}/PRD-{project-kebab}.md`
3. Re-triggering "draft PRD" or "draft PRD for X" detects state and resumes
4. Another model/device can pick up from the state file — all context is persisted

## Examples

**Trigger:** "draft PRD for Contact Edits under amplemarket"

1. Creates `amplemarket/projects/contact-edits/` (if needed)
2. Loads `amplemarket/templates_examples/prd-template.md` + examples
3. Searches Featurebase, Linear, Amplemarket KB for "contact edits"
4. Maps gathered context → writes first draft with 8 open questions
5. Interviews user: 3 rounds, 12 questions answered, 3 kept open
6. Finalizes: `amplemarket/projects/contact-edits/PRD-contact-edits.md`
7. Offers multi-perspective review

---

**Trigger:** "draft PRD" (no project specified)

1. Asks: "What's the project name and which area does it belong to?"
2. Proceeds as above

---

**Trigger:** Meeting transcript pasted + "help me write a PRD for this"

1. Extracts project name and area from transcript content
2. Uses full transcript as primary context source
3. Proceeds as above

---

**Recovery:** User starts on laptop, continues on phone

1. Laptop session: completes Phase 1-2, answers 5 questions in Phase 3, session drops
2. Phone session: "draft PRD for Contact Edits"
3. Detects state file → "Found draft in progress. You were in interview round 2. 6 open questions remain. Continue?"
4. Resumes interviewing from where it left off
