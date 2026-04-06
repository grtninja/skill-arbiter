export const API_BASE = "http://127.0.0.1:17665";
export const flowStages = ["app-open", "agent-start", "checks", "loads", "ready"];
export const toneClasses = ["tone-ok", "tone-warn", "tone-bad", "tone-neutral"];

export const SEVERITY_ORDER = {
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

function defaultInventoryState() {
  return {
    skills: [],
    incidents: [],
    sources: [],
    legitimacy_summary: {},
    interop_sources: [],
  };
}

function defaultPollProfile() {
  return {
    health_ms: 60000,
    passive_inventory_ms: 300000,
    skill_game_ms: 0,
    collaboration_ms: 0,
    stack_runtime_ms: 0,
  };
}

export const state = {
  currentCaseId: "",
  inventoryState: defaultInventoryState(),
  casesState: [],
  lastPassiveInventoryRefreshAt: 0,
  bootstrapHydrated: false,
  pollStartTimers: {},
  pollProfile: defaultPollProfile(),
  pollRunning: {},
  pollLastRun: {},
  pollTimers: {},
};
