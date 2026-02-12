# Create Linear Ticket

Take a loose brain dump and turn it into a well-researched, well-formatted Linear ticket with context from the knowledge base, codebase, existing Linear issues, and vault documents.

**References:** `{area}/_config.md` § Linear Tickets

## Contract

**Pre-conditions:**
- Linear MCP available
- Area `_config.md` has `## Linear Tickets` section (team, project, status, priority, template)
- User provides a brain dump (free-form text describing what they want)

**Post-conditions:**
- Linear issue created with formatted description
- ACTION_LOG.md updated with issue URL

**CRITICAL:** No write to Linear without explicit user approval. The `create_issue` call requires confirmation.

**Errors:**
- Linear MCP unavailable → abort
- Area config missing `## Linear Tickets` → abort with instructions to add config
- Context source fails → surface per Failure Escalation Policy, continue with available sources
- Duplicate detected → present matches, user decides whether to proceed

## Triggers

| Command | Action |
|---------|--------|
| "create ticket" | Run with brain dump from message |
| "create linear ticket" | Run with brain dump from message |
| "file a ticket for X" | Run with X as brain dump |
| "ticket: X" | Run with X as brain dump |
| "new ticket" | Run — prompt for brain dump if not provided |
| "log a bug for X" | Run with X as brain dump, hint type=bug |

## Runtime Protocol

### 0. Init

```
parse: brain_dump (user's free-form input), type_hint (bug/feature/task if detectable)
resolve: area (default from vault context)
load: {area}/_config.md → § Linear Tickets (team, default_project, default_status, default_priority, template)
validate: Linear MCP is responsive (get_team as health check)
```

If brain dump is empty or missing, ask: "What do you want to file a ticket for?"

### 1. Understand

Parse the brain dump to extract:

```
intent: What is the user asking for? (bug fix, new feature, improvement, task)
subject: What part of the product does this touch?
keywords: 2-5 search terms for research phase
urgency_signals: words suggesting priority ("broken", "blocking", "nice to have")
```

Do NOT ask questions yet. Form a working hypothesis from the brain dump alone.

### 2. Research

Gather context from available tools. Each source is optional — skip gracefully if tool is offline or returns nothing.

**Source checklist** (per `{area}/_config.md` tool roles):

```
In parallel where possible:
  knowledge_base → search for subject keywords
  codebase → explore via explore-codebase in lean/question mode:
    "Where is {subject} implemented? What files handle {keywords}?"
    (foreground only — needs file permissions)
  issue_tracker → search Linear for context:
    list_issues(query="{keywords}", team=config.team, limit=10)
    list_projects(query="{subject}") → check project descriptions
  vault → Grep/Glob the area folder for related notes, PRDs, meeting notes

Optional (if subject warrants):
  chat → search Slack channels from config:
    slack_search_public(query="{keywords} in:{channel}")
    Prioritize #action-bugs / #action-questions for bug/feature context
  feedback_board → search for similar user requests:
    find_similar_posts(query="{subject}")
```

**After each fetch, verify result** per Failure Escalation Policy. Log what succeeded and what failed. Surface failures to user immediately.

**Output:** Research digest — compressed findings, not raw data. Keep file:line references from codebase, issue URLs from Linear, article titles from KB.

### 3. Duplicate Check

Before drafting, search Linear for existing/similar issues:

```
queries:
  list_issues(query="{primary keywords}", team=config.team, limit=10)
  list_issues(query="{alternate phrasing}", team=config.team, limit=10)

Score matches:
  exact: title closely matches intent + same project → likely duplicate
  related: similar topic but different scope → related, not duplicate
  distinct: different concern → skip
```

**If exact matches found:**

```
⚠ Found existing issues that may cover this:
- [{identifier}] {title} ({state}) — {project}
  {1-line description excerpt}

1. Same thing — don't create a new ticket
2. Related but different — proceed (I'll link to these)
3. Let me inspect one of these first
```

Wait for user decision:
- (1) → abort, return existing issue URL
- (2) → proceed, store related issues for `relatedTo` field
- (3) → show full issue via `get_issue`, then re-ask

**If no matches → proceed silently.**

### 4. Draft

Compose the ticket using the template from `_config.md § Linear Tickets`.

**Map research findings to template sections:**

```
title: Concise, action-oriented. Format: "{Verb} {feature} {context}"
description: Render template with research findings
metadata:
  team: config.team
  project: config.default_project (override if brain dump references specific project)
  state: config.default_status
  priority: infer from urgency_signals, default to config.default_priority
  labels: infer from subject classification (optional)
  relatedTo: issues from step 3 if user chose "related but different"
```

**Present the draft in this exact format:**

---

**{title}**

Team: {team} | Project: {project} | Status: {status} | Priority: {priority}
{Labels if any} {Related issues if any}

{rendered template — Current Behavior, Desired Behavior, LLM Context}

---

Assumptions:
- {assumption about scope, project placement, priority, etc.}
- {assumption about current behavior based on research}
- {assumption about implementation approach}

Questions (optional — answer any, all, or none):
1. {most clarifying question}
2. {second question}
3. {third question}

---

### 5. Refine

User can:

- **approve** / **lgtm** / **ship it** → proceed to Commit
- **edit: {instructions}** → apply edits, re-present draft
- **answer questions** → incorporate answers, re-present draft
- **change project/priority/team** → update metadata, re-present
- **cancel** / **abort** → stop, no ticket created

On re-draft, show only what changed (delta), not the full card again, unless user asks.

### 6. Commit

Execute after explicit user approval only.

```
create_issue(
  title: {title},
  description: {rendered description in markdown},
  team: config.team,
  project: {project},
  state: config.default_status,
  priority: {priority_number},
  labels: {labels if any},
  relatedTo: {related issue identifiers if any}
)

→ capture returned issue identifier and URL
```

Present:
```
Created: [{identifier}] {title}
{URL}
```

### 7. Log

```
Append to ACTION_LOG.md:
    ### {date} Create Linear Ticket
    - Issue: [{identifier}] {title}
    - Team: {team} | Project: {project} | Priority: {priority}
    - Sources used: {list of sources that provided context}
    - URL: {issue URL}
```

## API Notes

This procedure uses the **Linear MCP** tools:

- `list_issues(query="...", team="...")` — search for existing/similar issues
- `list_projects(query="...")` — find project context and design specs
- `get_issue(id="...")` — fetch full issue details for duplicate review
- `create_issue(title, description, team, project, state, priority, ...)` — create the ticket
- `get_team(query="...")` — resolve team name, health check
- `list_issue_statuses(team="...")` — validate status names if needed

## Examples

**"create ticket: analytics dashboard is showing wrong numbers for email open rates"**
→ Parse as bug. Research: KB (analytics docs) + codebase (analytics pack) + Linear (existing analytics bugs) + Slack (#action-bugs). Check for duplicates. Draft with Current Behavior from KB, Desired Behavior from brain dump, LLM Context with file paths.

**"ticket: we need a way to bulk edit contact tags"**
→ Parse as feature. Research: KB (contacts docs) + codebase (contacts/tags) + Featurebase (similar requests). Draft with implementation hints.

**"log a bug for DMARC validation showing false positives in domain health center"**
→ Parse as bug (explicit hint). Research: KB (domain health docs) + codebase (domain health pack) + Linear (related issues) + Slack (#action-bugs for user reports). Draft ticket.
