from __future__ import annotations

from dataclasses import asdict, dataclass


SAFE_CAPABILITY_CODES = {
    "openclaw_nullclaw_tool_surface",
    "agent_tools_definition",
    "agent_resources_definition",
}

HOSTILE_CODES = {
    "known_blocked_package",
    "cross_agent_remote_install",
    "curl_pipe_shell",
    "wget_pipe_shell",
    "invoke_expression",
    "powershell_iex",
    "encoded_command",
    "frombase64",
    "fake_password_prompt",
    "silent_password_read",
    "osascript_password_dialog",
    "get_credential",
    "read_host_secure",
    "npm_global_bin_persistence",
    "scheduled_task",
    "registry_run_key",
    "launch_agents",
    "crontab_persistence",
    "python_launcher_spoof",
    "python_binary_copy",
}
ALWAYS_BLOCK_CODES = {
    "known_blocked_package",
    "fake_password_prompt",
    "silent_password_read",
    "osascript_password_dialog",
    "scheduled_task",
    "registry_run_key",
    "launch_agents",
    "crontab_persistence",
    "python_launcher_spoof",
    "python_binary_copy",
    "vendored_python_binary",
}


@dataclass(frozen=True)
class ThreatDescriptor:
    code: str
    title: str
    family: str
    why_it_matters: str
    operator_action: str
    adjacent_vectors: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


