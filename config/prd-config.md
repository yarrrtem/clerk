# PRD Workflow Configuration

Shared configuration for `draft-prd.md` and `review-prd.md`.

## Execution Modes

| Mode | When to use | Interview | Review | Context budget |
|------|-------------|-----------|--------|----------------|
| **lean** | Quick sketch, time-constrained, early-stage idea | 1 round, 3 questions | 1 reviewer (HoP) | ~2K tokens digest |
| **standard** (default) | Normal PRD drafting | 2 rounds, 5 questions each | 3 reviewers, structural pass | ~5K tokens digest |
| **deep** | High-stakes initiative, complex domain | 3 rounds, 5 questions each | 3 reviewers + adjudication + deep pass on weak sections | ~10K tokens digest |

Default: **standard**. User can override: "draft PRD for X (lean)" or "deep review PRD".

## Context Budgeting

Raw inputs (transcripts, threads, codebases) MUST be compressed into a **context digest** before use.

**Rules:**
- Never paste full transcripts into state files — summarize + keep source pointer
- Context digest format: `{key finding} [source: {path|url|tool}]`
- Max digest size per source: ~1K tokens
- Total compiled digest: governed by execution mode (see table above)
- Full sources remain accessible via pointers — fetch on demand during interviews

**Digest template:**
```markdown
## Context Digest

### From: {source name} [{source type}: {path/url}]
- {Key finding 1}
- {Key finding 2}
- {Key finding 3}

### From: {source name} [{source type}: {path/url}]
- ...
```

## Quality Gates

### Draft Quality Gate (before finalization)

Each core section is scored: **filled** | **partial** | **empty**

| Section | Minimum for standard | Minimum for deep |
|---------|---------------------|------------------|
| 1.1 Business Value | partial | filled |
| 1.2 Audience | partial | filled |
| 1.3 Success Criteria | partial (at least 1 metric) | filled (primary + guardrail) |
| 2.1 Solution Approach | partial | filled |
| 2.2 Milestones + Out of Scope | partial | filled |
| 2.3 Open Questions | filled (always — even if no gaps) | filled + owners assigned |
| 2.4 Core Flow Change | empty OK | partial |

**Gate rule:** If any section below minimum, warn user and suggest one more interview round before finalizing.

### Review Quality Gate (before "review complete")

- Every blocking concern has: section reference, severity, suggested owner
- Cross-cutting issues (flagged by 2+ reviewers) are elevated to top of synthesis
- "Must-fix before kickoff" checklist generated: feasibility blockers, missing metrics, dependency owners, rollout risks

## Evidence Tagging

Every major claim in the PRD should be tagged:

| Tag | Meaning |
|-----|---------|
| `[source: {ref}]` | Backed by data, quote, or research |
| `[inferred]` | Reasoned from available context but not directly stated |
| `[assumption]` | Best guess — needs validation |

During review, untagged claims are flagged as potential gaps.

## Capability Detection

Tools are configured per area in `{area}/_config.md` (§ Tools). At runtime, check which configured tools are actually online.

Also see: SYSTEM.md § Failure Escalation Policy (applies to all tool calls and sub-agents).

```
1. Load {area}/_config.md → parse tool role mappings
   If no _config.md exists → discover tools dynamically, no area-specific hints
2. For each configured role, probe the MCP tool
   online → available for context gathering
   offline → log "Unavailable: {role} ({tool})"
3. Report availability summary to user before gathering:
   "Tools available: {list}. Unavailable: {list}."
4. Never block the workflow on a missing tool
5. Model unavailable → fall back to next available (opus → sonnet → haiku)
```

**Failure logging in state files:**
```
## Fetch Results
- {role}: ✓ ({N} findings)
- {role}: ✗ {reason} — user provided paste | skipped | retried
- {role}: ⊘ unavailable (not probed)
```

**Critical rule:** A failed fetch is NOT the same as "no results found." Failed means the data might exist but we couldn't get it. Always tell the user so they can provide it manually.

## Confidence Scoring

Each PRD section gets a confidence score after mapping:

| Score | Meaning | Action |
|-------|---------|--------|
| **high** | Multiple sources agree, evidence-backed | No interview needed |
| **medium** | Some signal but gaps or assumptions | Prioritize for interview |
| **low** | Minimal signal, mostly inferred | Must interview or mark as open question |
| **none** | Zero signal | Leave empty, create open question with owner |

Confidence drives interview question prioritization and review focus areas.

## Question Limits

To prevent question explosion:

| Limit | Value |
|-------|-------|
| Max follow-up questions per answer | 2 |
| Max total open questions | 15 |
| Max questions per interview round | 5 |
| Question debt limit (unasked backlog) | 10 — if exceeded, prune lowest-priority |

Priority order for questions: Problem Statement > Solution Approach > Milestones > Roll-out > Other.

## State File Schema

Compact YAML-like structure for cross-model recovery:

```markdown
# PRD State: {Project Name}

project: {kebab-name}
area: {area}
mode: {lean|standard|deep}
phase: {setup|gathering|mapping|interview-N|finalizing|review}
created: {ISO date}
updated: {ISO date}

## Context Digest
{Compressed findings — see digest template above}

## Section Confidence
- 1.1_business_value: {high|medium|low|none}
- 1.2_audience: {medium}
- 1.3_success_criteria: {low}
- 2.1_solution: {medium}
- 2.2_milestones: {low}
- 2.3_open_questions: {filled}
- 2.4_core_flow: {none}

## Interview Log
1. Q: {question} → A: {answer summary} → Sections updated: {list}
2. Q: {question} → A: skipped

## Open Questions
1. {question} — priority: {high|medium|low} — owner: {person/role}
2. {question} — priority: {medium} — owner: {TBD}

## Review Results (if in review phase)
- tech_lead: {complete|pending|failed}
- head_of_product: {complete|pending|failed}
- design_lead: {complete|pending|failed}
- blocking_concerns: {N}
- addressed: {N}
```

## Reviewer Output Schema

Every reviewer sub-agent must end their response with a fenced YAML block in this exact shape. The synthesis step parses this for reliable aggregation.

```yaml
concerns:
  - section: "1.1 Business Value"       # PRD section reference
    severity: blocking                   # blocking | non-blocking
    concern: "One-sentence description"
    evidence: "What in the PRD (or missing from it) prompted this"
    suggested_owner: "PM"                # PM | Engineering | Design | TBD
    action: "Specific next step to resolve"
  - section: "2.1 Solution Approach"
    severity: non-blocking
    concern: "..."
    evidence: "..."
    suggested_owner: "Engineering"
    action: "..."
questions:
  - question: "Specific, answerable question text"
    priority: high                       # high | medium | low
    suggested_owner: "PM"                # PM | Engineering | Design | TBD
```

**Rules:**
- Every concern MUST have all 5 fields — no omissions
- `section` must match a real section heading from the PRD
- `severity` is strictly `blocking` or `non-blocking` — no other values
- Prose review comes first; YAML block is the last thing in the response

## Platform Notes

### Claude Code
- Sub-agents via Task tool with `model` parameter
- Model preference: strongest available reasoning model
- Fallback chain: opus → sonnet → haiku

### Cursor
- Can use any available model for reviewer diversity
- Recommended: different model per reviewer for maximum perspective diversity
- All prompts are self-contained — no dependency on conversation history
- Keep context window in mind: prefer reference-by-path over large pastes
