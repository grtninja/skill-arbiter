const API_BASE = "http://127.0.0.1:17665";
const flowStages = ["app-open", "agent-start", "checks", "loads", "ready"];
const toneClasses = ["tone-ok", "tone-warn", "tone-bad", "tone-neutral"];

let currentCaseId = "";
let inventoryState = { skills: [], incidents: [], sources: [], legitimacy_summary: {}, interop_sources: [] };
let casesState = [];
let lastPassiveInventoryRefreshAt = 0;
let bootstrapHydrated = false;
const pollStartTimers = {};
let pollProfile = {
  health_ms: 60000,
  passive_inventory_ms: 300000,
  skill_game_ms: 0,
  collaboration_ms: 0,
  stack_runtime_ms: 0,
};
const pollRunning = {};
const pollLastRun = {};
const pollTimers = {};

const SEVERITY_ORDER = {
  critical: 0,
  blocked: 0,
  hostile: 0,
  high: 1,
  medium: 2,
  review: 2,
  warn: 2,
  accepted: 3,
  low: 3,
  trusted: 4,
  observe: 5,
  monitor: 5,
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

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

function severityRank(value) {
  return SEVERITY_ORDER[String(value || "").toLowerCase()] ?? 9;
}

function normalizeTone(value) {
  const raw = String(value || "").toLowerCase();
  if (["ok", "pass", "ready", "enabled", "on", "trusted", "keep", "observe"].includes(raw)
    || raw.includes("trusted")) {
    return "ok";
  }
  if (["accepted", "accepted_review", "official_accepted", "owned_accepted", "manual_accepted"].includes(raw)
    || raw.includes("accepted")) {
    return "neutral";
  }
  if (["critical", "fail", "blocked", "hostile", "deny", "disabled", "off"].includes(raw)
    || raw.includes("critical")
    || raw.includes("blocked")
    || raw.includes("hostile")
    || raw.includes("fail")) {
    return "bad";
  }
  if (["high", "warn", "warning", "pending", "review", "manual_review", "manual review", "starting", "monitor"].includes(raw)
    || raw.includes("high")
    || raw.includes("review")
    || raw.includes("pending")
    || raw.includes("warn")
    || raw.includes("watch")
    || raw.includes("monitor")) {
    return "warn";
  }
  return "neutral";
}

function createPill(label, variant = "neutral", kind = "status-pill") {
  return `<span class="${kind} ${escapeHtml(variant)}">${escapeHtml(label)}</span>`;
}

function setFlow(stage) {
  flowStages.forEach((id) => {
    const el = document.getElementById(`flow-${id}`);
    if (el) {
      const active = flowStages.indexOf(id) <= flowStages.indexOf(stage);
      el.classList.toggle("active", active);
    }
  });
}

function setBanner(text) {
  const el = document.getElementById("status-banner");
  if (el) {
    el.textContent = text;
  }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value;
  }
}

function setHtml(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.innerHTML = value;
  }
}

function setFeedText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value;
  }
}

function setCardTone(cardId, tone) {
  const el = document.getElementById(cardId);
  if (!el) {
    return;
  }
  toneClasses.forEach((name) => el.classList.remove(name));
  el.classList.add(`tone-${tone}`);
}

function setMetricStatus(cardId, valueId, value) {
  const tone = normalizeTone(value);
  setCardTone(cardId, tone);
  setHtml(valueId, createPill(value, tone));
}

function setMetricCount(cardId, valueId, count, tone = "neutral") {
  setCardTone(cardId, tone);
  setText(valueId, String(count));
}

function parsePollProfile(payload) {
  const profile = payload?.poll_profile || payload?.stack_runtime_contract?.poll_profile || {};
  const sanitize = (value, fallback) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
  };
  return {
    health_ms: sanitize(profile.health_ms, 60000),
    passive_inventory_ms: sanitize(profile.passive_inventory_ms, 300000),
    skill_game_ms: 0,
    collaboration_ms: 0,
    stack_runtime_ms: 0,
  };
}

