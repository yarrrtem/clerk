# Draft Launch Message

Compose a product launch announcement for `#all-product-launches` and create it as a Slack draft.

**References:** @amplemarket/templates_examples/launch-message-template.md · @amplemarket/_slack-style.md

## Contract

**Pre-conditions:**
- Slack MCP tools available (`slack_send_message_draft`, `slack_search_channels`)
- User provides brain dump: feature name, what shipped, and ideally team + rollout status

**Post-conditions:**
- Draft created in `#all-product-launches` (C0366HHNFPY), visible in user's Drafts & Sent
- User reviewed and approved the message before draft creation
- ACTION_LOG.md updated

**Errors:**
- Slack MCP unavailable → abort with "Slack tools not available"
- Template not found → warn, use inline fallback structure
- Draft already exists in channel → show composed message for manual paste
- Missing required fields (team, rollout) → ask user before composing

## Triggers

| Input | Action |
|-------|--------|
| "draft launch message" | Compose launch announcement |
| "write a launch announcement" | Compose launch announcement |
| "announce X in product launches" | Compose for feature X |
| "product launch for X" | Compose for feature X |

## Procedure

### 1. Parse brain dump

Extract from user input:

| Field | Required | Notes |
|-------|----------|-------|
| `feature_name` | ✓ | Title of the feature |
| `what_changed` | ✓ | What shipped — capabilities, behavior changes |
| `who_worked_on_it` | ✓ | Team members for shoutout (names or @mentions) |
| `rollout_status` | ✓ | Who has it now, what's next |
| `customer_context` | | Which customers drove this, pain points |
| `loom_link` | | Demo video URL |
| `initiative` | | Broader project this connects to (for closer) |
| `prd_or_linear_ref` | | PRD path or Linear project name (for enrichment) |

Brain dumps are messy — extract what's there, flag what's missing.

### 2. Fill gaps

**Required fields missing → ask user directly:**

Batch questions (max 5). Examples:
- "Who should get the shoutout? Names + what they did."
- "What's the rollout status? (Live for X, rolling out to Y, ETA for Z)"
- "Do you have a Loom for this?"
- "Which customers drove this request?"

**Optional enrichment — only if user references a source:**

If user mentions a PRD:
```
Read: {area}/projects/{project}/PRD-{project}.md
→ Extract problem framing for "What we heard"
```

If user mentions a Linear project:
```
list_issues(project="{project_name}", team="SaaS")
→ Extract assignees for shoutout candidates
get_project(query="{project_name}")
→ Extract milestone/status for rollout context
```

If user mentions a Slack thread:
```
slack_search_public_and_private(query="{topic}")
→ Extract prior context, customer quotes
```

Do NOT auto-search all tools. Only fetch what the user points to.

### 3. Load template + style

```
Read: amplemarket/templates_examples/launch-message-template.md
→ Load template structure, writing rules, exemplars

Read: amplemarket/_slack-style.md
→ Load voice rules + anti-patterns (cross-functional register)
```

```
✓ Verify: template loaded
✗ On fail: Warn "Template not found — using inline structure." Use this fallback:
  {emoji title}
  What we heard: {problem}
  What we did: {bullets}
  Rollout: {status}
  {shoutout}
  {closer}
```

### 4. Compose message

Apply template structure + voice rules + anti-patterns.

**Calibration:**
- **"What we heard"**: 2-3 sentences. Customer-first framing. Name customers if they drove it.
- **"What we did"**: 3-5 bullets max. Capabilities, not implementation details.
- **Shoutout**: Always. "{Name} for {specific role}" format. Never generic "thanks team."
- **Closer**: 1 sentence. Connect to initiative/milestone. Not "stay tuned."
- **Overall length**: Lean short. The exemplars are the max length — aim shorter.

**Emoji title selection:**
Pick emoji pairs that match the feature theme:
- 🔐 permissions/security
- 📊 analytics/data
- 🧠 AI/intelligence
- 📞 calling/dialer
- 🗂️ organization/filtering
- ⚡ speed/performance
- 🔄 sync/integration

### 5. Present for review

```
**Draft for:** #all-product-launches

---
{composed message}
---

Create as Slack draft? (yes / edit / cancel)
```

- **yes** → proceed to step 6
- **edit** → user provides changes (shorter, different framing, add/remove shoutouts), revise, re-present
- **cancel** → abort

### 6. Create draft

```
slack_send_message_draft(
  channel_id = "C0366HHNFPY",
  message = {final_message}
)
```

```
✓ Verify: draft created (channel_link returned)
✗ On fail (draft already exists): "A draft already exists in #all-product-launches. Here's the message — you can paste it manually or clear the existing draft first."
✗ On fail (other): "Draft creation failed: {error}. Message copied above for manual paste."
```

### 7. Log & confirm

Append to ACTION_LOG.md:
```
### {date} Launch Announcement Draft
- Feature: {feature_name}
- Channel: #all-product-launches
- Team: {who_worked_on_it}
- Status: Draft created
```

Return to user:
```
Draft created in #all-product-launches. Review and send from Slack's Drafts.
```

## Recovery

No state file needed — brain dump + composed message are in conversation context.
If interrupted before step 6, user can say "resume" and the message is still available.

## Examples

**Input:** "launch message for Contact Edits — we shipped the ability to edit contacts for customers on the new CRM sync. Abdelrahman drove it, Andre and Nelson helped. Live for SFDC customers, Hubspot in March. Loom: [url]. This is part of the CRM Sync initiative."

- Parses: all fields present
- Loads template + style
- Composes: emoji title, user story about editing frustration, 3 bullets, rollout with ✅/🚀, shoutout to Abdelrahman + team, closer about CRM Sync initiative
- Creates draft in #all-product-launches

**Input:** "product launch for the new Custom Roles feature"

- Parses: feature_name only
- Asks: "Who should get the shoutout?", "What's the rollout status?", "Do you have a Loom?", "Any customer that drove this?"
- After answers → composes + reviews + drafts

**Input:** "announce Parallel Dialer in product launches — check the PRD at amplemarket/projects/parallel-dialer/"

- Parses: feature_name + PRD reference
- Reads PRD for problem framing + solution details
- Asks: team members, rollout status, Loom
- Composes using PRD context + user answers
