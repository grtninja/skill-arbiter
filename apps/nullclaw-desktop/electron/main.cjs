const electronModule = require('electron');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const ROOT = path.resolve(__dirname, '..', '..', '..');

let app;
let BrowserWindow;

if (typeof electronModule === 'string') {
  if (process.env.SKILL_ARBITER_ELECTRON_BOOTSTRAPPED) {
    throw new Error('Electron main process unavailable after bootstrap.');
  }
  const env = { ...process.env, SKILL_ARBITER_ELECTRON_BOOTSTRAPPED: '1' };
  delete env.ELECTRON_RUN_AS_NODE;
  const spawnBinary =
    /SkillArbiterSecurityConsole\.exe$/i.test(String(process.execPath || ''))
      ? process.execPath
      : electronModule;
  const child = spawn(spawnBinary, process.argv.slice(1), {
    stdio: 'ignore',
    env,
    detached: true,
    windowsHide: true,
  });
  child.unref();
  process.exit(0);
  return;
}

({ app, BrowserWindow } = electronModule);

const APP_TITLE = 'Skill Arbiter Security Console';
const APP_ID = 'grtninja.SkillArbiterSecurityConsole';
const AGENT_HOST = process.env.SKILL_ARBITER_AGENT_HOST || '127.0.0.1';
const AGENT_PORT = Number.parseInt(process.env.SKILL_ARBITER_AGENT_PORT || '17665', 10);
const UI_INDEX = path.resolve(__dirname, '..', 'ui', 'index.html');
const ICON_PATH = path.resolve(__dirname, '..', 'assets', 'skill_arbiter_ntm_v4.ico');
const AGENT_SCRIPT = path.resolve(ROOT, 'scripts', 'nullclaw_agent.py');
const BACKEND_STDOUT_LOG = path.join(os.tmpdir(), 'skill-arbiter-backend.stdout.log');
const BACKEND_STDERR_LOG = path.join(os.tmpdir(), 'skill-arbiter-backend.stderr.log');

let mainWindow = null;
let ownedBackend = null;
let revealTimer = null;

function candidatePaths() {
  const localAppData = process.env.LOCALAPPDATA || '';
  return [
    process.env.SKILL_ARBITER_PYTHON || '',
    path.join(ROOT, '.venv', 'Scripts', 'python.exe'),
    path.join(localAppData, 'Programs', 'Python', 'Python313', 'python.exe'),
    path.join(localAppData, 'Programs', 'Python', 'Python312', 'python.exe'),
    path.join(localAppData, 'Programs', 'Python', 'Python311', 'python.exe'),
    'python.exe',
  ].filter(Boolean);
}

function resolvePythonExecutables() {
  const seen = new Set();
  const candidates = [];
  for (const candidate of candidatePaths()) {
    if (candidate.includes(path.sep) && !fs.existsSync(candidate)) {
      continue;
    }
    if (seen.has(candidate)) {
      continue;
    }
    seen.add(candidate);
    candidates.push(candidate);
  }
  if (candidates.length > 0) {
    return candidates;
  }
  throw new Error('Unable to resolve a Python interpreter for Skill Arbiter.');
}

function healthUrl() {
  return `http://${AGENT_HOST}:${AGENT_PORT}/v1/health`;
}

function requestJson(url, timeoutMs = 1500) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout: timeoutMs }, (response) => {
      const chunks = [];
      response.on('data', (chunk) => chunks.push(chunk));
      response.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf8');
        if (response.statusCode !== 200) {
          reject(new Error(`status ${response.statusCode}`));
          return;
        }
        try {
          resolve(JSON.parse(body));
        } catch (error) {
          reject(error);
        }
      });
    });
    req.on('timeout', () => req.destroy(new Error('timeout')));
    req.on('error', reject);
  });
}

async function isBackendHealthy() {
  try {
    await requestJson(healthUrl(), 1500);
    return true;
  } catch {
    return false;
  }
}

async function waitForBackend(timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await isBackendHealthy()) {
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
  return false;
}

function appendBackendLog(message) {
  const line = `[${new Date().toISOString()}] ${message}\n`;
  fs.appendFileSync(BACKEND_STDERR_LOG, line, 'utf8');
}

function resetBackendLogs() {
  for (const filePath of [BACKEND_STDOUT_LOG, BACKEND_STDERR_LOG]) {
    try {
      fs.unlinkSync(filePath);
    } catch {
      // Ignore missing prior logs.
    }
  }
}

function stopBackendProcess(child) {
  if (!child || child.killed) {
    return;
  }
  try {
    process.kill(child.pid);
  } catch {
    // Best effort on failed child recycle.
  }
}