function withPollGate(name, handler, options = {}) {
  const minGap = Math.max(250, Number(options.minGapMs || 0));
  const visibleOnly = Boolean(options.visibleOnly ?? true);
  const now = Date.now();
  const lastRun = pollLastRun[name] || 0;
  if (pollRunning[name] || now - lastRun < minGap) {
    return;
  }
  if (visibleOnly && document.visibilityState === "hidden") {
    return;
  }
  pollRunning[name] = true;
  pollLastRun[name] = now;
  Promise.resolve()
    .then(() => handler())
    .catch(() => null)
    .finally(() => {
      pollRunning[name] = false;
    });
}

function scheduleRefresh(name, intervalMs, handler, options = {}) {
  const initialDelay = Number(options.initialDelayMs || 0);
  const visibleOnly = Boolean(options.visibleOnly ?? true);
  const interval = Math.max(5000, Number(intervalMs || 10000));
  const jitter = Math.floor(Math.random() * 2000);
  if (pollTimers[name]) {
    clearInterval(pollTimers[name]);
  }
  if (pollStartTimers[name]) {
    clearTimeout(pollStartTimers[name]);
  }
  const run = async () => {
    if (visibleOnly && document.visibilityState === "hidden") {
      return;
    }
    withPollGate(name, handler, { minGapMs: 250, visibleOnly: false });
  };
  const timer = setTimeout(() => {
    run().catch(() => null);
    pollTimers[name] = setInterval(run, interval);
  }, Math.max(0, initialDelay + jitter));
  pollStartTimers[name] = timer;
  return timer;
}

function clearScheduledRefresh(name) {
  if (pollStartTimers[name]) {
    clearTimeout(pollStartTimers[name]);
    delete pollStartTimers[name];
  }
  if (pollTimers[name]) {
    clearInterval(pollTimers[name]);
    delete pollTimers[name];
  }
}

function renderSubagentPayload(prefix, payload) {
  const source = payload?.source || "unknown";
  const active = payload?.active_subagents || [];
  const eventCount = payload?.observed_event_count || 0;
  setText(`${prefix}-source`, String(source));
  setText(`${prefix}-count`, String(active.length));
  setText(`${prefix}-event-count`, String(eventCount));
  setFeedText(`${prefix}-detail`, active.length
    ? active.map((row) => `${row.name} · ${row.state || "active"} (${row.event_count || 0})`).join("\n")
    : "No active subagents reported.");
}

function renderAgentRuntimePayload(payload) {
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

function setSelectedSubject(value) {
  const input = document.getElementById("mitigation-subject");
  if (input) {
    input.value = value || "";
  }
  renderSubjectDetails((value || "").trim());
}

function selectedSubject() {
  return (document.getElementById("mitigation-subject")?.value || "").trim();
}

function attachSubjectClick(tr, subject) {
  if (!subject) {
    return;
  }
  tr.dataset.subject = subject;
  tr.addEventListener("click", () => {
    setSelectedSubject(subject);
    setBanner(`Selected subject: ${subject}`);
  });
}

function renderTableRows(targetId, rows, cellRenderers, subjectKey = "") {
  const root = document.getElementById(targetId);
  root.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    const subject = subjectKey ? String(row[subjectKey] || "") : "";
    attachSubjectClick(tr, subject);
    cellRenderers.forEach((renderCell) => {
      const td = document.createElement("td");
      td.innerHTML = renderCell(row);
      tr.appendChild(td);
    });
    root.appendChild(tr);
  });
}

