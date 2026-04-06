import { SEVERITY_ORDER, state } from "./app_state.js";
import {
  createPill,
  escapeHtml,
  normalizeTone,
  renderEmptyRow,
  renderTableRows,
  setBanner,
  setText,
} from "./dom.js";

function severityRank(value) {
  return SEVERITY_ORDER[String(value || "").toLowerCase()] ?? 9;
}

export function setSelectedSubject(value) {
  const input = document.getElementById("mitigation-subject");
  if (input) {
    input.value = value || "";
  }
  renderSubjectDetails((value || "").trim());
}

export function selectedSubject() {
  return (document.getElementById("mitigation-subject")?.value || "").trim();
}

export function summarizeInventory(payload) {
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

export function sortSkills(skills) {
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

export function sortIncidents(incidents) {
  return [...incidents].sort((left, right) => {
    const severityDelta = severityRank(left.severity) - severityRank(right.severity);
    if (severityDelta !== 0) {
      return severityDelta;
    }
    return String(left.subject || "").localeCompare(String(right.subject || ""));
  });
}

export function sortSources(sources) {
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

export function isResearchWatchSource(row) {
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
      sourceType === "installed_skill"
      && !["official_trusted", "owned_trusted"].includes(legitimacy)
      && !String(skill.origin || "").toLowerCase().includes("openai_builtin")
      && !String(skill.origin || "").toLowerCase().includes("overlay_candidate_installed");
    const actionableThirdPartyInstalled =
      thirdPartyInstalled
      && !["keep", "observe", "accepted"].includes(action)
      && ["critical", "high", "medium"].includes(risk);
    if (
      !["blocked_hostile", "needs_review", "manual_review", "accepted_review"].includes(legitimacy)
      && !actionableThirdPartyInstalled
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
  return (state.inventoryState.skills || []).find((row) => row.name === subject) || null;
}

function incidentsForSubject(subject) {
  return (state.inventoryState.incidents || []).filter((row) => row.subject === subject);
}

function caseForSubject(subject) {
  return state.casesState.find((row) => row.subject === subject) || null;
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

export function renderCasesFeed() {
  const root = document.getElementById("cases-feed");
  if (!state.casesState.length) {
    root.textContent = "No mitigation cases yet.";
    return;
  }
  const lines = [];
  state.casesState.forEach((row) => {
    lines.push(`[${row.severity}] ${row.subject}`);
    lines.push(`  Class: ${row.classification}`);
    lines.push(`  Path: ${row.recommended_path || "pending"}`);
    lines.push(`  Next: ${(row.next_actions || []).join(" -> ") || "none"}`);
    lines.push(`  Summary: ${row.operator_summary || row.summary || "No summary."}`);
    lines.push("");
  });
  root.textContent = lines.join("\n").trim();
}

export function renderInterop(payload) {
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

export function renderPriorityQueue(payload) {
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
    tr.dataset.subject = row.subject;
    tr.addEventListener("click", () => {
      setSelectedSubject(row.subject);
      setBanner(`Selected subject: ${row.subject}`);
    });
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

export function renderSubjectDetails(subject) {
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
  state.currentCaseId = caseRow?.case_id || "";
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

export function renderSourceTables(sources) {
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
}
