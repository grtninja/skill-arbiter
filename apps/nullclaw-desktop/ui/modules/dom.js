import { flowStages, toneClasses } from "./app_state.js";

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function createPill(label, variant = "neutral", kind = "status-pill") {
  return `<span class="${kind} ${escapeHtml(variant)}">${escapeHtml(label)}</span>`;
}

export function normalizeTone(value) {
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

export function setFlow(stage) {
  flowStages.forEach((id) => {
    const el = document.getElementById(`flow-${id}`);
    if (el) {
      const active = flowStages.indexOf(id) <= flowStages.indexOf(stage);
      el.classList.toggle("active", active);
    }
  });
}

export function setBanner(text) {
  const el = document.getElementById("status-banner");
  if (el) {
    el.textContent = text;
  }
}

export function setText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value;
  }
}

export function setHtml(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.innerHTML = value;
  }
}

export function setFeedText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value;
  }
}

export function setCardTone(cardId, tone) {
  const el = document.getElementById(cardId);
  if (!el) {
    return;
  }
  toneClasses.forEach((name) => el.classList.remove(name));
  el.classList.add(`tone-${tone}`);
}

export function setMetricStatus(cardId, valueId, value) {
  const tone = normalizeTone(value);
  setCardTone(cardId, tone);
  setHtml(valueId, createPill(value, tone));
}

export function setMetricCount(cardId, valueId, count, tone = "neutral") {
  setCardTone(cardId, tone);
  setText(valueId, String(count));
}

export function renderTableRows(targetId, rows, cellRenderers, options = {}) {
  const root = document.getElementById(targetId);
  const subjectKey = options.subjectKey || "";
  const onSubjectSelected = options.onSubjectSelected || null;
  root.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    const subject = subjectKey ? String(row[subjectKey] || "") : "";
    if (subject && typeof onSubjectSelected === "function") {
      tr.dataset.subject = subject;
      tr.addEventListener("click", () => {
        onSubjectSelected(subject);
      });
    }
    cellRenderers.forEach((renderCell) => {
      const td = document.createElement("td");
      td.innerHTML = renderCell(row);
      tr.appendChild(td);
    });
    root.appendChild(tr);
  });
}

export function renderEmptyRow(targetId, colspan, message, tone = "neutral") {
  const root = document.getElementById(targetId);
  root.innerHTML = "";
  const tr = document.createElement("tr");
  tr.innerHTML = `<td colspan="${colspan}">${createPill(message, tone)}</td>`;
  root.appendChild(tr);
}

export async function copyText(value) {
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
