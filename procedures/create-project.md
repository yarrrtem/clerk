# Create Project

Create a new project with synchronized Todoist and vault representation.

## Contract

**Pre-conditions:**
- Project name provided
- Parent area provided and exists in SCHEMA.md
- Parent area has corresponding Todoist project

**Post-conditions:**
- Todoist sub-project exists under area's project
- Vault folder exists at `{area}/projects/{kebab-case}/`
- Vault file exists at `{area}/projects/{kebab-case}/{kebab-case}.md`
- ACTION_LOG.md updated

**Errors:**
- Area not in SCHEMA.md → abort with "Unknown area: {area}"
- Area's Todoist project not found → run ensure-todoist-sync first
- Todoist API fails → retry 3x, then abort with error details
- Vault folder already exists → skip creation, log "already exists"

## Procedure

### 1. Parse & validate

Extract from user input:
- `project_name`: Title Case (e.g., "CRM Sync")
- `area`: lowercase (e.g., "work")
- `status`: optional, default "Active"
- `description`: optional

```
✓ Verify: area exists in SCHEMA.md
✗ On fail: "Unknown area '{area}'. Valid areas: {list from SCHEMA}"
```

### 2. Derive identifiers

```
todoist_name = project_name                    # "CRM Sync"
vault_folder = kebab-case(project_name)        # "crm-sync"
vault_path   = {area}/projects/{vault_folder}/ # "work/projects/crm-sync/"
vault_file   = {vault_path}{vault_folder}.md   # "work/projects/crm-sync/crm-sync.md"
```

### 3. Check for duplicates

```
✓ Verify: No Todoist sub-project with same name under area
✗ On fail: "Project '{project_name}' already exists in Todoist"

✓ Verify: No vault folder at vault_path
✗ On fail: Log "Vault folder exists, skipping creation" (continue)
```

### 4. Create Todoist project

```python
parent_id = find_todoist_project(area)  # e.g., Work's ID
new_project = todoist.add_project(
    name=todoist_name,
    parent_id=parent_id
)
```

```
✓ Verify: new_project.id exists
✗ On fail: Retry 3x, then abort "Todoist API error: {details}"
```

### 5. Create vault folder & file

```bash
mkdir -p {vault_path}
```

Write `{vault_file}`:
```markdown
# {project_name}

{description if provided, otherwise omit this line}

## Status
{status}

## Context

## Notes
```

```
✓ Verify: vault_file exists and is readable
✗ On fail: Abort "Failed to create vault file: {error}"
```

### 6. Log & confirm

Append to ACTION_LOG.md:
```
### {date} Create Project
- Created: {area} > {project_name}
- Todoist ID: {new_project.id}
- Vault: {vault_file}
```

Return to user:
```
Created project "{project_name}" under {area}:
- Todoist: {area} > {project_name}
- Vault: {vault_file}
```

## Examples

**Input:** "create project CRM Sync under Work"

**Output:**
- Todoist: sub-project "CRM Sync" under Work (ID: abc123)
- Vault: `work/projects/crm-sync/crm-sync.md`
- Log entry added

---

**Input:** "create project Weekly Planning under Admin with status Active"

**Output:**
- Todoist: sub-project "Weekly Planning" under Admin
- Vault: `admin/projects/weekly-planning/weekly-planning.md`

---

**Edge case:** Project already exists in Todoist but not vault

**Behavior:** Abort with "Project 'X' already exists in Todoist. Run ensure-todoist-sync to create missing vault folder."

---

**Edge case:** Vault folder exists but not Todoist project

**Behavior:** Log "Vault folder exists", create Todoist project, continue.
