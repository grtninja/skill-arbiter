import { state } from "./app_state.js";

export function parsePollProfile(payload) {
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

export function withPollGate(name, handler, options = {}) {
  const minGap = Math.max(250, Number(options.minGapMs || 0));
  const visibleOnly = Boolean(options.visibleOnly ?? true);
  const now = Date.now();
  const lastRun = state.pollLastRun[name] || 0;
  if (state.pollRunning[name] || now - lastRun < minGap) {
    return;
  }
  if (visibleOnly && document.visibilityState === "hidden") {
    return;
  }
  state.pollRunning[name] = true;
  state.pollLastRun[name] = now;
  Promise.resolve()
    .then(() => handler())
    .catch(() => null)
    .finally(() => {
      state.pollRunning[name] = false;
    });
}

export function scheduleRefresh(name, intervalMs, handler, options = {}) {
  const initialDelay = Number(options.initialDelayMs || 0);
  const visibleOnly = Boolean(options.visibleOnly ?? true);
  const interval = Math.max(5000, Number(intervalMs || 10000));
  const jitter = Math.floor(Math.random() * 2000);
  if (state.pollTimers[name]) {
    clearInterval(state.pollTimers[name]);
  }
  if (state.pollStartTimers[name]) {
    clearTimeout(state.pollStartTimers[name]);
  }
  const run = async () => {
    if (visibleOnly && document.visibilityState === "hidden") {
      return;
    }
    withPollGate(name, handler, { minGapMs: 250, visibleOnly: false });
  };
  const timer = setTimeout(() => {
    run().catch(() => null);
    state.pollTimers[name] = setInterval(run, interval);
  }, Math.max(0, initialDelay + jitter));
  state.pollStartTimers[name] = timer;
  return timer;
}

export function clearScheduledRefresh(name) {
  if (state.pollStartTimers[name]) {
    clearTimeout(state.pollStartTimers[name]);
    delete state.pollStartTimers[name];
  }
  if (state.pollTimers[name]) {
    clearInterval(state.pollTimers[name]);
    delete state.pollTimers[name];
  }
}
