import { API_BASE, state } from "./app_state.js";
import {
  createPill,
  escapeHtml,
  normalizeTone,
  renderTableRows,
  setBanner,
  setFeedText,
  setFlow,
  setHtml,
  setMetricCount,
  setMetricStatus,
  setText,
} from "./dom.js";
import {
  parsePollProfile,
  withPollGate,
  scheduleRefresh,
  clearScheduledRefresh,
} from "./polling.js";
import {
  renderCasesFeed,
  renderInterop,
  renderPriorityQueue,
  renderSourceTables,
  renderSubjectDetails,
  selectedSubject,
  setSelectedSubject,
  sortIncidents,
  sortSkills,
  sortSources,
  summarizeInventory,
} from "./inventory_view.js";
import {
  renderAgentRuntimePayload,
  renderCollaborationError,
  renderSkillGameError,
  renderSubagentPayload,
  renderSupportChannels,
} from "./runtime_view.js";

async function api(path, method = "GET", body = null) {
  const options = { method, headers: {}, cache: "no-store" };
  if (body !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(`${API_BASE}${path}`, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `request failed: ${path}`);
  }
  return payload;
}

function handleSubjectSelection(subject) {
  setSelectedSubject(subject);
  setBanner(`Selected subject: ${subject}`);
}

export async function refreshSkillGame() {
  const payload = await api("/v1/skill-game/status");
  setText("game-level", String(payload.level || 1));
  setText("game-xp", `${payload.total_xp || 0}`);
  setText("game-streak", `${payload.streak || 0}`);
  const targets = payload.recommended_targets || [];
  const originalLevels = payload.original_skill_levels || [];
  setText("game-target-count", String(targets.length));
  setText("game-original-count", String(payload.original_skill_count || originalLevels.length || 0));
  const recentEvents = payload.recent_events || [];
  setFeedText("skill-game-feed", recentEvents.length
    ? recentEvents.map((row) => {
      const task = row.task || "unknown";
      const delta = row.xp_delta ?? 0;
      const clearRun = row.clear_run ? "clear" : "mixed";
      return `${row.timestamp || ""} | ${task} | xp ${delta} | ${clearRun}`;
    }).join("\n")
    : "No skill-game ledger yet.");
  setFeedText("skill-game-targets", targets.length
    ? targets.map((row) => `- ${row.name} [p${row.priority}] ${row.reason}`).join("\n")
    : "No upgrade targets queued.");
  setFeedText("skill-game-levels", originalLevels.length
    ? originalLevels.map((row) => `- ${row.name} [L${row.level}] ${row.notes || ""}`).join("\n")
    : "No original skill levels mapped yet.");
  await refreshAgentRuntime().catch(() => null);
  return payload;
}

export async function refreshCollaboration() {
  const payload = await api("/v1/collaboration/status");
  const events = payload.recent_events || [];
  const targets = payload.recommended_skill_work || [];
  const mx3Runtime = payload.mx3_runtime || payload.stack_runtime?.mx3 || {};
  const subagents = payload.subagent_coordination || payload.stack_runtime?.subagent_coordination || {};
  setText("collaboration-count", String(payload.event_count || 0));
  setText("collaboration-stable-count", String(payload.stable_event_count || 0));
  setText("collaboration-target-count", String(targets.length));
  setText("collaboration-trust-status", payload.trust_ledger_available ? "online" : "offline");
  setText("collaboration-mx3-mode", mx3Runtime.mode || "unknown");
  setText("collaboration-mx3-feeder", mx3Runtime.feeder_state || "unknown");
  setText("collaboration-mx3-seq", mx3Runtime.active_sequence_name || "none");
  renderSubagentPayload("collaboration-subagents", subagents);
  setFeedText("collaboration-feed", events.length
    ? events.map((row) => {
      const who = (row.collaborators || []).join(", ") || "local";
      const scope = (row.repo_scope || []).join(", ") || "single-repo";
      return `${row.created_at || ""} | ${row.task || "untitled"} | ${row.outcome || "pending"} | ${who} | ${scope}`;
    }).join("\n")
    : "No collaboration events recorded yet.");
  setFeedText("collaboration-targets", targets.length
    ? targets.map((row) => `- ${row.name} :: ${row.action} [score ${row.score}] ${row.reason || "reason pending"}`).join("\n")
    : "No collaboration-derived skill work queued.");
  return payload;
}

