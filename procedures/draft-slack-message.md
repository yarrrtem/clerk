# Draft Slack Message

Compose a Slack message in the user's voice and create it as a draft in Slack for review.

## Contract

**Pre-conditions:**
- Slack MCP tools available (`slack_send_message_draft`, `slack_search_channels`, `slack_search_users`)
- Message intent provided: what to say + who/where to say it
- Area context available for style guide lookup

**Post-conditions:**
- Draft created in target Slack channel (visible in user's Drafts & Sent)
- User reviewed the message before draft was created
- ACTION_LOG.md updated

**Errors:**
- Slack MCP unavailable → abort with "Slack tools not available"
- Channel/user not found → ask user for valid target
- Style guide not found → warn, compose without style guide
- Draft already exists in channel → warn user, offer to compose anyway (they'll need to clear existing draft)

## Triggers

| Input | Action |
|-------|--------|
| "draft slack message" | Compose new message |
| "write a slack message to X" | Compose for recipient X |
| "message X on slack" | Compose for recipient X |
| "draft message for #channel" | Compose for specific channel |
| "reply to X about Y" | Compose thread reply (needs thread_ts) |

## Procedure

### 1. Parse intent

Extract from user input:
- `target`: channel name, user name, or "the thread about X"
- `topic`: what the message is about
- `key_points`: specific content to include (if provided)
- `tone_override`: explicit tone request ("keep it casual", "make it formal") — optional
- `thread_ts`: if replying to a specific thread — optional

If any are ambiguous, ask the user before proceeding.

### 2. Resolve channel

**If target is a channel name:**
```
slack_search_channels(query="{channel_name}")
→ extract channel_id
```

**If target is a person's name:**
```
slack_search_users(query="{person_name}")
→ extract user_id → use as channel_id for DM
```

**If target is a thread:**
```
slack_search_public_and_private(query="{topic} from:<@{user_id}>")
→ find the thread → extract channel_id + thread_ts
```

```
✓ Verify: channel_id resolved
✗ On fail: "I couldn't find '{target}'. Can you give me the exact channel name or person?"
```

### 3. Detect tone register

Infer from channel type and context:

| Signal | Register |
|--------|----------|
| DM or private team channel | **casual** |
| Public internal channel (#mission-*, #action-*, #team-*) | **cross-functional** |
| Shared/external channel (#amplemarket-*, #oreilly-*, contains external users) | **customer-facing** |
| User says "keep it casual" or "informal" | **casual** (override) |
| User says "make it formal" or "professional" | **customer-facing** (override) |

### 4. Load style guide

```
Read: {area}/_slack-style.md
→ Focus on the matched register section
→ Load voice rules and anti-patterns
```

Currently: `amplemarket/_slack-style.md`

If style guide not found, warn:
```
⚠ No style guide found at {area}/_slack-style.md — composing without voice matching.
```

### 5. Compose draft

Write the message applying:
1. **Voice rules** from the style guide (capitalization, punctuation, contractions)
2. **Register exemplars** as tone reference (match length, structure, warmth level)
3. **Anti-patterns** as negative constraints (avoid AI-sounding phrases)
4. **User's key points** as content source

Do NOT over-explain, pad, or hedge. Match the register's natural length:
- Casual: 1-3 sentences, fragments ok
- Cross-functional: 1-3 paragraphs, structured
- Customer-facing: 2-4 paragraphs, warm and forward-looking

### 6. Present for review

Show the user:

```
**Draft for:** #{channel} (register: {casual|cross-functional|customer-facing})

---
{composed message}
---

Send as draft? (yes / edit / cancel)
```

- **yes** → proceed to step 7
- **edit** → user provides changes, revise, re-present
- **cancel** → abort, no draft created

### 7. Create draft in Slack

```
slack_send_message_draft(
  channel_id = {channel_id},
  message = {final_message},
  thread_ts = {thread_ts if replying}
)
```

```
✓ Verify: draft created (channel_link returned)
✗ On fail: "Draft creation failed: {error}. You can copy the message above and paste it manually."
```

### 8. Log & confirm

Append to ACTION_LOG.md:
```
### {date} Slack Draft
- Channel: #{channel_name}
- Register: {register}
- Topic: {topic}
- Status: Draft created
```

Return to user:
```
Draft created in #{channel_name}. You can review and send it from Slack's Drafts.
```

## Recovery

If interrupted before step 7, the composed message is in the conversation context — user can ask to resume.
No state file needed (drafts are lightweight, single-turn).

## Examples

**Input:** "draft a message to Luis about the CRM sync rollout timeline"
- Resolves: Luis → DM channel_id
- Register: casual (DM with teammate)
- Output: Short, lowercase-i message with timeline highlights

**Input:** "write a message in #mission-winning-povs explaining the contact edit ETA for CodeRabbit"
- Resolves: #mission-winning-povs → channel_id
- Register: cross-functional (public mission channel)
- Output: Structured paragraphs, empathetic closing, proper caps

**Input:** "message the O'Reilly channel about the sync fix being deployed"
- Resolves: #oreilly-* → channel_id
- Register: customer-facing (shared external channel)
- Output: Warm, professional, future-vision framing
