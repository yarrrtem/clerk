# PRD Interview Heuristics

Guidelines for structured interviewing during PRD drafting. Referenced by `draft-prd.md`.

## Core Principles

1. **One question at a time** — depth over breadth, follow valuable threads
2. **Build on answers** — each question references what was said before
3. **Suggest hypotheses** — "I think X might be Y — does that resonate?" beats "What is Y?"
4. **Reference evidence** — "You mentioned X in the meeting..." not "Tell me about..."
5. **Be specific** — "Is the primary user SDR managers or individual SDRs?" not "Who is the audience?"

## Question Generation by Round

### Round 1 — Problem Framing

Focus: Validate the core problem, clarify audience, test assumptions, surface constraints.

| Pattern | Example |
|---------|---------|
| Validate core problem | "Is the primary pain point X or Y?" |
| Clarify audience | "When you say enterprise customers, do you mean 500+ employees or Fortune 500?" |
| Test gathered assumptions | "The meeting transcript suggests Z — is that still the direction?" |
| Surface constraints | "Are there compliance, timeline, or resource constraints I should know about?" |
| Quantify impact | "Do you have data on how often this problem occurs? Even a rough estimate helps." |

### Round 2 — Solution Shaping

Focus: Challenge the approach, probe milestones, test metrics, surface competition, identify risks.

| Pattern | Example |
|---------|---------|
| Challenge approach | "Have you considered alternative X? What made you lean toward Y?" |
| Probe boundaries | "Where's the line between M1 and M2? What would you cut from M1 if forced?" |
| Test success criteria | "Would you consider it successful if only metric X moved but Y stayed flat?" |
| Competitive context | "How do Outreach and Salesloft handle this? Are we matching or differentiating?" |
| Identify risks | "What's the biggest thing that could go wrong? What keeps you up at night about this?" |

### Round 3 — Sharpening

Focus: Scope discipline, operational readiness, stakeholder gaps, edge cases, dependencies.

| Pattern | Example |
|---------|---------|
| Scope discipline | "Is X truly needed for v1, or could it be a fast follow?" |
| Operational readiness | "How will you roll this out? Big bang or phased? Who are the early access candidates?" |
| Stakeholder gaps | "Who else needs to weigh in? Legal? Security? Sales enablement?" |
| Edge cases | "What happens when a user does X in situation Y?" |
| Dependencies | "What needs to be true for this to ship? Any team outside yours blocking?" |

## Question Quality Checklist

Before asking a question, verify:

- [ ] **Specific:** Can be answered in 1-3 sentences (not an essay)
- [ ] **Grounded:** References available context or previous answers
- [ ] **Actionable:** Answer will change something in the PRD
- [ ] **Non-obvious:** Not something you could infer from existing context
- [ ] **Hypothesis-bearing:** Offers a suggestion to confirm/deny when possible

## Bad vs. Good Questions

| Bad | Why | Good |
|-----|-----|------|
| "What's the business value?" | Too broad, parrots the template | "You mentioned this blocks enterprise deals — is the primary driver deal size or reducing churn?" |
| "Who is the audience?" | Generic | "The Featurebase data shows SDR managers and individual BDRs both requesting this — are they the same audience or separate personas?" |
| "What are the milestones?" | Template-filling, not thinking | "The solution has 3 natural phases: permissions, object sharing, and team hierarchy. Does that match your priority order?" |
| "Any success criteria?" | Lazy | "If we ship M1, what's the one metric that tells you it was worth it? New enterprise deal closures?" |

## Follow-up Generation

When an answer opens a new thread:

1. **Contradiction detected:** "Earlier you said X, but this suggests Y — which takes priority?"
2. **Scope signal:** "That sounds like it could expand scope — should we park that as a follow-up?"
3. **Missing stakeholder:** "That decision affects team Z — have they weighed in?"
4. **Risk surface:** "If that assumption is wrong, what's the fallback?"

**Limits:** Max 2 follow-ups per answer. Cap total open questions at 15 (see prd-config.md).

## Handling "I don't know" Answers

When the user can't answer:

1. **Reframe:** "Let me ask it differently — if you had to bet, would you say..."
2. **Offer options:** "I see three possibilities: A, B, or C. Does any feel closest?"
3. **Defer gracefully:** "That's a great open question — I'll add it with a suggested owner. Who should answer it?"
4. **Don't push:** After one reframe, accept "I don't know" and move on. Tag as `[assumption]` with a note.

## Evidence Elicitation

When answers lack evidence:

| Prompt | Purpose |
|--------|---------|
| "Is that from customer feedback, or your intuition?" | Surface evidence type |
| "Do you have a quote or data point I can reference?" | Get source material |
| "Which customers have told you this directly?" | Ground in specifics |
| "Is there a Slack thread or Featurebase post about this?" | Point to existing evidence |

Tag accordingly: `[source: customer X]`, `[source: Featurebase]`, `[inferred]`, `[assumption]`.