function summarizeInventory(payload) {
  const skills = payload.skills || [];
  const incidents = payload.incidents || [];
  const driftCount = skills.filter((row) => String(row.drift_state || "").includes("missing_local_builtin") || String(row.drift_state || "").includes("local_system_drift")).length;
  const candidateCount = skills.filter((row) => row.source_type === "overlay_candidate").length;
  const manualReviewCount = skills.filter((row) =>
    row.local_presence === "installed"
    && ["official_review", "official_sensitive", "owned_review", "owned_sensitive", "manual_review", "baseline_review"].includes(String(row.legitimacy_status || ""))
  ).length;
  const criticalRiskCount = incidents.filter((row) => String(row.severity || "").toLowerCase() === "critical").length;
  const highRiskCount = incidents.filter((row) => String(row.severity || "").toLowerCase() === "high").length;
  const blockedHostile = payload.legitimacy_summary?.blocked_hostile || 0;

  setText("drift-count", String(driftCount));
  setText("candidate-count", String(candidateCount));
  setText("manual-review-count", String(manualReviewCount));
  setText("manual-review-count-side", String(manualReviewCount));
  setText("critical-risk-count", String(criticalRiskCount));
  setText("high-risk-count", String(highRiskCount));
  setText("blocked-hostile-count-top", String(blockedHostile));
  setText("blocked-hostile-count", String(blockedHostile));
  setText("blocked-hostile-count-side", String(blockedHostile));
}

function sortSkills(skills) {
  return [...skills].sort((left, right) => {
    const legitimacyDelta = severityRank(left.legitimacy_status) - severityRank(right.legitimacy_status);
    if (legitimacyDelta !== 0) {
      return legitimacyDelta;
    }
    const riskDelta = severityRank(left.risk_class) - severityRank(right.risk_class);
    if (riskDelta !== 0) {
      return riskDelta;
    }
    const actionDelta = severityRank(left.recommended_action) - severityRank(right.recommended_action);
    if (actionDelta !== 0) {
      return actionDelta;
    }
    return String(left.name || "").localeCompare(String(right.name || ""));
  });
}

function sortIncidents(incidents) {
  return [...incidents].sort((left, right) => {
    const severityDelta = severityRank(left.severity) - severityRank(right.severity);
    if (severityDelta !== 0) {
      return severityDelta;
    }
    return String(left.subject || "").localeCompare(String(right.subject || ""));
  });
}

function sortSources(sources) {
  return [...sources].sort((left, right) => {
    const leftWatch = isResearchWatchSource(left) ? 1 : 0;
    const rightWatch = isResearchWatchSource(right) ? 1 : 0;
    if (leftWatch !== rightWatch) {
      return leftWatch - rightWatch;
    }
    const riskDelta = severityRank(left.risk_class) - severityRank(right.risk_class);
    if (riskDelta !== 0) {
      return riskDelta;
    }
    return String(left.source_id || "").localeCompare(String(right.source_id || ""));
  });
}

function isResearchWatchSource(row) {
  const presence = String(row?.local_presence || "").toLowerCase();
  return presence === "reference_only" || presence === "tracked_reference";
}

function sourceRiskMeta(row) {
  if (isResearchWatchSource(row)) {
    return { label: "research-watch", variant: "watch" };
  }
  return {
    label: row?.risk_class || "monitor",
    variant: row?.risk_class || "monitor",
  };
}

function sourceActionMeta(row) {
  if (isResearchWatchSource(row)) {
    return { label: "watchlist", variant: "neutral" };
  }
  return {
    label: row?.recommended_action || "observe",
    variant: normalizeTone(row?.recommended_action),
  };
}

function renderEmptyRow(targetId, colspan, message, tone = "neutral") {
  const root = document.getElementById(targetId);
  root.innerHTML = "";
  const tr = document.createElement("tr");
  tr.innerHTML = `<td colspan="${colspan}">${createPill(message, tone)}</td>`;
  root.appendChild(tr);
}

function sortInterop(rows) {
  return [...rows].sort((left, right) => {
    const leftPresence = String(left.local_presence || "").toLowerCase() === "present" ? 0 : 1;
    const rightPresence = String(right.local_presence || "").toLowerCase() === "present" ? 0 : 1;
    if (leftPresence !== rightPresence) {
      return leftPresence - rightPresence;
    }
    return String(left.source_id || "").localeCompare(String(right.source_id || ""));
  });
}

