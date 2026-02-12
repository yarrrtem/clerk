# Explore Codebase

Explore a codebase to answer questions, check feasibility, trace flows, or survey modules. Uses isolated sub-agents with full file access.

**References:** @.clerk/config/paths.yaml

## Contract

**Pre-conditions:**
- Codebase is resolvable (see Resolution Order below)
- Resolved path exists on current machine

**Post-conditions:**
- Structured findings returned in focus-appropriate format
- If called from another procedure: findings compressed into context digest

**Errors:**
- Codebase not resolvable → "Could not resolve a codebase. Provide a path or configure one in _config.md + paths.yaml"
- Path doesn't exist → "Codebase not available on this device (path: {path}). Skipping."
- Sub-agent fails → return partial results or error

## Triggers

| Command | Action |
|---------|--------|
| "explore codebase" | Run with current area, question focus |
| "check the code for X" | Run with question focus |
| "is X feasible?" | Run with feasibility focus |
| "how does X work in the code?" | Run with trace focus |
| "what's in {module}?" | Run with survey focus |
| (auto) | Called by draft-prd.md during gather phase |

## Runtime Protocol

### 0. Resolve Codebase

**Resolution order** — try each, stop at first success:

```
1. Explicit path from user (e.g., "explore codebase at ~/code/ampledash")
   → Use directly, skip config lookup

2. Area config: {area}/_config.md → extract codebase key from Tools table
   ⚠️ The Tool column contains a SYMBOLIC KEY (e.g., "ampledash"), NOT a path.
   Never use this value as a filesystem path directly.
   → Resolve key via paths.yaml codebases → {key} → path field → absolute path

3. Global fallback: paths.yaml codebases section has only one entry
   → Use it (with confirmation: "Using codebase '{name}' — correct?")

4. None resolved → ask user: "Which codebase? Provide a path or key."
```

After resolution, verify path exists on disk. If missing → abort with device-not-available message.

**Bind resolved values for prompt assembly (§3):**
```
resolved_path = <absolute path from paths.yaml>    # e.g., /Users/artem/code/ampledash
codebase_name = <key from _config.md or paths.yaml> # e.g., "ampledash"
main_branch   = <from paths.yaml, default: master>
```
These literal values are substituted into the sub-agent prompt at §3. The `{absolute_path}` placeholder in the prompt MUST be the resolved filesystem path, never the symbolic key.

### 1. Freshness Check

Ensure the codebase is current **before** exploration begins. Never explore stale code by default — the whole point is accurate answers.

**Never mutate the repo silently.** Always report state and get approval. But recommend pulling when stale.

```
1. cd {codebase_path}
2. Check: git rev-parse --abbrev-ref HEAD → current branch
3. Read main_branch from paths.yaml (default: master)
4. Check: git log -1 --format="%cr" → age of last commit

If on main branch and last commit ≤ 1 day old:
    → Report: "Codebase: {name} on `{main_branch}` (last commit: {age ago}). Looks fresh."
    → Proceed to §2.

If on main branch and last commit > 1 day old:
    → Report: "Codebase: {name} on `{main_branch}` but last commit was {age ago}."
    → Recommend: "Pull latest before exploring? [Y/n]" (default: YES)
    → If approved: git pull, then proceed
    → If declined: proceed with note "⚠️ Exploring potentially stale code"

If on a feature branch:
    → Report: "Codebase is on branch `{branch}`, not `{main_branch}`."
    → Ask: "Switch to {main_branch} and pull? Or explore current branch?"
    → No default — user must choose explicitly.

If git pull fails (network, merge conflict):
    → Report error, continue with current state, note: "⚠️ Pull failed, using local copy"
```

**Key principle:** Freshness check and pull happen BEFORE exploration, never after. Don't explore first and then discover the data was stale.

### 2. Determine Focus

| Focus | When | Output emphasis |
|-------|------|-----------------|
| `question` (default) | "Does the code support X?" | Direct answer with evidence |
| `feasibility` | During PRD drafting, "is X feasible?" | What exists, what needs building, complexity |
| `trace` | "How does feature Y work?" | Call chain, data flow, key files |
| `survey` | "What's in module Z?" | Structure, patterns, key abstractions |

