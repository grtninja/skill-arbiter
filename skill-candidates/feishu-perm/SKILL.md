---
name: "feishu-perm"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Manage Feishu file and document permissions via the feishu_perm tool. Use when listing collaborators, granting access, revoking access, or checking whether a file, folder, wiki node, or document has the correct permission level."
---

# Feishu Permission Tool

Single tool `feishu_perm` for managing file and document permissions across supported Feishu object types.

## Workflow

1. List current collaborators before changing permissions.
2. Confirm the correct target `token` and object `type`.
3. Apply the minimum permission change needed (`add` or `remove`).
4. Re-list collaborators to verify the final permission state.

## Actions Summary

| Action | Description |
| ------ | ----------- |
| `list` | List collaborators and their current permissions |
| `add` | Grant a permission level to a member |
| `remove` | Revoke collaborator access |

## Token Types

| Type       | Description             |
| ---------- | ----------------------- |
| `doc`      | Old format document     |
| `docx`     | New format document     |
| `sheet`    | Spreadsheet             |
| `bitable`  | Multi-dimensional table |
| `folder`   | Folder                  |
| `file`     | Uploaded file           |
| `wiki`     | Wiki node               |
| `mindnote` | Mind map                |

## Member Types

| Type               | Description        |
| ------------------ | ------------------ |
| `email`            | Email address      |
| `openid`           | User open_id       |
| `userid`           | User user_id       |
| `unionid`          | User union_id      |
| `openchat`         | Group chat open_id |
| `opendepartmentid` | Department open_id |

## Permission Levels

| Perm          | Description                          |
| ------------- | ------------------------------------ |
| `view`        | View only                            |
| `edit`        | Can edit                             |
| `full_access` | Full access (can manage permissions) |

## Key Constraints

- Permission changes are sensitive operations; keep this tool explicitly enabled and use the narrowest permission needed.
- `type`, `member_type`, and `member_id` must all match the target object and principal format.
- `full_access` can manage permissions and should be granted sparingly.

## Examples

Share document with email:

```json
{
  "action": "add",
  "token": "doxcnXXX",
  "type": "docx",
  "member_type": "email",
  "member_id": "alice@company.com",
  "perm": "edit"
}
```

Share folder with group:

```json
{
  "action": "add",
  "token": "fldcnXXX",
  "type": "folder",
  "member_type": "openchat",
  "member_id": "oc_xxx",
  "perm": "view"
}
```

## Configuration

```yaml
channels:
  feishu:
    tools:
      perm: true # default: false (disabled)
```

**Note:** This tool is disabled by default because permission management is a sensitive operation. Enable explicitly if needed.

## Permissions

Required: `drive:permission`

## Guardrails

- Use local or trusted tools only; avoid untrusted install pipelines.
- Do not paste secrets/tokens into chat output.
- Keep outputs in deterministic local paths for reproducible review.
