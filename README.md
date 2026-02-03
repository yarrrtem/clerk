# Clerk

A productivity system built for [Claude Code](https://claude.ai/code), but compatible with Cursor and other AI coding assistants.

## What it does

- Collects inputs from multiple sources (BACKLOG.md, inbox folder, Todoist, Granola meetings)
- Classifies items as tasks, notes, or instructions
- Enriches with metadata (priority, labels, due dates)
- Routes to appropriate destinations (Todoist projects, vault folders)
- Presents batched reviews for human approval before committing

## Prerequisites

Clerk requires two things:

1. **A personal knowledgebase (vault)** — A folder of markdown files organized by life areas. Works great with [Obsidian](https://obsidian.md), but any markdown folder works.

2. **A Todoist account** — Tasks are managed in Todoist, with projects mirroring your vault structure.

## How it works

### Capture everywhere, process later

Throughout the day, capture thoughts quickly without worrying about organization:

- **BACKLOG.md** — Open your vault, type a line, done. One item per line.
- **Todoist Inbox** — Use the Todoist app on your phone for on-the-go capture.
- **`_inbox/` folder** — Drop longer notes as markdown files.
- **Granola** — Meeting notes sync automatically (if configured).

### Process with AI assistance

When ready, run `process backlog` in Claude Code. Clerk will:

1. Collect all pending items from every source
2. Classify each as a task, note, or instruction
3. Suggest destinations, priorities, and labels
4. Present items in batches for your review
5. Commit approved items to Todoist and your vault

You stay in control — nothing happens without your approval.

### Vault structure

Organize your vault by areas of life, with projects nested inside:

```
vault/
├── CLAUDE.md              # Entry point (references clerk)
├── SCHEMA.md              # Your areas and routing rules
├── GOALS.md               # Current priorities
├── ME.md                  # Context about you
├── BACKLOG.md             # Quick capture (one item per line)
├── _inbox/                # Longer notes to process
├── _state/                # Processing state (auto-managed)
│
├── work/                  # Area
│   ├── work.md            # Area overview
│   ├── bookmarks.md       # Saved articles/links
│   └── projects/
│       └── crm-redesign/  # Project folder
│
├── home/                  # Area
│   ├── home.md
│   └── projects/
│       └── garage-renovation/
│
├── health/                # Area
├── family/                # Area
└── ...
```

### Todoist alignment

Your Todoist projects should mirror your vault areas:

| Vault folder | Todoist project |
|--------------|-----------------|
| `work/` | Work |
| `work/projects/crm-redesign/` | Work > CRM Redesign |
| `home/` | Home |
| `home/projects/garage-renovation/` | Home > Garage Renovation |
| `health/` | Health |

When you run `process backlog`, Clerk routes tasks to the matching Todoist project and notes to the matching vault folder.

## Setup

1. Clone this repo:
   ```bash
   git clone https://github.com/yarrrtem/clerk.git ~/clerk
   ```

2. Run setup (asks for your vault path):
   ```bash
   ~/clerk/setup
   ```

3. Create required vault files from templates:
   ```bash
   cp ~/clerk/config/templates/SCHEMA.example.md ~/your-vault/SCHEMA.md
   cp ~/clerk/config/templates/GOALS.example.md ~/your-vault/GOALS.md
   cp ~/clerk/config/templates/ME.example.md ~/your-vault/ME.md
   ```

4. Create entry point in your vault:
   ```bash
   echo "@.clerk/SYSTEM.md" > ~/your-vault/CLAUDE.md
   ```

5. Open Claude Code in your vault and try:
   ```
   process backlog
   ```

## Structure

```
clerk/
├── SYSTEM.md              # Main system prompt
├── setup                   # Interactive setup script
├── config/
│   ├── schema-base.md     # Classification rules
│   ├── sources.md         # Input source definitions
│   └── templates/         # Vault file templates
├── procedures/            # Workflow definitions
│   ├── process-backlog.md
│   ├── input-triage.md
│   ├── commit-reviewed.md
│   └── ...
└── tools/
    ├── calendar/          # Fastmail CalDAV integration
    ├── contacts/          # Contacts lookup
    ├── granola-mcp/       # Meeting notes MCP server
    ├── headless-browser/  # Web scraping MCP server
    └── raycast/           # Quick capture scripts
```

## Requirements

- [Claude Code](https://claude.ai/code) CLI (or Cursor, etc.)
- Python 3.10+
- Todoist account (for task management)
- Optional: Granola (for meeting notes), Fastmail (for calendar)

## Configuration

Setup generates these files (gitignored):
- `config/paths.yaml` - vault and clerk paths
- `.claude/mcp.json` - MCP server configuration
- `.claude/settings.local.json` - Claude Code permissions
- `tools/calendar/calendars.yaml` - calendar aliases
- `tools/raycast/*.sh` - quick capture scripts

## License

MIT
