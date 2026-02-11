# PRD Evidence Guide

How to tag and track evidence in PRD drafts. Referenced by `draft-prd.md`.

## Evidence Tags

Every major claim in a PRD should be tagged:

| Tag | Meaning | Example |
|-----|---------|---------|
| `[source: {ref}]` | Backed by data, quote, or research | "Enterprise buyers cite limited role granularity [source: Key Accounts Survey]" |
| `[inferred]` | Reasoned from context but not directly stated | "This suggests SDR managers are the primary audience [inferred]" |
| `[assumption]` | Best guess — needs validation | "We assume 80% of usage will be via the web app [assumption]" |

## When to Use Each Tag

**Use `[source]` when:**
- Referencing customer quotes or feedback
- Citing data from analytics, surveys, or research
- Quoting competitor analysis
- Referencing feedback board posts, chat threads, or meeting transcripts
- Pointing to existing documentation

**Use `[inferred]` when:**
- Drawing a conclusion from multiple data points
- Extrapolating from related evidence
- Connecting dots between different sources
- Making a logical deduction that isn't explicitly stated

**Use `[assumption]` when:**
- No evidence exists — it's a hypothesis
- The claim is based on intuition or experience
- Multiple alternatives are viable and you're picking one
- The statement needs validation before committing

## Source Reference Format

Keep source references compact but traceable:

```markdown
[source: feedback_board — "Feature Request Title" (47 upvotes)]
[source: meetings — Q1 Planning meeting 2026-02-05]
[source: issue_tracker — PROJ-1921 design specs]
[source: chat — #product-discussion 2026-01-15]
[source: Customer — Acme Corp (Jane), via call recording]
[source: Competitor analysis — Competitor X feature comparison]
[source: knowledge_base — "How the product handles X"]
```

## During Review

Reviewers check for:
1. **Untagged claims** — major statements with no evidence marker → flag as gap
2. **Assumption density** — too many `[assumption]` tags in a section → needs more research
3. **Source quality** — are sources credible and recent?
4. **Missing evidence** — claims that should have data but don't

## Cleaning Up Tags

During finalization:
- Confirmed assumptions → convert to `[source]` with the confirming evidence
- Disproven assumptions → remove claim or rewrite
- Inferences validated by user → upgrade to `[source: PM confirmation]`
- Remaining assumptions → keep tagged, add to open questions with owner
