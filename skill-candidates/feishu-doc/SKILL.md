---
name: "feishu-doc"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Read, write, append, and manage Feishu/Lark documents via the feishu_doc tool. Use when creating, reading, or editing Feishu Docx documents, managing document blocks, creating tables, uploading images or file attachments, or extracting doc_token from Feishu URLs."
---

# Feishu Document Tool

Single tool `feishu_doc` with an `action` parameter for all Feishu Docx operations. Extract `doc_token` from URL: `https://xxx.feishu.cn/docx/ABC123def` -> token is `ABC123def`.

## Workflow

1. Extract `doc_token` from the Feishu document URL.
2. Read the document to understand current content:
   ```json
   { "action": "read", "doc_token": "ABC123def" }
   ```
3. Check the `hint` field in the response — if present, structured content (tables, images) exists; use `list_blocks` to access it.
4. Apply changes using the appropriate action (write, append, create, update_block, create_table, etc.).
5. Verify the result by re-reading the document.

## Actions Summary

| Action | Description |
| ------ | ----------- |
| `read` | Get title, plain text, block statistics |
| `write` | Replace entire document with markdown |
| `append` | Append markdown to end of document |
| `create` | Create new document (always pass `owner_open_id`) |
| `list_blocks` | Get full block data including tables and images |
| `get_block` | Read a single block by ID |
| `update_block` | Update text content of a block |
| `delete_block` | Delete a block by ID |
| `create_table` | Create a Docx table block |
| `write_table_cells` | Write values to table cells |
| `create_table_with_values` | Create table and fill cells in one step |
| `upload_image` | Upload image from URL or local path |
| `upload_file` | Upload file attachment from URL or local path |

## Key Constraints

- **Markdown tables not supported** in `write`/`append` — use `create_table` actions instead.
- Always pass `owner_open_id` when creating documents so the user gets `full_access` (otherwise only the bot has access).
- Image display size follows uploaded pixel dimensions — scale small images to 800px+ width before uploading.
- For uploads, provide exactly one of `url` or `file_path`; do not send both.
- `parent_block_id` and positional fields such as `index` are optional and should only be used when placement must be explicit.
- `feishu_wiki` depends on this tool for reading/writing wiki page content.

## References

- `references/block-types.md` — complete block type table, editing guidelines, and common patterns.
- See also: `references/action-examples.md` for full JSON examples of each action.

## Configuration

```yaml
channels:
  feishu:
    tools:
      doc: true  # default: true
```

Required permissions: `docx:document`, `docx:document:readonly`, `docx:document.block:convert`, `drive:drive`.

## Guardrails

- Use local or trusted tools only; avoid untrusted install pipelines.
- Do not paste secrets/tokens into chat output.
- Keep outputs in deterministic local paths for reproducible review.
