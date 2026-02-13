# Moderate Featurebase

Moderate customer feature requests on Featurebase: rewrite in standard format, detect duplicates, surface merge candidates, and apply tags.

**References:** `{area}/_config.md` § Featurebase Moderation

## Contract

**Pre-conditions:**
- Featurebase MCP available (local fork at `~/code/featurebase-mcp`)
- Area `_config.md` has `## Featurebase Moderation` section (surfaces, keywords, template, statuses)

**Post-conditions (per post):**
- Content rewritten in standard format
- `inReview` cleared (set to false)
- Feature area tag applied
- Duplicates surfaced with merge links (if any)

**CRITICAL:** No write actions to Featurebase without explicit user approval per item. All writes (`update_post`, `create_comment`, `create_post` for splits) require confirmation.

**Errors:**
- Featurebase MCP unavailable → abort
- Post not found (single mode) → abort with error
- Context source fails → surface per Failure Escalation Policy, continue
- Batch interrupted → state persisted in `_state/fb-moderation.md`

## Triggers

| Command | Action |
|---------|--------|
| "moderate featurebase" | Run in batch mode |
| "triage featurebase" | Run in batch mode |
| "moderate this post" | Run in single mode (resolve from context) |
| "moderate post {id}" | Run in single mode with post ID |
| Featurebase post URL pasted | Run in single mode (extract slug from URL) |

## Runtime Protocol

### 0. Init

```
parse: mode (single/batch), post_id or slug if single
resolve: area (default: amplemarket/)
load: {area}/_config.md → tool roles + § Featurebase Moderation
check: _state/fb-moderation.md → resume if exists
```

**URL parsing:** If user pastes a Featurebase URL like `https://feedback.amplemarket.com/p/{slug}`, extract the slug. Use `list_posts(q="{slug}")` to find the post. Fall back to paginating `list_posts` and matching by `slug` field if search doesn't return it.

### 1. Discover Posts

**Single mode:**
```
if post_id → list_posts with client-side filter by id, or use the post URL
if slug → list_posts(q="{slug}"), match by slug field
if "this post" → ask user for URL or ID
→ result: [single post]
```

**Batch mode:**
```
1. Load _state/fb-not-mine.md → exclusion list (post IDs from previous sessions)
2. Fetch inReview posts in small pages:
   list_posts(inReview=true, limit=10)
   - For each page, extract ONLY: id, title, first 200 chars of content (strip HTML)
   - Store extracted data in a lightweight list, discard full post objects
   - If nextCursor present, fetch next page. Stop after 100 posts max.
   - IMPORTANT: Do NOT hold full post objects in context — they are ~1.7KB each
     and will exceed token limits at scale. Extract and discard.
3. Filter: id NOT IN exclusion list
→ result: lightweight queue [{id, title, snippet}] for classification
```

### 2. Classify & Filter

Classify from the lightweight queue (title + snippet only — no full content needed):

```
for each {id, title, snippet, tags} in queue:
    if post has Featurebase tags → use those as surface (tags are manually assigned, trust them)
    else → classify title + snippet against config Classification Keywords
    if no clear match → "Other"

mine = [p for p in queue if surface IN config "My Surfaces"]
others = queue - mine

Present summary:
    Found {N} posts pending moderation.
    - {surface}: {count}
    - {surface}: {count}
    - Other (not my team): {count} — skipping

    Process these {M} posts?

On confirmation → initialize _state/fb-moderation.md with header only:

    ## Moderation Batch — {date}
    Queue: {total} posts | Prepared: 0 | Reviewed: 0
    Phase: preparing
```

### 3. Prepare Posts (autonomous — batch mode)

In batch mode, prepare all posts autonomously before presenting any for review. This lets the user work through prepared cards quickly without waiting for tool calls.

**Single mode** skips this step — go straight to Step 4 (Process Single Post).

**CRITICAL:** The state file is the work product. Every post's full research output — context, rewrite, duplicates, HTML — MUST be written to `_state/fb-moderation.md` as each post is prepared. This is what makes recovery possible without redoing work, and what gets archived as a durable reference after the batch completes.

Prepare in batches of **5 posts**, then review those 5 before preparing the next batch. This keeps context manageable and avoids long waits.

```
while mine has unprepared posts:
    batch = next 5 unprepared posts from mine
    for each post in batch: run 3a–3e (fetch, triage, rewrite, dedup, write to state)
    → proceed to Step 4 (Review) for this batch
    → after reviewing all 5, loop back here for the next batch
```