function buildPriorityRows(payload) {
  const priorityMap = new Map();
  (payload.skills || []).forEach((skill) => {
    if (String(skill.local_presence || "") !== "installed") {
      return;
    }
    const legitimacy = String(skill.legitimacy_status || "").toLowerCase();
    const risk = String(skill.risk_class || "").toLowerCase();
    const sourceType = String(skill.source_type || "").toLowerCase();
    const action = String(skill.recommended_action || "").toLowerCase();
    const thirdPartyInstalled =
      sourceType === "installed_skill" &&
      !["official_trusted", "owned_trusted"].includes(legitimacy) &&
      !String(skill.origin || "").toLowerCase().includes("openai_builtin") &&
      !String(skill.origin || "").toLowerCase().includes("overlay_candidate_installed");
    const actionableThirdPartyInstalled =
      thirdPartyInstalled &&
      !["keep", "observe", "accepted"].includes(action) &&
      ["critical", "high", "medium"].includes(risk);
    if (
      !["blocked_hostile", "needs_review", "manual_review", "accepted_review"].includes(legitimacy) &&
      !actionableThirdPartyInstalled
    ) {
      return;
    }
    const severity =
      legitimacy === "blocked_hostile" || risk === "critical"
        ? "critical"
        : risk === "high"
          ? "high"
          : "review";
    priorityMap.set(skill.name, {
      subject: skill.name,
      severity,
      ownership: skill.ownership || "pending",
      legitimacy: skill.legitimacy_status || "pending",
      action: skill.recommended_action || "review",
      summary: skill.legitimacy_reason || "Skill requires operator review.",
    });
  });
  (payload.incidents || []).forEach((incident) => {
    const existing = priorityMap.get(incident.subject);
    const severity = String(incident.severity || "review").toLowerCase();
    const candidate = {
      subject: incident.subject,
      severity,
      ownership: incident.ownership || existing?.ownership || "pending",
      legitimacy: incident.legitimacy_status || existing?.legitimacy || "pending",
      action: incident.recommended_steps?.[0] || existing?.action || "review",
      summary: incident.summary || existing?.summary || "Incident requires operator review.",
    };
    if (!existing || severityRank(candidate.severity) < severityRank(existing.severity)) {
      priorityMap.set(incident.subject, candidate);
    }
  });
  return [...priorityMap.values()]
    .sort((left, right) => {
      const severityDelta = severityRank(left.severity) - severityRank(right.severity);
      if (severityDelta !== 0) {
        return severityDelta;
      }
      return String(left.subject || "").localeCompare(String(right.subject || ""));
    })
    .slice(0, 60);
}

function skillForSubject(subject) {
  return (inventoryState.skills || []).find((row) => row.name === subject) || null;
}

function incidentsForSubject(subject) {
  return (inventoryState.incidents || []).filter((row) => row.subject === subject);
}

function caseForSubject(subject) {
  return casesState.find((row) => row.subject === subject) || null;
}

function formatFindingDetails(details, incidents) {
  if (!details || !details.length) {
    return "No detailed findings were cached for this subject.";
  }
  const lines = [];
  details.forEach((detail) => {
    lines.push(`- ${detail.title || detail.code}`);
    lines.push(`  Family: ${detail.family || "review"}`);
    if (detail.message) {
      lines.push(`  Match: ${detail.message}`);
    }
    lines.push(`  Why: ${detail.why_it_matters || "Needs operator review."}`);
    lines.push(`  Action: ${detail.operator_action || "Review manually."}`);
    lines.push(`  Adjacent: ${detail.adjacent_vectors || "Check neighboring skills and scripts."}`);
    lines.push("");
  });
  if (incidents && incidents.length) {
    const uniqueSteps = [...new Set(incidents.flatMap((row) => row.recommended_steps || []))];
    if (uniqueSteps.length) {
      lines.push(`Recommended incident steps: ${uniqueSteps.join(" -> ")}`);
    }
  }
  return lines.join("\n").trim();
}

