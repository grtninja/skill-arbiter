const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');

const WINDOWS_PROCESS_EXE_NAME = 'SkillArbiterSecurityConsole.exe';

function resolveElectronBinary() {
  const electronBinary = require('electron');
  if (typeof electronBinary !== 'string') {
    throw new Error('Unable to resolve Electron binary path.');
  }
  return electronBinary;
}

function ensureNamedWindowsBinary(electronBinary) {
  if (process.platform !== 'win32') {
    return electronBinary;
  }
  const namedBinary = path.join(path.dirname(electronBinary), WINDOWS_PROCESS_EXE_NAME);
  try {
    const sourceStat = fs.statSync(electronBinary);
    const targetStat = fs.existsSync(namedBinary) ? fs.statSync(namedBinary) : null;
    if (targetStat && targetStat.size === sourceStat.size && targetStat.mtimeMs >= sourceStat.mtimeMs) {
      return namedBinary;
    }
  } catch {
    // Recreate the alias below.
  }
  try {
    if (fs.existsSync(namedBinary)) {
      fs.unlinkSync(namedBinary);
    }
    fs.linkSync(electronBinary, namedBinary);
    return namedBinary;
  } catch {
    fs.copyFileSync(electronBinary, namedBinary);
    return namedBinary;
  }
}

function main(argv) {
  const desktopRoot = path.resolve(__dirname, '..');
  const electronBinary = ensureNamedWindowsBinary(resolveElectronBinary());
  if (argv.includes('--print-binary')) {
    process.stdout.write(`${electronBinary}\n`);
    return 0;
  }

  const env = { ...process.env };
  delete env.ELECTRON_RUN_AS_NODE;
  const child = spawn(electronBinary, ['.'], {
    cwd: desktopRoot,
    env,
    detached: true,
    stdio: 'ignore',
    windowsHide: true,
  });
  child.unref();
  return 0;
}

if (require.main === module) {
  try {
    process.exitCode = main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`[Skill Arbiter Security Console] ${error.message}\n`);
    process.exitCode = 1;
  }
}