If called from `draft-prd.md` → default to `feasibility`.
If user asks a direct question → default to `question`.
Infer from phrasing, or ask if ambiguous.

### 3. Build Sub-Agent Prompt

Assemble a self-contained prompt. The sub-agent receives NO conversation history.

**CLAUDE.md handling:** If the codebase has a CLAUDE.md, extract only the sections relevant to exploration (Stack, Architecture, directory structure, docs index). Skip workflow rules, linting commands, commit conventions — those are for contributors, not researchers. Cap at ~800 tokens.

```markdown
# Codebase Explorer

You are exploring a codebase to answer a specific question. You have access to
file search, content search, and file read capabilities. Explore thoroughly.

## Codebase
- Name: {codebase_name}
- Root: {absolute_path}
- Branch: {current_branch} (last commit: {date})

### Codebase Context (from CLAUDE.md)
{extracted relevant sections: Stack, Architecture, directory layout, docs index — capped ~800 tokens}

## Focus: {question|feasibility|trace|survey}

## Task
{The specific question or task}

## Area Context
{Relevant excerpts from area docs, PRD sections, or user's question — compressed
to essential context only. Include project names, feature names, team context
that helps the sub-agent understand what to look for.}

## Constraints
- Stay within: {root_path}
- Priority directories: {list from _config.md context hints, or inferred from task}
- Ignore: node_modules, vendor, tmp, log, .git, coverage, public/packs

## Exploration Guidelines
- Search for files by pattern, search content by keyword/regex, read files as needed
- You may launch parallel sub-agents for different areas of the codebase if the
  question spans multiple concerns — synthesize all findings before returning
- Read the codebase context above for directory conventions before diving in
- Follow imports and call chains to their source
- Check both backend and frontend if the question spans the stack

## Guardrails
- Budget: {see mode limits below}
- If you've read 30+ files without converging on an answer, pause and summarize
  what you've found so far rather than continuing to search
- Prefer targeted searches (specific class names, method names, route patterns)
  over broad directory scans

## Output Format
{format template for the chosen focus — see below}

Your output should be ~{budget} tokens of structured findings.
```

### 4. Check Codebase Permissions

Before launching the sub-agent, verify that read permissions exist for the resolved codebase path. Sub-agents (especially background ones) will silently fail if permissions aren't pre-approved.

**Check method:** Read the settings file at `{clerk_path}/.claude/settings.local.json` (resolve `clerk_path` from paths.yaml). Look for `Read({resolved_path}/` in the `permissions.allow` array.

```
1. Read {clerk_path}/.claude/settings.local.json
2. Parse JSON, check permissions.allow array
3. Search for any entry containing "Read({resolved_path}/"

If found → permissions_ok = true
If not found → permissions_ok = false
```

**If permissions_ok = false:**
```
Report to user:
  "Codebase read permissions not configured for {resolved_path}.
   Running exploration in foreground (interactive mode).
   After this run, I can add permissions so future explorations work in background."

→ Force foreground execution (never run_in_background)
→ After successful exploration, offer:
  "Add read permissions for {resolved_path} to settings.local.json?
   This allows future explorations to run as background agents. [Y/n]"
→ If approved: use Python to inject Read/Grep/Glob/Bash(git) permissions
  (same logic as setup script — see clerk/setup for the Python snippet)
```

**If permissions_ok = true:**
→ Proceed normally (foreground or background as appropriate)

### 5. Launch Exploration

**Critical pre-launch checks:**
1. All `{placeholders}` in the prompt from §3 are resolved to literal values
2. `{absolute_path}` contains the filesystem path (e.g., `/Users/artem/code/ampledash`), NOT the symbolic key
3. Model is set to `opus` (see § Platform Notes)
4. If permissions_ok = false → set `run_in_background: false` (foreground only)

**Claude Code invocation — single-agent (for `question` and `trace`):**
```
Task tool:
  subagent_type: "general-purpose"
  model: "opus"
  prompt: <fully assembled prompt from §3, all placeholders resolved to literals>
```

