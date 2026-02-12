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
for each {id, title, snippet} in queue:
    classify title + snippet against config Classification Keywords
    if no clear match → "Other"

mine = [p for p in queue if surface IN config "My Surfaces"]
others = queue - mine

Present summary:
    Found {N} posts pending moderation.
    - {surface}: {count}
    - {surface}: {count}
    - Other (not my team): {count} — skipping

    Process these {M} posts?

On confirmation → write queue to _state/fb-moderation.md
```

### 3. Process Each Post (one at a time)

For each post in `mine`, run 3a–3e, then immediately present for review.

**First:** Fetch the full post via `get_post(id=post.id)` — this gets the complete content for rewriting. Only fetch one post at a time.

#### 3a. Gather Context

Fetch from available tools (per `_config.md` tool roles). Run in parallel where possible. **Foreground only.**

```
knowledge_base → search KB for keywords from post title
issue_tracker → search Linear for related issues
(skip codebase in batch — offer per-post if user asks)

verify each result (Failure Escalation Policy):
    if error → log ✗, surface to user, offer paste/skip/retry
    if success → log ✓, compress into digest
```

#### 3b. Triage & Split

**Split detection:** If the post describes multiple distinct, unrelated requests:
1. Identify each distinct request
2. Present to user: "This post contains {N} separate requests. Split into individual posts?"
3. If approved: create new posts for each (with user confirmation per write), update original
4. Track splits in `_state/fb-moderation.md` for idempotency
5. Process each resulting post separately

**Surface classification:**
- Classify using config keywords + gathered context
- If unclear → ask user: "Which surface does this belong to? {options}"

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

**Edge cases:**
- Post too vague → flag as `needs-pm-input`, present original + ask user
- Post is a bug report → note this, suggest different handling
- Post is well-written already → propose minimal edits, don't over-rewrite

#### 3d. Detect Duplicates

Use v2 API search + LLM judgment:

```
1. Extract 1-2 keyword queries from rewritten post title
   Example: "Filter Analytics by Active Sequences"
   → queries: ["analytics filter sequence", "sequence analytics"]

2. For each query: list_posts(q="...", limit=10)
   - v2 API does server-side search on title + content

3. Score each result against rewritten post:
   - exact: Same core request → recommend merge
   - related: Overlapping scope → note as related
   - distinct: Different request → skip

4. For merge candidates, identify canonical:
   - Most upvotes wins
   - If tied, oldest wins
```

#### 3e. Present Result

Present a compact review card. No code blocks, no raw HTML. Titles as headings outside blockquotes. Separate blockquotes for Current/Desired/Voice with blank lines between them. Rich context with linked Linear issues.

---

{author name} | {N} upvotes | {date} | Surface: {surface}
{postUrl}

### {original title} (original)
> {1-2 sentence plain-text summary of original content}

---

### {new title}

> **Current Behavior:**
> - {bullet points — what exists today, sourced from KB}

> **Desired Behavior:**
> - {bullet points — what the user wants}

> **User Voice:** "{verbatim quote}" — {author name}

Tags: {suggested tags}
Duplicates: {None / Likely duplicate of [{title}]({link}) ({N} upvotes) / Related: [{title}]({link})}
Context:
- {bulleted list of relevant Linear issues with links, status, and brief description}
- {KB findings if any}

Suggested action: {approve / merge / reject / needs-pm-input}

approve / edit / skip / reject / not-mine?

---

Keep it short. Omit context/duplicates lines entirely if nothing was found — don't show empty fields.

**User chooses per item:**
- **approve** — apply rewrite + tags, clear inReview
- **edit** — user provides corrections, re-present
- **merge** — clerk provides canonical link for manual merge in Featurebase UI
- **skip** — leave as-is (stays in review queue)
- **reject** — set status per config Status Mapping, clear inReview
- **not-mine** — wrong team; add to `_state/fb-not-mine.md`, skip

### 4. Commit

Execute the chosen action immediately after user approves. **Each write requires prior approval from Step 3e.**

```
match action:
    approve →
        update_post(id, title=new_title, content=new_content, inReview=false, tags=[surface_tag, ...])

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

Update _state/fb-moderation.md with result
```

Then proceed to next post in queue.

### 5. Log & Clean Up

```
Append to ACTION_LOG.md:
    ## Featurebase Moderation — {date}
    - Processed: {N} posts
    - Approved: {N} (list titles)
    - Merged: {N}
    - Rejected: {N}
    - Skipped: {N}
    - Not mine: {N}

If batch complete → delete _state/fb-moderation.md
If interrupted → state persists for recovery
```

## Recovery

State persists in `_state/fb-moderation.md`. Re-triggering detects state and resumes from next unprocessed item. State tracks:

```markdown
## Queue
| ID | Title | Surface | Status |
|----|-------|---------|--------|
| {id} | {title} | {surface} | pending/approved/skipped/... |

## Current Position
Processing item {N} of {total}
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
→ Extract slug, search for post, gather context, rewrite, check duplicates, present for approval, commit.

**"moderate featurebase"**
→ Fetch inReview posts (~10-30), classify surfaces, filter to My Surfaces, process one at a time with immediate review.

**"triage featurebase" after interruption**
→ Detect `_state/fb-moderation.md`, report progress ("5 of 12 processed"), resume from next unprocessed item.
