---
name: "feishu-drive"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Browse and manage Feishu Drive folders and files via the feishu_drive tool. Use when listing shared folders, inspecting file metadata, creating folders, moving files, or deleting Drive items the bot can access."
---

# Feishu Drive Tool

Single tool `feishu_drive` for cloud storage operations across Feishu Drive folders and files.

## Workflow

1. Extract `folder_token` from a Feishu Drive URL when you are targeting a specific folder.
2. Start with `list` to confirm what the bot can actually access.
3. Use `info` to inspect a specific file before moving or deleting it.
4. Apply the minimal file operation needed (`create_folder`, `move`, `delete`).
5. Re-list the target folder to verify the result.

From URL `https://xxx.feishu.cn/drive/folder/ABC123` -> `folder_token` = `ABC123`

## Actions Summary

| Action | Description |
| ------ | ----------- |
| `list` | List root or folder contents |
| `info` | Get file metadata by token and type |
| `create_folder` | Create a folder at root or inside a parent folder |
| `move` | Move a file into a target folder |
| `delete` | Delete a file or Drive item by token and type |

## File Types

| Type       | Description             |
| ---------- | ----------------------- |
| `doc`      | Old format document     |
| `docx`     | New format document     |
| `sheet`    | Spreadsheet             |
| `bitable`  | Multi-dimensional table |
| `folder`   | Folder                  |
| `file`     | Uploaded file           |
| `mindnote` | Mind map                |
| `shortcut` | Shortcut                |

## Key Constraints

- `info`, `move`, and `delete` require the correct `type` for the target object.
- `info` does not recursively search Drive; browse with `list` first when the location is uncertain.
- Bots do not have a normal user root folder. Shared folder access is the practical starting point for most bot workflows.

## Configuration

```yaml
channels:
  feishu:
    tools:
      drive: true # default: true
```

Required permissions:

- `drive:drive` - Full access (create, move, delete)
- `drive:drive:readonly` - Read only (list, info)

## Known Limitations

- **Bots have no root folder**: Feishu bots use `tenant_access_token` and don't have their own "My Space". The root folder concept only exists for user accounts. This means:
  - `create_folder` without `folder_token` will fail (400 error)
  - Bot can only access files/folders that have been **shared with it**
  - **Workaround**: User must first create a folder manually and share it with the bot, then bot can create subfolders inside it

## Guardrails

- Use local or trusted tools only; avoid untrusted install pipelines.
- Do not paste secrets/tokens into chat output.
- Keep outputs in deterministic local paths for reproducible review.
