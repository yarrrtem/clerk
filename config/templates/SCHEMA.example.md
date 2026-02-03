# Schema

Your vault's area definitions and routing configuration.

For generic classification rules, see `.clerk/config/schema-base.md`.

## Areas

Define your Todoist projects and corresponding vault folders:

| Todoist Project | Area Folder | Description |
|-----------------|-------------|-------------|
| Work | work/ | Your job |
| Personal | personal/ | Personal life |
| Home | home/ | Home maintenance |
| Health | health/ | Physical and mental wellbeing |
| Admin | admin/ | Finances, taxes, legal |
| Learning | learning/ | Skill development |
| Inbox | (fallback — needs triage) | Uncategorized items |

**Customize this table** with your own areas. Each area should have:
- A Todoist project with the same name
- A folder in your vault: `{area-folder}/`
- An area file: `{area-folder}/{area-name}.md` with routing keywords

**Routing:** Read `{area-folder}/{area-name}.md` for routing keywords and context.

## Example Project Structure

```
work/
  work.md
  bookmarks.md
  projects/
    current-initiative/
personal/
  personal.md
  projects/
    side-project/
```

Customize project examples to match your vault structure.