function spawnBackendForCandidate(pythonExe) {
  const stdoutFd = fs.openSync(BACKEND_STDOUT_LOG, 'a');
  const stderrFd = fs.openSync(BACKEND_STDERR_LOG, 'a');
  const childEnv = { ...process.env };
  for (const key of ['PYTHONHOME', 'PYTHONPATH', 'PYTHONEXECUTABLE', 'VIRTUAL_ENV', 'UV_PYTHON']) {
    delete childEnv[key];
  }
  const child = spawn(
    pythonExe,
    [AGENT_SCRIPT, '--host', AGENT_HOST, '--port', String(AGENT_PORT)],
    {
      cwd: ROOT,
      detached: false,
      env: childEnv,
      stdio: ['ignore', stdoutFd, stderrFd],
      windowsHide: true,
    }
  );
  child.on('error', (error) => {
    appendBackendLog(`spawn error for ${pythonExe}: ${error.message}`);
  });
  child.on('exit', (code, signal) => {
    appendBackendLog(`backend exit for ${pythonExe}: code=${code ?? 'null'} signal=${signal ?? 'null'}`);
  });
  return child;
}

async function ensureBackend() {
  if (await isBackendHealthy()) {
    return;
  }
  resetBackendLogs();
  const candidates = resolvePythonExecutables();
  appendBackendLog(`backend candidates=${JSON.stringify(candidates)}`);
  for (const pythonExe of candidates) {
    appendBackendLog(`trying backend candidate=${pythonExe}`);
    ownedBackend = spawnBackendForCandidate(pythonExe);
    if (await waitForBackend(7000)) {
      appendBackendLog(`backend healthy on candidate=${pythonExe}`);
      return;
    }
    stopBackendProcess(ownedBackend);
    ownedBackend = null;
  }
  throw new Error(
    `Skill Arbiter backend failed to become healthy. See ${BACKEND_STDERR_LOG}`
  );
}

function showStartupFailure(message) {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }
  const escaped = JSON.stringify(String(message));
  void mainWindow.webContents.executeJavaScript(
    `document.body.innerHTML = '<pre style="white-space:pre-wrap;font:14px Consolas,monospace;padding:24px;color:#f5d8d8;background:#16090b;min-height:100vh;margin:0">' + ${escaped} + '</pre>';`,
    true
  );
}

function createWindow() {
  const revealWindow = () => {
    if (!mainWindow || mainWindow.isDestroyed()) {
      return;
    }
    if (revealTimer) {
      clearTimeout(revealTimer);
      revealTimer = null;
    }
    if (!mainWindow.isVisible()) {
      mainWindow.show();
    }
    mainWindow.focus();
  };

  mainWindow = new BrowserWindow({
    width: 1380,
    height: 920,
    minWidth: 1120,
    minHeight: 760,
    show: false,
    backgroundColor: '#08101A',
    title: APP_TITLE,
    autoHideMenuBar: true,
    icon: fs.existsSync(ICON_PATH) ? ICON_PATH : undefined,
    webPreferences: {
      contextIsolation: true,
      sandbox: true,
      devTools: false,
      backgroundThrottling: false,
    },
  });
  mainWindow.once('ready-to-show', () => {
    revealWindow();
  });
  mainWindow.webContents.once('did-finish-load', () => {
    revealWindow();
  });
  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription) => {
    process.stderr.write(`[${APP_TITLE}] window load failed: ${errorCode} ${errorDescription}\n`);
    revealWindow();
  });
  mainWindow.on('closed', () => {
    if (revealTimer) {
      clearTimeout(revealTimer);
      revealTimer = null;
    }
    mainWindow = null;
  });
  mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  revealTimer = setTimeout(() => {
    revealWindow();
  }, 3000);
  void mainWindow.loadURL(pathToFileURL(UI_INDEX).toString());
}

function stopOwnedBackend() {
  if (!ownedBackend || ownedBackend.killed) {
    return;
  }
  try {
    process.kill(ownedBackend.pid);
  } catch {
    // Best effort on shutdown.
  }
}

async function main() {
  app.setName(APP_TITLE);
  if (process.platform === 'win32') {
    app.setAppUserModelId(APP_ID);
  }
  await app.whenReady();
  createWindow();
  await ensureBackend();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  stopOwnedBackend();
});

main().catch((error) => {
  process.stderr.write(`[${APP_TITLE}] ${error.message}\n`);
  showStartupFailure(error.message);
  stopOwnedBackend();
  app.exit(1);
});