async function refreshHealth() {
  try {
    const payload = await api("/v1/health");
    setHtml("host-chip", `<span class="dot"></span> Host: ${escapeHtml(payload.host_id)}`);
    setMetricStatus("agent-card", "agent-status", payload.status);
    setText("stack-mode", payload.stack_mode || "unknown");
    setText("stack-health-url", payload.stack_health_url || "not-set");
    setText("stack-runtime-status", payload.stack_runtime?.health?.status || payload.stack_runtime?.status || "unknown");
    setText("stack-runtime-mode", payload.stack_runtime?.mx3?.mode || "unknown");
    setText("stack-runtime-feeder", payload.stack_runtime?.mx3?.feeder_state || "unknown");
    setText("stack-runtime-seq", payload.stack_runtime?.mx3?.active_sequence_name || "none");
    setText("stack-runtime-seq-path", payload.stack_runtime?.mx3?.active_dfp_path || "none");
    renderSubagentPayload("health-stack-subagents", payload.stack_runtime?.subagent_coordination || {});
    renderAgentRuntimePayload({ stack_runtime: payload.stack_runtime, advisor_note: payload.advisor_detail || "" });
    const advisorText = payload.advisor_enabled
      ? `${payload.advisor_model} (${payload.advisor_status || "pending"})`
      : "disabled";
    setHtml("model-chip", `<span class="dot"></span> Advisor: ${escapeHtml(advisorText)}`);
    setHtml("version-chip", `<span class="dot"></span> Version: ${escapeHtml(payload.version || "pending")}`);
    setFlow("agent-start");
    setBanner(
      payload.advisor_status === "offline"
        ? "Window open. Local arbitration agent attached. Advisor offline; deterministic mode is active."
        : "Window open. Local arbitration agent attached.",
    );
    state.pollProfile = parsePollProfile(payload);
    return payload;
  } catch {
    setMetricStatus("agent-card", "agent-status", "starting");
    setText("stack-mode", "error");
    setText("stack-health-url", "error");
    setText("stack-runtime-status", "error");
    setText("stack-runtime-mode", "error");
    setText("stack-runtime-feeder", "error");
    setText("stack-runtime-seq", "error");
    setText("stack-runtime-seq-path", "error");
    setText("health-stack-subagents-source", "error");
    setText("health-stack-subagents-count", "error");
    setText("health-stack-subagents-event-count", "error");
    setFeedText("health-stack-subagents-detail", "Stack runtime unavailable.");
    setText("runtime-vscode-count", "error");
    setText("runtime-task-count", "error");
    setText("runtime-qwen-count", "error");
    setText("game-vscode-count", "error");
    setText("game-active-task-count", "error");
    setText("game-qwen-count", "error");
    setFeedText("runtime-local-detail", "Local runtime unavailable.");
    setFeedText("runtime-supervisor-note", "Supervisor unavailable.");
    setFeedText("skill-game-runtime", "Live local supervision unavailable.");
    setBanner("Waiting for the local arbitration agent.");
    return null;
  }
}

async function refreshAgentRuntime() {
  const payload = await api("/v1/agent-runtime/status");
  renderAgentRuntimePayload(payload);
  return payload;
}

export async function runSelfChecks() {
  setFlow("checks");
  setBanner("Running privacy and self-governance checks.");
  const payload = await api("/v1/self-checks/run", "POST", {});
  setMetricStatus("privacy-card", "privacy-status", payload.privacy_passed ? "pass" : "fail");
  const governance = payload.self_governance || {};
  const governanceText = governance.passed ? "pass" : `${governance.critical_count || 0} critical`;
  setMetricStatus("governance-card", "governance-status", governanceText);
  document.getElementById("privacy-feed").textContent = JSON.stringify(payload, null, 2);
  return payload;
}

