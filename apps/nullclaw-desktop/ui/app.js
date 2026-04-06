import { setBanner } from "./modules/dom.js";
import {
  acceptSelectedReview,
  bootstrap,
  planMitigationCase,
  refreshAuditLog,
  refreshCollaboration,
  refreshInventory,
  refreshPublicReadiness,
  refreshSkillGame,
  revokeSelectedReview,
  runMitigationAction,
  runSelfChecks,
} from "./modules/app_runtime.js";
import {
  renderCollaborationError,
  renderSkillGameError,
} from "./modules/runtime_view.js";

function bindAction(id, handler) {
  document.getElementById(id).addEventListener("click", () => {
    handler().catch((error) => setBanner(error.message));
  });
}

function bindRefreshWithRenderer(id, handler, errorRenderer, label) {
  document.getElementById(id).addEventListener("click", () => {
    handler().catch((error) => {
      errorRenderer(error);
      setBanner(`${label} failed: ${error.message}`);
    });
  });
}

bindAction("run-checks", runSelfChecks);
bindAction("refresh-inventory", refreshInventory);
bindRefreshWithRenderer("refresh-skill-game", refreshSkillGame, renderSkillGameError, "Skill Game refresh");
bindRefreshWithRenderer("refresh-collaboration", refreshCollaboration, renderCollaborationError, "Collaboration refresh");
bindAction("refresh-readiness", refreshPublicReadiness);
bindAction("refresh-log", refreshAuditLog);
bindAction("plan-mitigation", planMitigationCase);
bindAction("accept-review", acceptSelectedReview);
bindAction("revoke-review", revokeSelectedReview);
bindAction("mitigate-quarantine", () => runMitigationAction("quarantine"));
bindAction("mitigate-strip", () => runMitigationAction("strip"));
bindAction("mitigate-request", () => runMitigationAction("request"));
bindAction("mitigate-rebuild", () => runMitigationAction("rebuild"));
bindAction("mitigate-blacklist", () => runMitigationAction("blacklist"));
bindAction("mitigate-remove", () => runMitigationAction("remove_or_refactor"));
bindAction("mitigate-repeat", () => runMitigationAction("repeat"));

bootstrap().catch((error) => setBanner(error.message));
