# Clerk

A productivity system built for [Claude Code](https://claude.ai/code), but compatible with Cursor and other AI coding assistants.

## What it does

- Collects inputs from multiple sources (BACKLOG.md, inbox folder, Todoist, Granola meetings)
- Classifies items as tasks, notes, or instructions
- Enriches with metadata (priority, labels, due dates)
- Routes to appropriate destinations (Todoist projects, vault folders)
- Presents batched reviews for human approval before committing

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
