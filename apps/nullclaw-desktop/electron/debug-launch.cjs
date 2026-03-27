const { app, BrowserWindow } = require('electron');
const path = require('node:path');
app.whenReady().then(() => {
  const win = new BrowserWindow({ width: 1400, height: 900, webPreferences: { contextIsolation: true, sandbox: true, devTools: true, backgroundThrottling: false } });
  win.webContents.on('console-message', (_e, level, message, line, sourceId) => console.log('console', JSON.stringify({ level, message, line, sourceId })));
  win.webContents.on('render-process-gone', (_e, details) => console.log('render-process-gone', JSON.stringify(details)));
  win.webContents.on('unresponsive', () => console.log('renderer-unresponsive'));
  win.webContents.on('did-fail-load', (_e, code, desc) => console.log('did-fail-load', code, desc));
  win.webContents.on('did-finish-load', () => console.log('did-finish-load'));
  win.loadURL('file:///' + path.join(__dirname, '..', 'ui', 'index.html').replace(/\\/g,'/'));
});
