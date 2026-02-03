# Ensure Todoist Sync

Verify Todoist projects and vault folders are in sync before processing.

## Contract

**Pre-conditions:**
- SCHEMA.md contains list of required area projects
- Todoist API is accessible

**Post-conditions:**
- All required area projects exist in Todoist
- All Todoist sub-projects have matching vault folders
- All vault project folders have matching Todoist sub-projects
- ACTION_LOG.md updated with sync status

**Errors:**
- Todoist API unavailable → abort with "Cannot connect to Todoist"
- User declines to create missing projects → abort with "Cannot proceed without required projects"
- Vault write fails → abort with error details

## Procedure

### Part 1: Area Projects

#### 1.1 Load requirements

```
required_projects = read_from("SCHEMA.md")  # e.g., [Work, Family, Home, ...]
```

#### 1.2 Fetch existing

```python
existing_projects = todoist.find_projects()
existing_names = [p.name for p in existing_projects]
```

#### 1.3 Compare

```
missing = required_projects - existing_names
```

```
✓ Verify: missing is empty
→ Continue to Part 2

✗ On fail: missing is not empty
→ Show user: "These Todoist projects need to be created: {missing}"
→ Ask: "Create them now?"
→ If yes: create each via todoist.add_project(name)
→ If no: abort "Cannot proceed without required projects"
```

### Part 2: Sub-Project Sync (Todoist → Vault)

#### 2.1 For each area project

```python
for area_project in existing_projects:
    sub_projects = todoist.find_projects(parent_id=area_project.id)

    for sub in sub_projects:
        vault_folder = kebab_case(sub.name)
        vault_path = f"{area_project.name.lower()}/projects/{vault_folder}/"

        if not exists(vault_path):
            missing_vault.append({
                "todoist_name": sub.name,
                "vault_path": vault_path
            })
```

#### 2.2 Report missing vault folders

```
✓ Verify: missing_vault is empty
→ Continue to Part 3

✗ On fail: missing_vault is not empty
→ Show user: "These Todoist projects are missing vault folders: {list}"
→ Ask: "Create vault folders now?"
→ If yes: for each, create folder + .md file per create-project template
→ If no: log warning, continue
```

### Part 3: Sub-Project Sync (Vault → Todoist)

#### 3.1 Scan vault folders

```python
vault_projects = glob("*/projects/*/")

for vault_path in vault_projects:
    area = vault_path.split("/")[0]
    folder_name = vault_path.split("/")[2]

    # Find matching Todoist sub-project
    area_project = find_todoist_project(area)
    sub_projects = todoist.find_projects(parent_id=area_project.id)

    matching = [s for s in sub_projects if kebab_case(s.name) == folder_name]

    if not matching:
        missing_todoist.append({
            "vault_path": vault_path,
            "area": area,
            "suggested_name": title_case(folder_name)
        })
```

#### 3.2 Report missing Todoist projects

```
✓ Verify: missing_todoist is empty
→ Continue to logging

✗ On fail: missing_todoist is not empty
→ Show user: "These vault projects are missing from Todoist: {list}"
→ Ask: "Create Todoist projects now?"
→ If yes: for each, create sub-project under appropriate area
→ If no: log warning, continue
```

### 4. Log & confirm

Append to ACTION_LOG.md:
```
### {date} Todoist Sync
- Area projects: {count} verified
- Sub-projects synced: {count}
- Vault folders created: {count}
- Todoist projects created: {count}
```

## Required Area Projects

From SCHEMA.md:
- Work
- Family
- Home
- Health
- Admin
- Career
- Learning
- Playground

## Kebab-Case Conversion

Todoist name → Vault folder:
- "CRM Sync" → `crm-sync`
- "Q1 Marketing Campaign" → `q1-marketing-campaign`
- "AI Thought Leadership" → `ai-thought-leadership`

## Examples

**Input:** Fresh setup, no Todoist projects exist

**Output:**
- User prompted to create 8 area projects
- After approval, all created
- Log entry added

---

**Input:** Todoist has "CRM Sync" under Work, vault missing folder

**Output:**
- User prompted: "These Todoist projects are missing vault folders: [CRM Sync]"
- After approval, creates `work/projects/crm-sync/crm-sync.md`

---

**Input:** Vault has `work/projects/new-feature/`, no matching Todoist project

**Output:**
- User prompted: "These vault projects are missing from Todoist: [new-feature]"
- After approval, creates "New Feature" sub-project under Work

---

**Edge case:** User declines to create missing area projects

**Behavior:** Abort entire processing — can't route tasks without destination projects.

---

**Edge case:** User declines to create missing vault folders

**Behavior:** Log warning, continue — sync is advisory, not blocking.

---

**Frequency:** Run on initial setup, then weekly or when projects change.