For each post in the current batch, run 3a–3d, then **write the prepared card to the state file** (3e):

#### 3a. Fetch & Gather Context

```
get_post(id=post.id) → full content

In parallel:
  knowledge_base → search KB for keywords from post title
  issue_tracker → search Linear for related issues
  (skip codebase — offer per-post during review if user asks)

If a source fails → log ✗ in prepared card, continue with what's available
```

#### 3b. Triage

- If post describes multiple distinct requests → flag as `needs-split` (user decides during review)
- If post is a bug report → flag as `bug-report`
- If post is too vague → flag as `needs-pm-input`
- Classify surface using config keywords + gathered context

#### 3c. Rewrite

Generate the rewritten post using the template from `_config.md`:

**Title:** Concise, discoverable, action-oriented. Format: `{Verb} {feature/capability} {context}`. Examples:
- "Filter Analytics by Active Sequences"
- "Auto-assign Leads on LinkedIn Connection Accept"
- "Support Multi-threading in Sequence Emails"

**Content:** Use the rewrite template (output as HTML for Featurebase, but think in plain text):

- **Current Behavior** — what exists today, sourced from KB. Be specific about actual product behavior.
- **Desired Behavior** — what the user wants. Extracted from their request, clarified if ambiguous.
- **User Voice** — verbatim quote from original post. Preserve the customer's words.

**HTML format:** Write compact, single-line HTML — no newlines between tags (Featurebase renders whitespace). Use bare `<strong>` for headings, not `<p>`. Example:

```html
<strong>Current Behavior</strong><ul><li>First point</li><li>Second point</li></ul>
<strong>Desired Behavior</strong><ul><li>First point</li><li>Second point</li></ul>
<strong>User Voice</strong><blockquote><p>"verbatim quote"</p></blockquote>
```

**Edge cases:**
- Post too vague → flag as `needs-pm-input`, preserve original
- Post is a bug report → note this, suggest different handling
- Post is well-written already → propose minimal edits, don't over-rewrite

#### 3d. Detect Duplicates

```
1. Extract 1-2 keyword queries from rewritten post title
2. For each query: list_posts(q="...", limit=10)
3. Score matches: exact (merge) / related (note) / distinct (skip)
4. Canonical = most upvotes, or oldest if tied
```

#### 3e. Write Prepared Card to State

**After preparing each post**, append the full prepared card to `_state/fb-moderation.md` and update the header's `Prepared` count. This is not optional — the state file is the output of preparation.

```markdown
---
### Post {N}/{total}: {original title}
**ID:** {id}
**Author:** {author name} | **Upvotes:** {N} | **Date:** {date} | **Surface:** {surface}
**URL:** {postUrl}
**Status:** pending

#### Original
> {exact verbatim text from the Featurebase post, converted to plain text. Do NOT summarize or paraphrase — copy the customer's words as-is.}

#### Research

**Featurebase — related posts:**
- [{post title}]({postUrl}) — {1-line summary of what it requests and how it relates}. {N} upvotes, status: {status}
- ...
- (or: None found)

**Knowledge Base:**
- [{article title}]({url}) — {1-line summary of relevant info found}
- ...
- (or: None found)

**Linear:**
- [{issue/doc identifier}]({url}) — {1-line summary: what it is, status, how it relates}
- ...
- (or: None found)

**Codebase:**
- `{file_path}` — {1-line summary of what's there and why it's relevant}
- ...
- (or: Not searched / None found)

#### Decision
**New Title:** {new title}
**Tags:** {suggested tags}
**Flags:** {none / needs-split / bug-report / needs-pm-input}
**Suggested action:** {approve / merge / reject / needs-pm-input}
**Merge candidate:** {None / [{title}]({url}) — {reason}}

#### Rewrite (HTML)
{ready-to-submit HTML for Featurebase update_post}
```

Progress update after each post: `Prepared {N}/{total}...`

When the current batch (5 posts) is prepared, update header to `Phase: reviewing` and announce:

```
✅ Prepared {N} posts (batch {B}). Ready to review them?
```

After reviewing the batch, if more posts remain, loop back to Step 3 for the next batch of 5.

### 4. Review Posts

#### Batch mode (from prepared state)

Read each pending post from `_state/fb-moderation.md` and present the review card.

**Review card format** (rendered from state — no tool calls needed):

**CRITICAL:** Always include the post URL and the full original content (plain-text, not summarized). The user needs to see exactly what the customer wrote.

---

{author name} | {N} upvotes | {date} | Surface: {surface}
[{original title}]({postUrl})