export async function refreshInventory() {
  setFlow("loads");
  setBanner("Refreshing local skill and source inventory.");
  const payload = await api("/v1/inventory/refresh", "POST", {});
  state.inventoryState = payload;

  const incidents = sortIncidents(payload.incidents || []);
  const skills = sortSkills(payload.skills || []);
  const sources = sortSources(payload.sources || []);
  const incidentCount = payload.incident_count || 0;

  setMetricCount("skills-card", "skill-count", payload.skill_count || 0, "ok");
  setMetricCount("sources-card", "source-count", payload.source_count || 0, "neutral");
  setMetricCount("incidents-card", "incident-count", incidentCount, incidentCount > 0 ? "warn" : "ok");
  document.getElementById("advisor-note").textContent = payload.advisor_note || "Local Qwen advisor unavailable. Running deterministic-only inventory.";

  renderTableRows("skills-body", skills.slice(0, 240), [
    (row) => escapeHtml(row.name),
    (row) => escapeHtml(row.source_type),
    (row) => createPill(row.local_presence || "pending", normalizeTone(row.local_presence)),
    (row) => createPill(row.risk_class || "pending", row.legitimacy_status === "blocked_hostile" ? "blocked" : row.risk_class, "severity-pill"),
    (row) => createPill(row.recommended_action || "review", normalizeTone(row.recommended_action)),
  ], {
    subjectKey: "name",
    onSubjectSelected: handleSubjectSelection,
  });

  renderTableRows("incidents-body", incidents.slice(0, 120), [
    (row) => createPill(row.severity || "review", row.severity, "severity-pill"),
    (row) => escapeHtml(row.subject),
    (row) => escapeHtml(row.summary),
  ], {
    subjectKey: "subject",
    onSubjectSelected: handleSubjectSelection,
  });

  renderSourceTables(sources);
  summarizeInventory(payload);
  renderPriorityQueue(payload);
  renderInterop(payload);
  setFlow("ready");
  setBanner("Skill Arbiter is ready. Operator actions are enabled.");
  await refreshCases();
  const currentSubject = selectedSubject();
  const subjectStillKnown = skills.some((row) => row.name === currentSubject)
    || incidents.some((row) => row.subject === currentSubject);
  renderSubjectDetails(subjectStillKnown ? currentSubject : "");
  return payload;
}

async function passiveRefreshInventory() {
  if (typeof document !== "undefined" && document.visibilityState === "hidden") {
    return;
  }
  const now = Date.now();
  if (now - state.lastPassiveInventoryRefreshAt < 5000) {
    return;
  }
  state.lastPassiveInventoryRefreshAt = now;
  await refreshInventory().catch(() => null);
}

export async function refreshPublicReadiness() {
  const payload = await api("/v1/public-readiness/run", "POST", {});
  document.getElementById("readiness-status").textContent = payload.passed
    ? "Ready for public review"
    : `${payload.critical_count || 0} critical / ${payload.high_count || 0} high`;
  document.getElementById("readiness-feed").textContent = JSON.stringify(payload, null, 2);
  return payload;
}

async function refreshAbout() {
  const payload = await api("/v1/about");
  setText("about-application", payload.application || "Skill Arbiter Security Console");
  setText("about-version", payload.version || "pending");
  setText("about-developer", payload.developer || "grtninja");
  setText("about-license", payload.license || "MIT");
  setText("about-description", payload.description || "No description available.");
  state.pollProfile = parsePollProfile(payload);
  renderSupportChannels(payload.support_channels || []);
}

export async function refreshAuditLog() {
  const payload = await api("/v1/audit-log");
  document.getElementById("audit-feed").textContent = JSON.stringify(payload.events || [], null, 2);
}

async function refreshCases() {
  const payload = await api("/v1/mitigation/cases");
  state.casesState = payload.cases || [];
  renderCasesFeed();
  renderSubjectDetails(selectedSubject());
}

async function hydrateDeferredPanels() {
  await refreshSkillGame().catch((error) => {
    renderSkillGameError(error);
  });
  await refreshCollaboration().catch((error) => {
    renderCollaborationError(error);
  });
  await refreshPublicReadiness().catch(() => null);
  await refreshAuditLog().catch(() => null);
}

