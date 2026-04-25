---
name: "feishu-wiki"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Navigate and manage Feishu Wiki spaces and nodes via the feishu_wiki tool. Use when listing spaces, browsing wiki trees, creating or moving wiki pages, renaming nodes, or resolving a wiki node into the backing Docx object for feishu_doc edits."
---

# Feishu Wiki Tool

Single tool `feishu_wiki` for knowledge base operations across Feishu Wiki spaces and nodes.

## Workflow

1. Start with `spaces` or `nodes` to understand the current wiki structure.
2. Use `get` on a wiki token when you need the backing `obj_token` and `obj_type`.
3. Use `feishu_doc` for the page content itself once you have the resolved `obj_token`.
4. Apply the smallest structural action needed in the wiki layer (`create`, `move`, `rename`).
5. Re-query the node tree to verify the final location and title.

From URL `https://xxx.feishu.cn/wiki/ABC123def` -> `token` = `ABC123def`

## Actions Summary

| Action | Description |
| ------ | ----------- |
| `spaces` | List accessible wiki spaces |
| `nodes` | List nodes in a space or under a parent node |
| `get` | Resolve wiki node details including `obj_token` |
| `create` | Create a wiki node or page |
| `move` | Move a node within or across spaces |
| `rename` | Rename an existing node |

## Wiki-Doc Workflow

To edit a wiki page:

1. Get node: `{ "action": "get", "token": "wiki_token" }` → returns `obj_token`
2. Read doc: `feishu_doc { "action": "read", "doc_token": "obj_token" }`
3. Write doc: `feishu_doc { "action": "write", "doc_token": "obj_token", "content": "..." }`

## Key Constraints

- `feishu_wiki` manages the structure; `feishu_doc` manages wiki page content.
- `obj_type` defaults to `docx`, but can also be `sheet`, `bitable`, `mindnote`, `file`, `doc`, or `slides`.
- Cross-space moves should be verified carefully because both target space and parent location matter.

## Configuration

```yaml
channels:
  feishu:
    tools:
      wiki: true # default: true
      doc: true # required - wiki content uses feishu_doc
```

**Dependency:** This tool requires `feishu_doc` to be enabled. Wiki pages are documents - use `feishu_wiki` to navigate, then `feishu_doc` to read/edit content.

## Permissions

Required: `wiki:wiki` or `wiki:wiki:readonly`

## Guardrails

- Use local or trusted tools only; avoid untrusted install pipelines.
- Do not paste secrets/tokens into chat output.
- Keep outputs in deterministic local paths for reproducible review.