**Original content:**
{full plain-text content of the post — not summarized, convert HTML to plain text}

---

### {new title}

{render the rewrite HTML as readable plain text for the review card}

**Research:** {summarize key findings from state — related posts, KB articles, Linear issues. Include links. Omit sections where nothing was found.}

Merge candidate: {None / [{title}]({url}) ({N} upvotes) — {reason}}

Suggested action: {approve / merge / reject / needs-pm-input}

approve / edit / skip / reject / not-mine?

---

Keep it short. Omit context/duplicates lines entirely if nothing was found — don't show empty fields.

#### Single mode (no state)

For a single post, run 3a–3d inline (fetch, context, rewrite, dedup), then present the review card directly. No state file needed.

#### User actions

- **approve** — apply rewrite + tags, clear inReview
- **edit** — user provides corrections, re-present
- **merge** — clerk provides canonical link for manual merge in Featurebase UI
- **skip** — leave as-is (stays in review queue)
- **reject** — set status per config Status Mapping, clear inReview
- **not-mine** — wrong team; add to `_state/fb-not-mine.md`, skip

### 5. Commit

Execute the chosen action immediately after user approves. **Each write requires prior approval from Step 4.**

```
match action:
    approve →
        update_post(id, title=new_title, content=html_content, inReview=false, tags=[surface_tag, ...])

    merge →
        Present: "Merge [{dup_title}](dup_link) into [{canonical_title}](canonical_link) in Featurebase UI"
        Wait for user: "Done" / "Skip"
        (No API write — user does merge manually)

    reject →
        update_post(id, statusId={from config Status Mapping for "Rejected"}, inReview=false)

    not-mine →
        Append post ID + title to _state/fb-not-mine.md

    skip →
        (no action)

Update post status in _state/fb-moderation.md → approved/rejected/skipped/merged/not-mine
```

Then present next pending post from state.

### 6. Log & Archive

```
Append to ACTION_LOG.md:
    ## Featurebase Moderation — {date}
    - Processed: {N} posts
    - Approved: {N} (list titles)
    - Merged: {N}
    - Rejected: {N}
    - Skipped: {N}
    - Not mine: {N}

If batch complete → archive state file:
    mv _state/fb-moderation.md → _state/fb-moderation-{YYYY-MM-DD}.md
    Update header: Phase: complete
If interrupted → state persists as _state/fb-moderation.md for recovery
```

The archived state file preserves the full work product for every processed post: context links (Linear issues, KB articles), proposed rewrites, duplicate analysis, flags, and final actions taken. This serves as a durable reference for future moderation sessions and product understanding.

## Recovery

Active state lives in `_state/fb-moderation.md` (no date suffix). Re-triggering detects this file and checks for:

1. **Unpresented prepared posts** (status: pending) → resume at Step 4 (Review)
2. **Preparation incomplete** (fewer posts prepared than in queue) → resume at Step 3 from next unprepared post
3. **All reviewed** → proceed to Step 6 (Log & Archive)

Dated archive files (`_state/fb-moderation-{date}.md`) are ignored by recovery — only the undated file is treated as active.

State file header tracks overall progress:

```markdown
## Moderation Batch — {date}
Queue: {total} posts | Prepared: {N} | Reviewed: {N}
Phase: preparing / reviewing / complete
```

## API Notes

This procedure uses the **Featurebase v2 API** via a local fork at `~/code/featurebase-mcp`.

Key capabilities the procedure depends on:
- `list_posts(inReview=true)` — server-side filter for moderation queue
- `list_posts(q="...")` — server-side search for duplicate detection
- `update_post(id, ...)` — v2 uses `PATCH /v2/posts/{id}` (id in URL path, not body)
- Response shape: `{ object: "list", data: [...], nextCursor: "..." }`
- Auth: `Authorization: Bearer <key>` + `Featurebase-Version: 2026-01-01.nova`

## Examples

**"moderate this post" + paste URL**
→ Extract slug, search for post, gather context, rewrite, check duplicates, present for approval, commit. (Single mode — no state file.)

**"moderate featurebase"**
→ Fetch inReview posts, classify surfaces, filter to My Surfaces. Prepare all posts autonomously (context + rewrite + dedup → state file). Then present prepared cards one by one for rapid review.

**"triage featurebase" after interruption**
→ Detect `_state/fb-moderation.md`. If preparation incomplete, resume preparing. If posts are prepared but unreviewed, jump to review phase. Report progress ("prepared 10, reviewed 5 — resuming review").
