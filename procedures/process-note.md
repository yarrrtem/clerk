# Process Note

Enrich a #note item with metadata for vault commit.

## Contract

**Pre-conditions:**
- Item is tagged #note #processing
- Item has `original:` field
- SCHEMA.md defines routing rules

**Post-conditions:**
- Item has required fields based on note type:
  - **Media:** `destination:`, `media_type:`, `media_entry:`, `append_to_section:`
  - **Bookmark:** `destination:`, `bookmark_entry:`, `append_to_section:`, optionally `create_task:`
  - **General:** `destination:`, `filename:`, `content:`, `links:`
- Item is either #ready-to-review or #blocked

**Errors:**
- URL fetch fails → continue with available context, log warning
- Cannot determine destination → #blocked with `blocked_on: "Which area?"`
- Web search for media metadata fails → use available info from original

## Note Types

| Type | Signals | Destination |
|------|---------|-------------|
| Media | Book title, movie, TV show, "by [author]" | `{area}/books-and-movies.md` |
| Bookmark | URL to article, video, thread | `{area}/bookmarks.md` |
| General | Observations, thoughts, context | `{area}/` or project folder |

## Procedure

### 1. URL Detection & Enrichment

```python
if contains_url(item.original):
    url = extract_url(item.original)
    try:
        # Try built-in WebFetch first
        page_content = WebFetch(url)
        item.url_summary = summarize(page_content, bullets=5)
    except (403, 500, blocked):
        # Fallback to headless browser for sites that block programmatic access
        try:
            page_content = mcp_headless_browser.fetch_url(url)
            item.url_summary = summarize(page_content, bullets=5)
        except:
            log_warning("Both WebFetch and headless browser failed")
            item.url_summary = None
    except:
        log_warning("URL fetch failed, continuing with original text")
        item.url_summary = None
```

**Tool fallback:** If WebFetch returns 403/500 or appears blocked, use the `fetch_url` tool from the `headless-browser` MCP server. This handles sites like Medium, Substack, and other platforms with bot detection.

```
✓ Verify: url_summary populated (if URL present)
✗ On fail: continue without summary
```

### 2. Determine target area

```python
context = item.url_summary or item.original
target_area = match_to_area(context, SCHEMA_MD)

if not target_area:
    target_area = "playground"  # default
```

```
✓ Verify: target_area is valid area from SCHEMA.md
✗ On fail: default to "playground"
```

### 3. Detect note type and route

#### 3a. Media Detection (Books/Movies/TV)

```python
if is_media_reference(item.original):
    item.media_type = detect_media_type(item.original)  # book, movie, tv-show

    # Look up metadata
    metadata = web_search(f"{item.original} {item.media_type}")

    item.media_entry = format_media_entry(
        title=metadata.title,
        creator=metadata.author_or_director,
        year=metadata.year,
        summary=metadata.one_liner
    )

    item.destination = f"{target_area}/books-and-movies.md"
    item.append_to_section = section_for_media_type(item.media_type)
    # e.g., "## Books", "## Movies", "## TV Shows"

    goto step_8  # Skip to transition
```

```
✓ Verify: media_entry has title, creator, year, summary
✗ On fail: use original text, mark for review
```

#### 3b. Bookmark Detection (Articles/Videos)

```python
if contains_url(item.original):
    surrounding_text = extract_surrounding_text(item.original)

    # Determine intent
    engage_signals = ["need to read", "watch this", "read carefully",
                      "important", "review this", "check out", "I should"]
    reference_signals = ["interesting", "FYI", "saw this"]

    intent = "engage" if any(s in surrounding_text for s in engage_signals) else "reference"

    item.bookmark_entry = format_bookmark_entry(
        title=item.url_summary.title or url,
        source=extract_domain(url),
        type=detect_content_type(url),  # article, video, thread
        summary=item.url_summary.bullets
    )

    item.destination = f"{target_area}/bookmarks.md"
    item.append_to_section = section_for_content_type(item.bookmark_entry.type)
    # e.g., "## Articles", "## Videos"

    if intent == "engage":
        item.create_task = True
        item.task_title = f"{'Read' if is_article else 'Watch'}: {item.bookmark_entry.title}"
        item.task_project = todoist_project_for_area(target_area)
        item.task_priority = "p4"

    goto step_8  # Skip to transition
```