**Claude Code invocation — multi-agent coordinator (for `feasibility` and `survey`):**
```
Task tool:
  subagent_type: "general-purpose"
  model: "opus"
  prompt: <coordinator prompt — includes: "This is a large codebase. Break the
    exploration into parallel sub-agents for different layers (e.g., model, API,
    frontend, permissions) and synthesize their findings.">
```

The coordinator spawns its own sub-agents, each focused on a different concern, then synthesizes.

```
✓ Verify: sub-agent returned structured output
✗ On fail: retry once with same model, then return partial results with note
✗ Never fall back to haiku for retry — codebase exploration requires strong reasoning
```

### 6. Process Results

**If called directly by user:**
- Present findings as-is in the focus-appropriate format
- Include file:line references for easy navigation

**If called from another procedure (e.g., draft-prd):**
- Compress findings into context digest format:
  `{key finding} [source: codebase]`
- Respect the calling procedure's context budget
- Return compressed digest for inclusion in state file

### 7. Log

```
append ACTION_LOG.md:
    ### {date} Explore Codebase
    - Codebase: {name} ({path})
    - Branch: {branch} (pulled: yes|no|n/a)
    - Focus: {focus}
    - Task: {summary}
    - Caller: {direct|draft-prd|other}
```

## Output Templates

### question

```markdown
## Answer
{Direct answer to the question}

## Evidence
- `{file}:{line}` — {what this shows}
- `{file}:{line}` — {what this shows}

## Confidence: {high|medium|low}
{Brief explanation of confidence level}
```

### feasibility

```markdown
## Feasibility Assessment: {feature/capability}

### Exists Today
- {capability} — `{file}:{line}`

### Needs Building
- {capability} — estimated complexity: {trivial|moderate|significant}
  Closest existing pattern: `{file}`

### Risks / Unknowns
- {risk}

### Key Files
- `{file}` — {role in the solution}
```

### trace

```markdown
## Trace: {feature/flow name}

### Entry Point
`{file}:{line}` — {description}

### Call Chain
1. `{file}:{line}` → {what happens}
2. `{file}:{line}` → {what happens}
3. ...

### Data Flow
{input} → {transformation} → {output}
Key models: {list}

### Key Files
- `{file}` — {role}
```

### survey

```markdown
## Survey: {module/directory}

### Structure
{tree-like overview of key files and directories}

### Key Abstractions
- {class/module} — {responsibility}

### Patterns
- {pattern observed} — used in: {files}

### Entry Points
- `{file}` — {what it exposes}
```

## Context Budgets

Two separate budgets — don't conflate them:

**Exploration (how much the sub-agent reads):** Generous but not unlimited. The sub-agent should explore deeply, following call chains and reading relevant files. But include a soft guardrail: if 30+ files read without convergence, pause and summarize partial findings.

| Mode | Exploration guidance | Output budget |
|------|---------------------|--------------|
| lean | Targeted — follow the most direct path | ~2K tokens |
| standard | Thorough — explore related modules, check edge cases | ~5K tokens |
| deep | Exhaustive — multiple entry points, alternative implementations, full tradeoffs | ~10K tokens |

When called from draft-prd, output is further compressed to digest format per prd-config.md rules.

Inherit mode from the calling procedure, or default to standard for direct invocations.

## Recovery

No state file needed. Exploration is stateless — if interrupted, re-run. Results are ephemeral unless captured by a calling procedure's state file.

## Platform Notes

### Claude Code
- Sub-agents via Task tool with `model` parameter
- **Model: always use `model: "opus"` for codebase exploration** — never haiku
- Fallback chain: opus → sonnet (never haiku — codebase exploration requires strong reasoning to navigate large codebases, follow call chains, and synthesize findings)
- Sub-agents can nest (coordinator → parallel explorers)
- Codebase path passed as absolute path — Claude Code can access any directory on the filesystem

### Cursor
Add the codebase as a second workspace folder for best results — Cursor indexes both directories natively with full depth. Alternatively, use the sub-agent prompt as a self-contained handoff: open a separate Cursor window on the codebase, paste the prompt, get findings, bring them back.

### Any LLM with file access
The sub-agent prompt is fully self-contained. Give the model file access to the codebase path and the prompt works.
