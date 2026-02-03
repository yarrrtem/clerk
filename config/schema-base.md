# Schema Base

Generic classification rules and routing patterns. Vault-specific areas are defined in the vault's SCHEMA.md.

## Classification Signals

### Task Signals
- Has action verb (call, buy, fix, schedule, send, book, pay, cancel...)
- Has clear completion state (can be checked off)
- Time-sensitive or has deadline
- Imperative mood ("do X", "get Y")

### Note Signals
- Is an observation or thought (no action implied)
- Is a question or curiosity
- Is external content (URL, article, quote, reference)
- Descriptive mood ("X is Y", "noticed that...")

### Instruction Signals
- References existing task by name or description
- Uses completion language (done, finished, completed, cancel)
- Requests change to existing item (reprioritize, reschedule, move)
- Deletion language: cancel, delete, remove, nevermind
- Reschedule language: move to, postpone, due, change date
- Priority language: urgent, bump, deprioritize, p1, p2

## Classification Rules

- 2+ task signals, 0 conflicting → #task
- 2+ note signals, 0 conflicting → #note
- Matches instruction pattern → #instruction
- Mixed or weak signals → #blocked (ask user)

## Priority Guidelines

| Priority | Criteria |
|----------|----------|
| p1 | Urgent + important, time-critical, blocking others |
| p2 | Important but not urgent, should do soon |
| p3 | Normal priority, do when able |
| p4 | Low priority, nice to have, someday |

## Note Subtypes

Both media and bookmarks are routed to their relevant **area** based on content (default area if unclear).

### Media (Books/Movies/TV)
Larger time commitments — things to read or watch intentionally.

**Signals:**
- Book title, author name, "read", "by [author]"
- Movie/show title, "watch", "film", "series", "season"
- Recommendation language: "you should watch", "great book"

**Routing:** `{target_area}/books-and-movies.md`

### Bookmarks (Articles/Videos)
Shorter content — reference material or quick consumption.

**Signals:**
- URL to article, blog post, YouTube, Twitter/X thread
- Domain patterns: medium.com, substack, youtube.com, twitter.com

**Intent Detection:**

| Intent | Signals | Outcome |
|--------|---------|---------|
| Reference (default) | bare URL, "interesting", "FYI", "saw this", no context | Summary captured, no task |
| Engage | "need to read", "watch this", "important", "review this", "check out", "I should" | Summary captured + p4 task in area's Todoist project |

**Routing:** `{target_area}/bookmarks.md`

## Note Destinations

| Content Type | Destination |
|--------------|-------------|
| Books, movies, TV shows | {area}/books-and-movies.md |
| Articles, videos, threads | {area}/bookmarks.md |
| Area-related observations | {area}/ (add as sub-file) |
| Project-specific notes | {area}/projects/{project}/ |
| Unclear | _inbox/ (fallback) |

## Projects

Projects are finite initiatives with an end state. They live **inside their parent area**:

```
{area}/
  {area}.md
  bookmarks.md
  projects/
    {project-name}/
```

**Rules:**
- Each project belongs to exactly one area (pick the primary owner)
- Cross-area references use wiki-links: `[[other-area/projects/x]]`
- Todoist sub-projects mirror vault structure: `{Area} > {Project Name}`
- When a project completes, archive or delete the folder

## Labels

### Focus Level
| Label | Meaning |
|-------|---------|
| anytime | Quick task, can do in fragments, interruptible |
| scheduled | Needs a dedicated time block (30-60 min), but not intense focus |
| protected | Requires deep focus, no interruptions, "do not disturb" time |

### Planning
| Label | Meaning |
|-------|---------|
| this-week | Planned for this week (cleared weekly) |

### Other
| Label | Meaning |
|-------|---------|
| waiting | Blocked on external response |
| errand | Requires being out/traveling |
| recurring | Repeating task |