```
✓ Verify: bookmark_entry has title, source, type, summary
✗ On fail: use URL as title, skip summary
```

#### 3c. General Note

```python
# Determine destination
item.destination = determine_note_destination(item.original, target_area)
# Could be area folder or specific project folder

if not item.destination:
    apply_blocked(item, "Which area or project does this belong to?")
    return
```

```
✓ Verify: destination is valid path
✗ On fail: fallback to "_inbox/" or block
```

### 4. Determine filename (general notes only)

```python
if item.source_path:  # From _inbox/
    original_filename = basename(item.source_path)
    if is_descriptive(original_filename):
        item.filename = original_filename
    else:
        item.filename = generate_filename(item.original)
else:
    item.filename = generate_filename(item.original)
    # kebab-case, descriptive, e.g., "elena-visual-learning.md"
```

```
✓ Verify: filename is kebab-case and descriptive
✗ On fail: generate from first few words of content
```

### 5. Fetch context (general notes only)

```python
destination_files = glob(f"{item.destination}/*.md")
related_notes = find_related(item.original, destination_files, limit=3)
item.links = [note.filename for note in related_notes]
```

### 6. Check related Todoist tasks (general notes only)

```python
related_tasks = todoist.find_tasks(search=keywords(item.original))
if related_tasks:
    item.related_tasks = related_tasks[:3]
```

### 7. Generate content (general notes only)

```python
item.content = rewrite_for_clarity(item.original)
# Preserve detail and tone
# original: field already has verbatim copy
```

### 8. Transition

```python
item.tags.remove("#processing")
item.tags.append("#ready-to-review")
move_to_section(item, "Ready for Review")
```

```
✓ Verify: item in "Ready for Review" section
✗ On fail: abort "Failed to update PROCESSING.md"
```

## Entry Formats (After Processing)

**Media note:**
```markdown
### Item {N}
#note #ready-to-review
original: "The Origins of Wealth"
source: backlog
media_type: book
target_area: personal
destination: personal/books-and-movies.md
append_to_section: "## Books"
media_entry: "- **The Origin of Wealth** (2006) — Eric D. Beinhocker. Exploration of complexity economics."
```

**Bookmark (reference):**
```markdown
### Item {N}
#note #ready-to-review
original: "https://example.com/article"
source: backlog
target_area: work
destination: work/bookmarks.md
append_to_section: "## Articles"
bookmark_entry: |
  ### Article Title
  **Source:** example.com | **Type:** article
  - Key point 1
  - Key point 2
  [Original](https://example.com/article)
```

**Bookmark (engage):**
```markdown
### Item {N}
#note #ready-to-review
original: "need to read https://example.com/important-article"
source: backlog
target_area: work
destination: work/bookmarks.md
append_to_section: "## Articles"
bookmark_entry: |
  ### Important Article
  **Source:** example.com | **Type:** article
  - Summary point 1
  - Summary point 2
  [Original](https://example.com/important-article)
create_task: true
task_title: "Read: Important Article"
task_project: Work
task_priority: p4
```

**General note:**
```markdown
### Item {N}
#note #ready-to-review
original: "Elena learns better with visual aids"
source: backlog
target_area: famiglia
destination: famiglia/
filename: elena-visual-learning.md
content: "Elena seems to respond well to visual learning aids. Consider incorporating more diagrams and pictures in learning activities."
links: [elena-development.md, parenting-observations.md]
```

## Edge Cases

**URL fetch fails:** Log warning, use URL as title, skip summary bullets, continue processing.

**Ambiguous area:** Default to "playground", or block if more context needed.
