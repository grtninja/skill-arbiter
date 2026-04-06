const electronModule = require('electron');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
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
const ELECTRON_LOG = path.join(os.tmpdir(), 'skill-arbiter-electron.log');
const AGENT_SCRIPT = path.resolve(ROOT, 'scripts', 'nullclaw_agent.py');
const BACKEND_STDOUT_LOG = path.join(os.tmpdir(), 'skill-arbiter-backend.stdout.log');
const BACKEND_STDERR_LOG = path.join(os.tmpdir(), 'skill-arbiter-backend.stderr.log');

let mainWindow = null;
let revealTimer = null;
let ownedBackend = null;

function appendElectronLog(message) {
  const line = `[${new Date().toISOString()}] ${message}\n`;
  fs.appendFileSync(ELECTRON_LOG, line, 'utf8');
}

function healthUrl() {
  return `http://${AGENT_HOST}:${AGENT_PORT}/v1/ready`;
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

async function ensureBackend() {
  if (await isBackendHealthy()) {
    return;
  }
  const pythonwPath = resolvePythonwPath();
  if (!pythonwPath || !fs.existsSync(pythonwPath)) {
    throw new Error(`Pinned Skill Arbiter backend runtime missing: ${pythonwPath || 'unset'}`);
  }
  if (!fs.existsSync(AGENT_SCRIPT)) {
    throw new Error(`Skill Arbiter backend entrypoint missing: ${AGENT_SCRIPT}`);
  }
  appendElectronLog(`starting pinned backend runtime ${pythonwPath}`);
  const childEnv = { ...process.env };
  for (const key of ['PYTHONHOME', 'PYTHONPATH', 'PYTHONEXECUTABLE', 'VIRTUAL_ENV', 'UV_PYTHON']) {
    delete childEnv[key];
  }
  const stdoutFd = fs.openSync(BACKEND_STDOUT_LOG, 'a');
  const stderrFd = fs.openSync(BACKEND_STDERR_LOG, 'a');
  ownedBackend = spawn(
    pythonwPath,
    [AGENT_SCRIPT, '--host', AGENT_HOST, '--port', String(AGENT_PORT)],
    {
      cwd: ROOT,
      env: childEnv,
      detached: false,
      stdio: ['ignore', stdoutFd, stderrFd],
      windowsHide: true,
    },
  );
  ownedBackend.on('exit', (code, signal) => {
    appendElectronLog(`owned backend exited code=${code ?? 'null'} signal=${signal ?? 'null'}`);
    ownedBackend = null;
  });
  if (await waitForBackend(30000)) {
    appendElectronLog('backend became healthy after pinned spawn');
    return;
  }
  throw new Error('Skill Arbiter backend unavailable after pinned startup.');
}

function resolvePythonwPath() {
  const candidates = [];
  const envPinned = String(process.env.SKILL_ARBITER_PYTHONW || '').trim();
  if (envPinned) {
    candidates.push(envPinned);
  }
  const localAppData = process.env.LOCALAPPDATA || '';
  if (localAppData) {
    const pythonRoot = path.join(localAppData, 'Programs', 'Python');
    candidates.push(path.join(pythonRoot, 'Python313', 'pythonw.exe'));
    candidates.push(path.join(pythonRoot, 'Python312', 'pythonw.exe'));
    candidates.push(path.join(pythonRoot, 'Python311', 'pythonw.exe'));
    candidates.push(path.join(pythonRoot, 'Python310', 'pythonw.exe'));
  }
  candidates.push(path.join(ROOT, '.venv', 'Scripts', 'pythonw.exe'));

  for (const candidate of candidates) {
    const normalized = String(candidate || '').trim();
    if (normalized && fs.existsSync(normalized)) {
      return normalized;
    }
  }

  try {
    const lookedUp = spawnSync('where', ['pythonw.exe'], {
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'ignore'],
      shell: false,
      timeout: 1500,
    });
    if (lookedUp.status === 0 && lookedUp.stdout) {
      const first = String(lookedUp.stdout).split(/\r?\n/).map((line) => line.trim()).find(Boolean);
      if (first && fs.existsSync(first)) {
        return first;
      }
    }
  } catch {
    // Keep startup deterministic: fall through to missing-runtime error.
  }

  return envPinned || '';
}

function showStartupFailure(message) {
  appendElectronLog(`startup failure: ${message}`);
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
  appendElectronLog('createWindow called');
  const revealWindow = () => {
    if (!mainWindow || mainWindow.isDestroyed()) {
      appendElectronLog('revealWindow skipped: no mainWindow');
      return;
    }
    if (revealTimer) {
      clearTimeout(revealTimer);
      revealTimer = null;
    }
    if (!mainWindow.isVisible()) {
      appendElectronLog('revealWindow show()');
      mainWindow.show();
    }
    appendElectronLog('revealWindow focus()');
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
    appendElectronLog('ready-to-show');
    revealWindow();
  });
  mainWindow.webContents.once('did-finish-load', () => {
    appendElectronLog('did-finish-load');
    revealWindow();
  });
  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription) => {
    appendElectronLog(`did-fail-load ${errorCode} ${errorDescription}`);
    process.stderr.write(`[${APP_TITLE}] window load failed: ${errorCode} ${errorDescription}\n`);
    revealWindow();
  });
  mainWindow.webContents.on('render-process-gone', (_event, details) => {
    appendElectronLog(`render-process-gone reason=${details?.reason || 'unknown'} exitCode=${details?.exitCode ?? 'null'}`);
  });
  mainWindow.webContents.on('unresponsive', () => {
    appendElectronLog('webContents unresponsive');
  });
  mainWindow.on('closed', () => {
    appendElectronLog('window closed');
    if (revealTimer) {
      clearTimeout(revealTimer);
      revealTimer = null;
    }
    mainWindow = null;
  });
  mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  revealTimer = setTimeout(() => {
    appendElectronLog('reveal timer fired');
    revealWindow();
  }, 3000);
  appendElectronLog(`loading UI ${UI_INDEX}`);
  void mainWindow.loadURL(pathToFileURL(UI_INDEX).toString());
}

async function main() {
  appendElectronLog('main start');
  app.setName(APP_TITLE);
  if (process.platform === 'win32') {
    app.setAppUserModelId(APP_ID);
  }
  await app.whenReady();
  appendElectronLog('app ready');
  createWindow();
  void ensureBackend()
    .then(() => {
      appendElectronLog('backend ensured');
    })
    .catch((error) => {
      process.stderr.write(`[${APP_TITLE}] ${error.message}\n`);
      showStartupFailure(error.message);
      app.exit(1);
    });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
      void ensureBackend().then(() => {
        appendElectronLog('activate ensureBackend resolved');
      }).catch((error) => {
        appendElectronLog(`activate ensureBackend failed: ${error.message}`);
        process.stderr.write(`[${APP_TITLE}] ${error.message}\n`);
      });
    }
  });
}

app.on('window-all-closed', () => {
  appendElectronLog('window-all-closed');
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  appendElectronLog('will-quit');
  if (ownedBackend && !ownedBackend.killed) {
    try {
      process.kill(ownedBackend.pid);
    } catch {
      // best effort
    }
  }
});

main().catch((error) => {
  process.stderr.write(`[${APP_TITLE}] ${error.message}\n`);
  showStartupFailure(error.message);
  app.exit(1);
});