function statusGlyph(status) {
  if (status === "done") {
    return "[x]";
  }
  if (status === "skipped") {
    return "[-]";
  }
  return "[ ]";
}

function formatRunbook(caseRow, incidents, skill) {
  if (!caseRow) {
    const steps = [...new Set((incidents || []).flatMap((row) => row.recommended_steps || []))];
    if (!skill && !steps.length) {
      return "Plan a mitigation case to render the runbook here.";
    }
    return [
      `Ownership: ${skill?.ownership || "pending"}`,
      `Legitimacy: ${skill?.legitimacy_status || "pending"}`,
      `Reason: ${skill?.legitimacy_reason || "No legitimacy note cached."}`,
      "",
      `Immediate path: ${steps.length ? steps.join(" -> ") : "plan_case -> quarantine -> review"}`,
    ].join("\n");
  }
  const lines = [
    `Path: ${caseRow.recommended_path || "pending"}`,
    `${caseRow.operator_summary || caseRow.summary || "No case summary available."}`,
    "",
    "Steps:",
  ];
  (caseRow.steps || []).forEach((step) => {
    const confirmation = step.requires_confirmation ? " | confirm" : "";
    const auto = step.auto_allowed ? " | auto" : "";
    lines.push(`${statusGlyph(step.status)} ${step.label}: ${step.summary}${confirmation}${auto}`);
  });
  return lines.join("\n");
}

function renderCasesFeed() {
  const root = document.getElementById("cases-feed");
  if (!casesState.length) {
    root.textContent = "No mitigation cases yet.";
    return;
  }
  const lines = [];
  casesState.forEach((row) => {
    lines.push(`[${row.severity}] ${row.subject}`);
    lines.push(`  Class: ${row.classification}`);
    lines.push(`  Path: ${row.recommended_path || "pending"}`);
    lines.push(`  Next: ${(row.next_actions || []).join(" -> ") || "none"}`);
    lines.push(`  Summary: ${row.operator_summary || row.summary || "No summary."}`);
    lines.push("");
  });
  root.textContent = lines.join("\n").trim();
}

function renderInterop(payload) {
  const legitimacy = payload.legitimacy_summary || {};
  setText("official-trusted-count", String(legitimacy.official_trusted || 0));
  setText("owned-trusted-count", String(legitimacy.owned_trusted || 0));
  setText("accepted-review-count", String(legitimacy.accepted_review || 0));
  setText("needs-review-count", String(legitimacy.needs_review || 0));
  const interopRows = sortInterop((payload.interop_sources || []).map((row) => ({
    source_id: row.source_id,
    compatibility_surface: row.compatibility_surface || row.origin || "",
    local_presence: row.local_presence,
    notes: (row.notes || []).join(", "),
  })));
  renderTableRows("interop-body", interopRows, [
    (row) => escapeHtml(row.source_id),
    (row) => escapeHtml(row.compatibility_surface),
    (row) => createPill(row.local_presence || "pending", normalizeTone(row.local_presence)),
    (row) => escapeHtml(row.notes),
  ]);
}

