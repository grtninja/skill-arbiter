from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover - Python 3.11+ expected
    raise SystemExit(f"Python 3.11+ required for tomllib: {exc}")


DEFAULT_REQUIRED_ENV_KEYS = (
    "STARFRAME_MCP_SHIM_URL",
    "STARFRAME_MCP_SHIM_V1_URL",
    "STARFRAME_HOSTED_V1_URL",
    "STARFRAME_EMBED_V1_URL",
    "STARFRAME_CONTINUE_BRIDGE_URL",
    "STARFRAME_MCP_CORE_URL",
    "STARFRAME_MCP_UNIFIED_URL",
    "STARFRAME_SKILL_ARBITER_ROOT",
    "STARFRAME_SKILL_ROUTER",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a Codex config candidate before touching the live file."
    )
    parser.add_argument("config_path", type=Path, help="Path to the candidate config.toml")
    parser.add_argument("--require-model", default=None)
    parser.add_argument("--require-reasoning", default=None)
    parser.add_argument(
        "--require-mcp",
        action="append",
        default=[],
        help="Require an MCP server id to be active in [mcp_servers.*]",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional JSON summary path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw = args.config_path.read_text(encoding="utf-8")
    data = tomllib.loads(raw)

    errors: list[str] = []

    if args.require_model and data.get("model") != args.require_model:
        errors.append(f"model mismatch: expected {args.require_model}, got {data.get('model')}")

    if args.require_reasoning and data.get("model_reasoning_effort") != args.require_reasoning:
        errors.append(
            "model_reasoning_effort mismatch: "
            f"expected {args.require_reasoning}, got {data.get('model_reasoning_effort')}"
        )

    mcp_servers = data.get("mcp_servers")
    if not isinstance(mcp_servers, dict):
        errors.append("missing mcp_servers table")
        mcp_servers = {}

    for server_id in args.require_mcp:
        if server_id not in mcp_servers:
            errors.append(f"missing required MCP server: {server_id}")

    starframe = mcp_servers.get("starframe-local-mcp")
    if not isinstance(starframe, dict):
        errors.append("missing starframe-local-mcp table")
        env = {}
    else:
        env = starframe.get("env", {})
        if not isinstance(env, dict):
            errors.append("missing starframe-local-mcp env table")
            env = {}

    missing_env = [key for key in DEFAULT_REQUIRED_ENV_KEYS if key not in env]
    if missing_env:
        errors.append("missing required env keys: " + ", ".join(missing_env))

    skills = data.get("skills", {})
    skill_rows = skills.get("config", []) if isinstance(skills, dict) else []
    projects = data.get("projects", {})

    summary = {
        "config_path": str(args.config_path),
        "parse_ok": True,
        "model": data.get("model"),
        "model_reasoning_effort": data.get("model_reasoning_effort"),
        "active_mcp": sorted(mcp_servers.keys()),
        "skill_config_count": len(skill_rows) if isinstance(skill_rows, list) else 0,
        "trusted_project_count": len(projects) if isinstance(projects, dict) else 0,
        "errors": errors,
    }

    if args.json_out is not None:
        args.json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