async function completeBootstrap(healthPayload = null) {
  if (state.bootstrapHydrated) {
    return;
  }
  state.bootstrapHydrated = true;
  clearScheduledRefresh("bootstrap-recover");
  await runSelfChecks();
  await refreshInventory();
  const profileFromHealth = parsePollProfile(healthPayload || {});
  const profile = state.pollProfile;
  state.pollProfile = {
    health_ms: Math.max(60000, profile.health_ms || profileFromHealth.health_ms),
    passive_inventory_ms: Math.max(300000, profile.passive_inventory_ms || profileFromHealth.passive_inventory_ms),
    skill_game_ms: 0,
    collaboration_ms: 0,
    stack_runtime_ms: 0,
  };
  scheduleRefresh("health", state.pollProfile.health_ms, () => refreshHealth(), {
    initialDelayMs: 0,
    visibleOnly: false,
  });
  scheduleRefresh("inventory", state.pollProfile.passive_inventory_ms, () => passiveRefreshInventory(), {
    initialDelayMs: Math.min(300000, state.pollProfile.health_ms + 5000),
    visibleOnly: true,
  });
  window.addEventListener("focus", () => {
    withPollGate("health", () => refreshHealth(), { minGapMs: 10000, visibleOnly: false });
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      withPollGate("health", () => refreshHealth(), { minGapMs: 10000, visibleOnly: false });
    }
  });
  window.setTimeout(() => {
    hydrateDeferredPanels().catch(() => null);
  }, 250);
}

export async function planMitigationCase() {
  const subject = selectedSubject();
  if (!subject) {
    throw new Error("select or enter a subject first");
  }
  const payload = await api("/v1/mitigation/plan", "POST", { subject });
  state.currentCaseId = payload.case.case_id;
  state.casesState = [payload.case, ...state.casesState.filter((row) => row.case_id !== payload.case.case_id)];
  setBanner(`Mitigation case planned for ${subject}`);
  renderSubjectDetails(subject);
  await refreshCases();
}

export async function runMitigationAction(action) {
  const confirmationMap = {
    strip: "Strip suspicious artifacts for the selected subject?",
    rebuild: "Rebuild the selected subject from a trusted source?",
    remove_or_refactor: "Remove the installed subject or mark the candidate for refactor?",
  };
  if (confirmationMap[action] && !window.confirm(confirmationMap[action])) {
    setBanner(`Mitigation action cancelled: ${action}`);
    return;
  }
  if (!state.currentCaseId) {
    await planMitigationCase();
  }
  const payload = await api("/v1/mitigation/execute", "POST", { case_id: state.currentCaseId, action });
  state.currentCaseId = payload.case.case_id;
  state.casesState = [payload.case, ...state.casesState.filter((row) => row.case_id !== payload.case.case_id)];
  setBanner(`Mitigation action completed: ${action}`);
  renderSubjectDetails(payload.case.subject);
  await refreshCases();
  await refreshAuditLog();
  if (action === "repeat" || action === "rebuild" || action === "remove_or_refactor") {
    await refreshInventory();
  }
}

export async function acceptSelectedReview() {
  const subject = selectedSubject();
  if (!subject) {
    throw new Error("select a reviewed subject first");
  }
  const payload = await api("/v1/review/accept", "POST", { subject });
  setBanner(`Accepted review for ${subject}`);
  await refreshInventory();
  await refreshCases();
  await refreshAuditLog();
  return payload;
}

export async function revokeSelectedReview() {
  const subject = selectedSubject();
  if (!subject) {
    throw new Error("select a reviewed subject first");
  }
  const payload = await api("/v1/review/revoke", "POST", { subject });
  setBanner(`Revoked accepted review for ${subject}`);
  await refreshInventory();
  await refreshCases();
  await refreshAuditLog();
  return payload;
}

export async function bootstrap() {
  setFlow("app-open");
  await refreshAbout().catch(() => null);
  let healthPayload = null;
  let attached = false;
  for (let attempt = 0; attempt < 30; attempt += 1) {
    healthPayload = await refreshHealth();
    attached = Boolean(healthPayload);
    if (attached) {
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  if (!attached) {
    setBanner("Agent unavailable. Review the local Python/runtime state.");
    scheduleRefresh("bootstrap-recover", 5000, async () => {
      const recovered = await refreshHealth();
      if (recovered) {
        await completeBootstrap(recovered);
      }
    }, {
      initialDelayMs: 1000,
      visibleOnly: false,
    });
    return;
  }
  await completeBootstrap(healthPayload);
}