function renderPriorityQueue(payload) {
  const rows = buildPriorityRows(payload);
  const root = document.getElementById("priority-body");
  root.innerHTML = "";
  if (!rows.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="6">${createPill("clear", "ok")} No critical or high findings are currently queued.</td>`;
    root.appendChild(tr);
    return;
  }
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.className = `priority-${normalizeTone(row.severity) === "bad" ? "critical" : normalizeTone(row.severity) === "warn" ? "high" : "review"}`;
    attachSubjectClick(tr, row.subject);
    tr.innerHTML = [
      `<td>${createPill(row.severity, row.severity, "severity-pill")}</td>`,
      `<td>${escapeHtml(row.subject)}</td>`,
      `<td>${createPill(row.ownership || "pending", normalizeTone(row.ownership))}</td>`,
      `<td>${createPill(row.legitimacy || "pending", row.legitimacy === "blocked_hostile" ? "blocked" : normalizeTone(row.legitimacy), "severity-pill")}</td>`,
      `<td>${createPill(row.action || "review", normalizeTone(row.action))}</td>`,
      `<td>${escapeHtml(row.summary)}</td>`,
    ].join("");
    root.appendChild(tr);
  });
}

function renderSubjectDetails(subject) {
  const normalized = (subject || "").trim();
  setText("selected-subject-label", normalized || "none");
  if (!normalized) {
    setText("selected-subject-meta", "Select a skill or incident to explain findings and stage a mitigation case.");
    setText("selected-ownership", "pending");
    setText("selected-legitimacy", "No legitimacy decision yet.");
    setText("selected-path", "pending");
    setText("selected-path-detail", "Plan a case to branch into rebuild, review, or hostile containment.");
    setText("selected-next-actions", "pending");
    document.getElementById("finding-explainer").textContent = "Select a skill or incident to explain why the console flagged it.";
    document.getElementById("runbook-feed").textContent = "Plan a case to render the mitigation runbook here.";
    return;
  }

  const skill = skillForSubject(normalized);
  const incidents = incidentsForSubject(normalized);
  const caseRow = caseForSubject(normalized);
  currentCaseId = caseRow?.case_id || "";
  const details = (skill && skill.finding_details && skill.finding_details.length)
    ? skill.finding_details
    : (incidents[0]?.finding_details || []);
  const nextActions = caseRow?.next_actions || incidents[0]?.recommended_steps || [];
  const ownership = skill?.ownership || (caseRow?.source_domain || "pending");
  const legitimacy = skill?.legitimacy_status || caseRow?.classification || "pending";
  const legitimacyReason = skill?.legitimacy_reason || caseRow?.summary || "No legitimacy note cached.";
  const meta = [];
  if (skill?.source_type) {
    meta.push(skill.source_type);
  }
  if (skill?.risk_class) {
    meta.push(`risk=${skill.risk_class}`);
  }
  if (legitimacy) {
    meta.push(`legitimacy=${legitimacy}`);
  }
  setText("selected-subject-meta", meta.join(" | ") || "Selected from the current inventory.");
  setText("selected-ownership", ownership);
  setText("selected-legitimacy", legitimacyReason);
  setText("selected-path", caseRow?.recommended_path || "not planned");
  setText("selected-path-detail", caseRow?.operator_summary || "Plan a case to branch the mitigation path.");
  setText("selected-next-actions", nextActions.length ? nextActions.join(" -> ") : "plan_case");
  document.getElementById("finding-explainer").textContent = formatFindingDetails(details, incidents);
  document.getElementById("runbook-feed").textContent = formatRunbook(caseRow, incidents, skill);
}

async function copyText(value) {
  if (!value) {
    return;
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(value);
    setBanner(`Copied: ${value}`);
    return;
  }
  const area = document.createElement("textarea");
  area.value = value;
  area.style.position = "fixed";
  area.style.left = "-1000px";
  document.body.appendChild(area);
  area.select();
  document.execCommand("copy");
  document.body.removeChild(area);
  setBanner(`Copied: ${value}`);
}

function renderSupportChannels(channels) {
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
      copyText(item.value || "").catch((error) => setBanner(error.message));
    });

    row.appendChild(label);
    row.appendChild(value);
    row.appendChild(action);
    root.appendChild(row);
  });
}

async function refreshSkillGame() {
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

async function refreshCollaboration() {
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

function renderSkillGameError(error) {
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

function renderCollaborationError(error) {
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
    const banner = payload.advisor_status === "offline"
      ? "Window open. Local arbitration agent attached. Advisor offline; deterministic mode is active."
      : "Window open. Local arbitration agent attached.";
    setBanner(banner);
    const profile = parsePollProfile(payload);
    pollProfile = profile;
    return payload;
  } catch (error) {
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

async function runSelfChecks() {
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

async function refreshInventory() {
  setFlow("loads");
  setBanner("Refreshing local skill and source inventory.");
  const payload = await api("/v1/inventory/refresh", "POST", {});
  inventoryState = payload;

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
  ], "name");

  renderTableRows("incidents-body", incidents.slice(0, 120), [
    (row) => createPill(row.severity || "review", row.severity, "severity-pill"),
    (row) => escapeHtml(row.subject),
    (row) => escapeHtml(row.summary),
  ], "subject");

  const activeSources = sources.filter((row) => !isResearchWatchSource(row)).slice(0, 120);
  const researchWatchlist = sources.filter((row) => isResearchWatchSource(row)).slice(0, 120);
  if (activeSources.length) {
    renderTableRows("sources-active-body", activeSources, [
      (row) => escapeHtml(row.source_id),
      (row) => {
        const meta = sourceRiskMeta(row);
        return createPill(meta.label, meta.variant, "severity-pill");
      },
      (row) => {
        const meta = sourceActionMeta(row);
        return createPill(meta.label, meta.variant);
      },
    ]);
  } else {
    renderEmptyRow("sources-active-body", 3, "clear", "ok");
  }
  if (researchWatchlist.length) {
    renderTableRows("sources-watchlist-body", researchWatchlist, [
      (row) => escapeHtml(row.source_id),
      () => createPill("research-watch", "watch", "severity-pill"),
      () => createPill("watchlist", "neutral"),
    ]);
  } else {
    renderEmptyRow("sources-watchlist-body", 3, "none", "neutral");
  }

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
  if (now - lastPassiveInventoryRefreshAt < 5000) {
    return;
  }
  lastPassiveInventoryRefreshAt = now;
  await refreshInventory().catch(() => null);
}

async function refreshPublicReadiness() {
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
  const profile = parsePollProfile(payload);
  pollProfile = profile;
  renderSupportChannels(payload.support_channels || []);
}

async function refreshAuditLog() {
  const payload = await api("/v1/audit-log");
  document.getElementById("audit-feed").textContent = JSON.stringify(payload.events || [], null, 2);
}

async function refreshCases() {
  const payload = await api("/v1/mitigation/cases");
  casesState = payload.cases || [];
  renderCasesFeed();
  renderSubjectDetails(selectedSubject());
}

async function completeBootstrap(healthPayload = null) {
  if (bootstrapHydrated) {
    return;
  }
  bootstrapHydrated = true;
  clearScheduledRefresh("bootstrap-recover");
  await runSelfChecks();
  await refreshInventory();
  await refreshSkillGame().catch((error) => {
    renderSkillGameError(error);
    setBanner(`Skill Game refresh failed: ${error.message}`);
  });
  await refreshCollaboration().catch((error) => {
    renderCollaborationError(error);
    setBanner(`Collaboration refresh failed: ${error.message}`);
  });
  await refreshPublicReadiness();
  await refreshAuditLog();
  await refreshCases();
  const profileFromHealth = parsePollProfile(healthPayload || {});
  const profile = pollProfile;
  pollProfile = {
    health_ms: Math.max(60000, profile.health_ms || profileFromHealth.health_ms),
    passive_inventory_ms: Math.max(300000, profile.passive_inventory_ms || profileFromHealth.passive_inventory_ms),
    skill_game_ms: 0,
    collaboration_ms: 0,
    stack_runtime_ms: 0,
  };
  scheduleRefresh("health", pollProfile.health_ms, () => refreshHealth(), {
    initialDelayMs: 0,
    visibleOnly: false,
  });
  scheduleRefresh("inventory", pollProfile.passive_inventory_ms, () => passiveRefreshInventory(), {
    initialDelayMs: Math.min(300000, pollProfile.health_ms + 5000),
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
}

async function planMitigationCase() {
  const subject = selectedSubject();
  if (!subject) {
    throw new Error("select or enter a subject first");
  }
  const payload = await api("/v1/mitigation/plan", "POST", { subject });
  currentCaseId = payload.case.case_id;
  casesState = [payload.case, ...casesState.filter((row) => row.case_id !== payload.case.case_id)];
  setBanner(`Mitigation case planned for ${subject}`);
  renderSubjectDetails(subject);
  await refreshCases();
}

async function runMitigationAction(action) {
  const confirmationMap = {
    strip: "Strip suspicious artifacts for the selected subject?",
    rebuild: "Rebuild the selected subject from a trusted source?",
    remove_or_refactor: "Remove the installed subject or mark the candidate for refactor?",
  };
  if (confirmationMap[action] && !window.confirm(confirmationMap[action])) {
    setBanner(`Mitigation action cancelled: ${action}`);
    return;
  }
  if (!currentCaseId) {
    await planMitigationCase();
  }
  const payload = await api("/v1/mitigation/execute", "POST", { case_id: currentCaseId, action });
  currentCaseId = payload.case.case_id;
  casesState = [payload.case, ...casesState.filter((row) => row.case_id !== payload.case.case_id)];
  setBanner(`Mitigation action completed: ${action}`);
  renderSubjectDetails(payload.case.subject);
  await refreshCases();
  await refreshAuditLog();
  if (action === "repeat" || action === "rebuild" || action === "remove_or_refactor") {
    await refreshInventory();
  }
}

async function acceptSelectedReview() {
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

async function revokeSelectedReview() {
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

async function bootstrap() {
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

document.getElementById("run-checks").addEventListener("click", () => {
  runSelfChecks().catch((error) => setBanner(error.message));
});
document.getElementById("refresh-inventory").addEventListener("click", () => {
  refreshInventory().catch((error) => setBanner(error.message));
});
document.getElementById("refresh-skill-game").addEventListener("click", () => {
  refreshSkillGame().catch((error) => {
    renderSkillGameError(error);
    setBanner(`Skill Game refresh failed: ${error.message}`);
  });
});
document.getElementById("refresh-collaboration").addEventListener("click", () => {
  refreshCollaboration().catch((error) => {
    renderCollaborationError(error);
    setBanner(`Collaboration refresh failed: ${error.message}`);
  });
});
document.getElementById("refresh-readiness").addEventListener("click", () => {
  refreshPublicReadiness().catch((error) => setBanner(error.message));
});
document.getElementById("refresh-log").addEventListener("click", () => {
  refreshAuditLog().catch((error) => setBanner(error.message));
});
document.getElementById("plan-mitigation").addEventListener("click", () => {
  planMitigationCase().catch((error) => setBanner(error.message));
});
document.getElementById("accept-review").addEventListener("click", () => {
  acceptSelectedReview().catch((error) => setBanner(error.message));
});
document.getElementById("revoke-review").addEventListener("click", () => {
  revokeSelectedReview().catch((error) => setBanner(error.message));
});
document.getElementById("mitigate-quarantine").addEventListener("click", () => {
  runMitigationAction("quarantine").catch((error) => setBanner(error.message));
});
document.getElementById("mitigate-strip").addEventListener("click", () => {
  runMitigationAction("strip").catch((error) => setBanner(error.message));
});
document.getElementById("mitigate-request").addEventListener("click", () => {
  runMitigationAction("request").catch((error) => setBanner(error.message));
});
document.getElementById("mitigate-rebuild").addEventListener("click", () => {
  runMitigationAction("rebuild").catch((error) => setBanner(error.message));
});
document.getElementById("mitigate-blacklist").addEventListener("click", () => {
  runMitigationAction("blacklist").catch((error) => setBanner(error.message));
});
document.getElementById("mitigate-remove").addEventListener("click", () => {
  runMitigationAction("remove_or_refactor").catch((error) => setBanner(error.message));
});
document.getElementById("mitigate-repeat").addEventListener("click", () => {
  runMitigationAction("repeat").catch((error) => setBanner(error.message));
});

bootstrap().catch((error) => setBanner(error.message));
