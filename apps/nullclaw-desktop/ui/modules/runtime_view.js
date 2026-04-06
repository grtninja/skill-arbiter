import {
  copyText,
  setFeedText,
  setText,
} from "./dom.js";

export function renderSubagentPayload(prefix, payload) {
  const source = payload?.source || "unknown";
  const active = payload?.active_subagents || [];
  const eventCount = payload?.observed_event_count || 0;
  setText(`${prefix}-source`, String(source));
  setText(`${prefix}-count`, String(active.length));
  setText(`${prefix}-event-count`, String(eventCount));
  setFeedText(
    `${prefix}-detail`,
    active.length
      ? active.map((row) => `${row.name} · ${row.state || "active"} (${row.event_count || 0})`).join("\n")
      : "No active subagents reported.",
  );
}

export function renderAgentRuntimePayload(payload) {
  const runtime = payload?.stack_runtime || {};
  const local = runtime?.local_supervision || {};
  const vscode = local?.vscode || {};
  const advisor = local?.advisor || {};
  const activeTasks = local?.active_tasks || [];
  const workspaceHints = vscode?.workspace_hints || [];
  const qwenModels = advisor?.qwen_models || [];
  setText("runtime-vscode-count", String(vscode.window_count || 0));
  setText("runtime-task-count", String(activeTasks.length || 0));
  setText("runtime-qwen-count", String(qwenModels.length || 0));
  setText("game-vscode-count", String(vscode.window_count || 0));
  setText("game-active-task-count", String(activeTasks.length || 0));
  setText("game-qwen-count", String(qwenModels.length || 0));
  setFeedText(
    "runtime-local-detail",
    [
      `VS Code windows: ${vscode.window_count || 0}`,
      `Workspace hints: ${workspaceHints.length ? workspaceHints.join(", ") : "none"}`,
      `Active tasks: ${activeTasks.length ? activeTasks.join("; ") : "none"}`,
    ].join("\n"),
  );
  setFeedText("runtime-supervisor-note", advisor.note || payload?.advisor_note || "Local Qwen supervisor note unavailable.");
  setFeedText(
    "skill-game-runtime",
    [
      `Selected advisor model: ${advisor.selected_model || "unknown"}`,
      `Visible Qwen lanes: ${qwenModels.length ? qwenModels.join(", ") : "none"}`,
      `Active tasks: ${activeTasks.length ? activeTasks.join("; ") : "none"}`,
      `Supervisor note: ${advisor.note || payload?.advisor_note || "none"}`,
    ].join("\n"),
  );
}

export function renderSupportChannels(channels) {
  const root = document.getElementById("support-links");
  root.innerHTML = "";
  (channels || []).forEach((item) => {
    const row = document.createElement("div");
    row.className = "support-item";

    const label = document.createElement("strong");
    label.textContent = item.label || "Link";

    const value = document.createElement("code");
    value.textContent = item.value || "";

    const action = document.createElement("button");
    action.className = "copy-btn ghost";
    action.type = "button";
    action.textContent = "Copy";
    action.addEventListener("click", () => {
      copyText(item.value || "").catch(() => null);
    });

    row.appendChild(label);
    row.appendChild(value);
    row.appendChild(action);
    root.appendChild(row);
  });
}

export function renderSkillGameError(error) {
  const message = error?.message || String(error);
  setText("game-level", "error");
  setText("game-xp", "error");
  setText("game-streak", "error");
  setText("game-target-count", "error");
  setText("game-original-count", "error");
  setFeedText("skill-game-feed", `Skill Game refresh failed.\n${message}`);
  setFeedText("skill-game-targets", "Skill Game targets unavailable until refresh succeeds.");
  setFeedText("skill-game-levels", "Original skill levels unavailable until refresh succeeds.");
  setText("game-vscode-count", "error");
  setText("game-active-task-count", "error");
  setText("game-qwen-count", "error");
  setFeedText("skill-game-runtime", "Live local supervision unavailable.");
}

export function renderCollaborationError(error) {
  const message = error?.message || String(error);
  setText("collaboration-count", "error");
  setText("collaboration-stable-count", "error");
  setText("collaboration-target-count", "error");
  setText("collaboration-trust-status", "error");
  setText("collaboration-mx3-mode", "error");
  setText("collaboration-mx3-feeder", "error");
  setText("collaboration-mx3-seq", "error");
  setText("collaboration-subagents-source", "error");
  setText("collaboration-subagents-count", "error");
  setText("collaboration-subagents-event-count", "error");
  setFeedText("collaboration-subagents-detail", `Collaboration subagent refresh failed.\n${message}`);
  setFeedText("collaboration-feed", `Collaboration refresh failed.\n${message}`);
  setFeedText("collaboration-targets", "Collaboration-derived skill work is unavailable until refresh succeeds.");
}