THREAT_CATALOG = {
    "cross_agent_remote_install": ThreatDescriptor(
        code="cross_agent_remote_install",
        title="Remote install chained to agent tooling",
        family="remote_execution",
        why_it_matters="A skill can turn tool or resource surfaces into remote package execution on the host.",
        operator_action="Quarantine first, then blacklist and remove unless the source is explicitly rebuilt from a trusted local path.",
        adjacent_vectors="Check sibling skills for npx, bunx, pnpm dlx, pip install, and remote bootstrap commands.",
    ),
    "global_install_command": ThreatDescriptor(
        code="global_install_command",
        title="Global package install",
        family="persistence",
        why_it_matters="Global installs widen blast radius by mutating shared runtimes and PATH-visible tools.",
        operator_action="Contain the skill, verify the package source, and strip any persistence if the install was not explicitly intended.",
        adjacent_vectors="Inspect AppData npm bins, shell profile edits, and sibling install helpers.",
    ),
    "ephemeral_exec_command": ThreatDescriptor(
        code="ephemeral_exec_command",
        title="Ephemeral package execution",
        family="remote_execution",
        why_it_matters="npx-like execution can run remote code without a pinned local artifact review step.",
        operator_action="Review the exact package name and source, then quarantine or rebuild from a pinned local artifact.",
        adjacent_vectors="Check adjacent skills for typosquats, transient installers, and remote bootstrap prompts.",
    ),
    "known_blocked_package": ThreatDescriptor(
        code="known_blocked_package",
        title="Known blocked package",
        family="known_malware",
        why_it_matters="The package matches a tracked hostile supply-chain signature.",
        operator_action="Hard block, quarantine, blacklist, and remove the installed artifact from the live surface.",
        adjacent_vectors="Search the skill stack for the same package name, aliases, and repackaged installers.",
    ),
    "possible_typosquat_package": ThreatDescriptor(
        code="possible_typosquat_package",
        title="Possible typosquat package",
        family="supply_chain",
        why_it_matters="A one-character drift from a trusted brand can redirect installs to a malicious package.",
        operator_action="Do not install or execute until the package name, publisher, and source are verified.",
        adjacent_vectors="Review nearby package references and README install snippets for lookalike names.",
    ),
    "curl_pipe_shell": ThreatDescriptor(
        code="curl_pipe_shell",
        title="curl piped to shell",
        family="remote_execution",
        why_it_matters="Directly piping a fetched script into a shell bypasses artifact review and provenance checks.",
        operator_action="Quarantine immediately and require a reviewed, pinned local installer path.",
        adjacent_vectors="Check wget, irm, iex, and bash/pwsh bootstrap patterns nearby.",
    ),
    "wget_pipe_shell": ThreatDescriptor(
        code="wget_pipe_shell",
        title="wget piped to shell",
        family="remote_execution",
        why_it_matters="Like curl-to-shell, this executes remote content with no trust boundary.",
        operator_action="Block and replace with a reviewed local artifact flow.",
        adjacent_vectors="Inspect script bootstrap blocks and README install sections.",
    ),
    "invoke_expression": ThreatDescriptor(
        code="invoke_expression",
        title="Invoke-Expression use",
        family="script_execution",
        why_it_matters="Expression-based execution makes it hard to audit what actually ran on the host.",
        operator_action="Review the generated command string and quarantine if the origin is not explicit and local.",
        adjacent_vectors="Check encoded PowerShell and downloaded command content.",
    ),
    "powershell_iex": ThreatDescriptor(
        code="powershell_iex",
        title="PowerShell IEX use",
        family="script_execution",
        why_it_matters="IEX is a common way to hide remote execution or obfuscated payload assembly.",
        operator_action="Treat as hostile until proven otherwise; audit the exact command source.",
        adjacent_vectors="Look for Invoke-WebRequest, FromBase64String, and hidden Start-Process usage.",
    ),
    "encoded_command": ThreatDescriptor(
        code="encoded_command",
        title="Encoded PowerShell command",
        family="obfuscation",
        why_it_matters="Encoded shell blocks reduce operator visibility and are a common malware delivery primitive.",
        operator_action="Decode and inspect before any execution; quarantine if the decoded intent is not trusted.",
        adjacent_vectors="Search for FromBase64String, IEX, and detached process creation.",
    ),
    "frombase64": ThreatDescriptor(
        code="frombase64",
        title="Base64 payload decode",
        family="obfuscation",
        why_it_matters="Base64 decoding is frequently used to hide payloads, credentials, or script bodies.",
        operator_action="Inspect the decoded content and block if it expands into shell execution or persistence.",
        adjacent_vectors="Check sibling scripts for encoded commands and remote fetches.",
    ),
    "detached_pythonw": ThreatDescriptor(
        code="detached_pythonw",
        title="Detached pythonw launch",
        family="stealth_runtime",
        why_it_matters="pythonw can keep code running without an attached console or visible operator context.",
        operator_action="Require explicit operator confirmation and kill or quarantine if undeclared.",
        adjacent_vectors="Look for hidden subprocess flags and startup persistence.",
    ),
    "hidden_process_launch": ThreatDescriptor(
        code="hidden_process_launch",
        title="Hidden process launch",
        family="stealth_runtime",
        why_it_matters="A hidden process can outlive the initiating app and evade normal operator review.",
        operator_action="Review the child process target and block undeclared background execution.",
        adjacent_vectors="Check pythonw, Start-Job, detached subprocesses, and scheduled tasks.",
    ),
    "detached_subprocess": ThreatDescriptor(
        code="detached_subprocess",
        title="Detached subprocess",
        family="stealth_runtime",
        why_it_matters="Detached process groups can survive app shutdown and break expected operator control.",
        operator_action="Quarantine the launcher and require an explicit declared service model before allowlisting.",
        adjacent_vectors="Inspect daemon flags, nohup, and hidden shell launches.",
    ),
    "background_job_spawn": ThreatDescriptor(
        code="background_job_spawn",
        title="Background job spawn",
        family="stealth_runtime",
        why_it_matters="Background jobs can become runaway or undeclared host workers.",
        operator_action="Contain and verify whether the job is an approved local agent or stray automation.",
        adjacent_vectors="Check scheduled tasks, nohup, detached sessions, and orphaned Python processes.",
    ),
    "broad_process_kill": ThreatDescriptor(
        code="broad_process_kill",
        title="Broad process control",
        family="destructive_control",
        why_it_matters="Force-kill logic can disrupt unrelated tools or hide prior malicious activity.",
        operator_action="Require operator confirmation and narrow the target set before execution.",
        adjacent_vectors="Inspect port-based kill helpers, taskkill /F, pkill, and netstat-driven cleanup.",
    ),
    "browser_autolaunch": ThreatDescriptor(
        code="browser_autolaunch",
        title="Browser auto-launch",
        family="operator_bypass",
        why_it_matters="Auto-opening URLs can disrupt the operator workflow or hide unsafe handoffs to web flows.",
        operator_action="Strip or disable browser-launch behavior and keep support links copy-only in the app.",
        adjacent_vectors="Check explorer/start-process URL launches and window.open calls.",
    ),
    "npm_global_bin_persistence": ThreatDescriptor(
        code="npm_global_bin_persistence",
        title="Global npm bin persistence",
        family="persistence",
        why_it_matters="Global binary directories keep code on the host after the initiating workflow completes.",
        operator_action="Blacklist the skill if the persistence was not explicitly requested and remove the dropped binary.",
        adjacent_vectors="Inspect shell profile edits, AppData npm bin changes, and package postinstall scripts.",
    ),
    "scheduled_task": ThreatDescriptor(
        code="scheduled_task",
        title="Scheduled task persistence",
        family="persistence",
        why_it_matters="Scheduled tasks can restart hostile or stale code after the operator thinks it is gone.",
        operator_action="Block by default and only allow through an explicitly declared host service flow.",
        adjacent_vectors="Check registry run keys, startup folders, and background job launchers.",
    ),
    "registry_run_key": ThreatDescriptor(
        code="registry_run_key",
        title="Registry run-key persistence",
        family="persistence",
        why_it_matters="Run keys keep code resident across logins and are a common persistence mechanism.",
        operator_action="Treat as hostile until the exact change is justified and operator-approved.",
        adjacent_vectors="Inspect scheduled tasks, shell profile edits, and Startup folder artifacts.",
    ),
    "launch_agents": ThreatDescriptor(
        code="launch_agents",
        title="LaunchAgent or LaunchDaemon persistence",
        family="persistence",
        why_it_matters="Launch agents keep background code attached to the operator profile or machine startup.",
        operator_action="Require review and explicit service ownership before allowlisting.",
        adjacent_vectors="Check shell profiles, cron, and detached runtime helpers.",
    ),
    "shell_profile_persistence": ThreatDescriptor(
        code="shell_profile_persistence",
        title="Shell profile mutation",
        family="persistence",
        why_it_matters="Profile edits can silently change future shells, PATH resolution, and login-time behavior.",
        operator_action="Review the exact profile mutation and strip it unless it is an intentional, documented install step.",
        adjacent_vectors="Inspect PATH updates, npm bin writes, and copied runtime launchers.",
    ),
    "crontab_persistence": ThreatDescriptor(
        code="crontab_persistence",
        title="Cron persistence",
        family="persistence",
        why_it_matters="Cron can keep stale or hostile jobs executing independently of the operator.",
        operator_action="Block unless the repo explicitly owns that scheduled behavior and it is operator-approved.",
        adjacent_vectors="Check scheduled tasks, launch agents, and background job helpers.",
    ),
    "fake_password_prompt": ThreatDescriptor(
        code="fake_password_prompt",
        title="Fake password prompt",
        family="credential_theft",
        why_it_matters="A spoofed system or sudo prompt can capture credentials directly from the operator.",
        operator_action="Hard block and blacklist. Do not continue until the prompt source is removed.",
        adjacent_vectors="Check osascript dialogs, secure string reads, and CLI prompt wrappers.",
    ),
    "silent_password_read": ThreatDescriptor(
        code="silent_password_read",
        title="Silent password read",
        family="credential_theft",
        why_it_matters="Hidden password entry in scripts is a direct credential capture lane.",
        operator_action="Block and remove the prompt path from the skill.",
        adjacent_vectors="Inspect shell wrappers, install scripts, and elevated execution helpers.",
    ),
    "osascript_password_dialog": ThreatDescriptor(
        code="osascript_password_dialog",
        title="macOS password dialog spoof",
        family="credential_theft",
        why_it_matters="A scripted password dialog can impersonate the OS and steal secrets.",
        operator_action="Hard block and blacklist.",
        adjacent_vectors="Search for AppleScript dialogs and GUI credential prompts.",
    ),
    "get_credential": ThreatDescriptor(
        code="get_credential",
        title="Credential prompt helper",
        family="credential_access",
        why_it_matters="Credential collection helpers may be legitimate admin tooling or a theft path, depending on context.",
        operator_action="Manual review required. Verify the operator-facing flow and scope before keep.",
        adjacent_vectors="Inspect secure string handling, persistence, and shell elevation blocks.",
    ),
    "read_host_secure": ThreatDescriptor(
        code="read_host_secure",
        title="Secure-string host input",
        family="credential_access",
        why_it_matters="Secure-string prompts may still harvest secrets in a skill path that was not meant to handle them.",
        operator_action="Review the exact purpose and remove if it is not an explicit secret-management lane.",
        adjacent_vectors="Check credential prompts, key storage, and secret export logic.",
    ),
    "python_launcher_spoof": ThreatDescriptor(
        code="python_launcher_spoof",
        title="Python launcher spoof",
        family="runtime_dropper",
        why_it_matters="Copying or renaming Python binaries is a strong sign of stealth execution or runtime smuggling.",
        operator_action="Quarantine and remove the dropped runtime immediately.",
        adjacent_vectors="Inspect python.exe/pythonw.exe copies, PATH changes, and hidden launchers.",
    ),
    "python_binary_copy": ThreatDescriptor(
        code="python_binary_copy",
        title="Python binary copy",
        family="runtime_dropper",
        why_it_matters="Vendored interpreter copies can bypass normal runtime ownership and audit controls.",
        operator_action="Strip the copied interpreter and require a declared system runtime or venv instead.",
        adjacent_vectors="Check copied DLLs, shim launchers, and startup scripts.",
    ),
    "vendored_python_binary": ThreatDescriptor(
        code="vendored_python_binary",
        title="Vendored Python binary",
        family="runtime_dropper",
        why_it_matters="A skill should not ship its own Python interpreter into the live skill surface.",
        operator_action="Strip the runtime artifact and rebuild from a clean, declared interpreter path.",
        adjacent_vectors="Inspect pythonw.exe, copied venv launchers, and hidden process helpers.",
    ),
    "python_outside_expected_dirs": ThreatDescriptor(
        code="python_outside_expected_dirs",
        title="Python outside expected directories",
        family="repo_hygiene",
        why_it_matters="Executable Python outside expected script/test lanes can hide stray or stale automation.",
        operator_action="Review placement, move or quarantine if it is not an intentional runtime file.",
        adjacent_vectors="Check backup copies, temp files, and untracked Python in the same skill.",
    ),
    "hidden_python_script": ThreatDescriptor(
        code="hidden_python_script",
        title="Hidden Python artifact",
        family="runtime_hygiene",
        why_it_matters="Dotfiles and hidden scripts can be used to evade normal review or survive cleanup.",
        operator_action="Strip into quarantine storage and restore only if explicitly required.",
        adjacent_vectors="Check stale backups, swap files, and untracked Python siblings.",
    ),
    "backup_python_script": ThreatDescriptor(
        code="backup_python_script",
        title="Backup or stale Python artifact",
        family="runtime_hygiene",
        why_it_matters="Old backup scripts can accidentally become live execution targets or hide stale logic.",
        operator_action="Strip from the live surface and keep only one canonical source file.",
        adjacent_vectors="Inspect temp copies, renamed backups, and duplicated launchers.",
    ),
    "editor_swap_python_script": ThreatDescriptor(
        code="editor_swap_python_script",
        title="Editor swap or temp Python artifact",
        family="runtime_hygiene",
        why_it_matters="Swap files and temp copies should never ship as executable skill content.",
        operator_action="Strip from the skill tree and keep them ignored locally.",
        adjacent_vectors="Check hidden files and untracked Python generated by the editor.",
    ),
    "untracked_python_script": ThreatDescriptor(
        code="untracked_python_script",
        title="Untracked Python script",
        family="runtime_hygiene",
        why_it_matters="Untracked Python in a skill tree is a direct blind spot in review, release, and provenance flows.",
        operator_action="Quarantine or add it to source control intentionally after review; do not leave it ambiguous.",
        adjacent_vectors="Inspect stale temp files, copied runtimes, and candidate overlay drift.",
    ),
    "openclaw_nullclaw_tool_surface": ThreatDescriptor(
        code="openclaw_nullclaw_tool_surface",
        title="OpenClaw or NullClaw capability surface",
        family="capability_surface",
        why_it_matters="This marks agent-tooling reach, not malware by itself. It still widens what the skill can touch.",
        operator_action="Keep if owned and intentional; pair with stricter review if remote execution or persistence also appears.",
        adjacent_vectors="Check tool definitions, MCP bridges, remote installers, and resource fan-out.",
    ),
    "agent_tools_definition": ThreatDescriptor(
        code="agent_tools_definition",
        title="Agent tool definition",
        family="capability_surface",
        why_it_matters="Tool definitions expand host reach and require provenance and guardrails, but they are not hostile on their own.",
        operator_action="Review in context with ownership and surrounding high-risk findings.",
        adjacent_vectors="Inspect resource definitions, remote installs, and process-control helpers.",
    ),
    "agent_resources_definition": ThreatDescriptor(
        code="agent_resources_definition",
        title="Agent resource definition",
        family="capability_surface",
        why_it_matters="Resource definitions increase blast radius if paired with untrusted executors or install paths.",
        operator_action="Treat as medium review unless combined with remote execution or persistence.",
        adjacent_vectors="Check MCP adapters, tool fan-out, and host filesystem access.",
    ),
}


def describe_code(code: str) -> dict[str, str]:
    descriptor = THREAT_CATALOG.get(code)
    if descriptor is None:
        title = code.replace("_", " ").strip().title() or "Unknown finding"
        descriptor = ThreatDescriptor(
            code=code,
            title=title,
            family="review",
            why_it_matters="This finding needs operator review because it changes host capability or provenance confidence.",
            operator_action="Review the surrounding skill content and decide whether to keep, quarantine, or refactor.",
            adjacent_vectors="Check nearby scripts, installers, and config mutations for the same pattern.",
        )
    return descriptor.to_dict()


def describe_codes(codes: list[str]) -> list[dict[str, str]]:
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for code in codes:
        if code in seen:
            continue
        seen.add(code)
        rows.append(describe_code(code))
    return rows
