[CmdletBinding()]
param(
  [switch]$RestartExisting
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopRoot = Join-Path $repoRoot "apps\nullclaw-desktop"
$desktopScript = Join-Path $repoRoot "scripts\nullclaw_desktop.py"
$desktopLaunchScript = Join-Path $desktopRoot "electron\launchDesktop.cjs"
$desktopElectronPackage = Join-Path $desktopRoot "node_modules\electron\package.json"
$launcherScript = Join-Path $repoRoot "scripts\launch_security_console.vbs"
$wscriptPath = Join-Path $env:SystemRoot "System32\wscript.exe"
$node = Get-Command node.exe -ErrorAction SilentlyContinue
$healthUrl = "http://127.0.0.1:17665/v1/health"

function Set-SharedAgentLaneDefaults {
  $sharedBaseUrl = [string]$env:STARFRAME_SHARED_AGENT_BASE_URL
  if ([string]::IsNullOrWhiteSpace($sharedBaseUrl)) {
    $sharedBaseUrl = "http://127.0.0.1:9000/v1"
  }
  $sharedModel = [string]$env:STARFRAME_SHARED_AGENT_MODEL
  if ([string]::IsNullOrWhiteSpace($sharedModel)) {
    $sharedModel = "radeon-qwen3.5-4b"
  }

  $env:STARFRAME_SHARED_AGENT_BASE_URL = $sharedBaseUrl
  $env:STARFRAME_SHARED_AGENT_MODEL = $sharedModel
  $env:NULLCLAW_AGENT_BASE_URL = $sharedBaseUrl
  $env:NULLCLAW_AGENT_MODEL = $sharedModel
  $env:NULLCLAW_AGENT_ENABLE_LLM = "1"
  $env:MX3_LMSTUDIO_TOOL_MODEL = $sharedModel
}

Set-SharedAgentLaneDefaults

function Test-ElectronRuntimeReady {
  return (Test-Path $desktopLaunchScript) -and (Test-Path $desktopElectronPackage)
}

function Get-SecurityConsoleProcesses {
  $protected = Get-ProtectedProcessIds
  Get-CimInstance Win32_Process |
    Where-Object {
      if ($protected.ContainsKey([int]$_.ProcessId)) {
        return $false
      }
      $commandLine = [string]$_.CommandLine
      $executablePath = [string]$_.ExecutablePath
      (
        ($commandLine -and (
          $commandLine -like "*nullclaw_desktop.py*" -or
          $commandLine -like "*nullclaw_agent.py*" -or
          $commandLine -like "*skill_arbiter.agent_server*" -or
          $commandLine -like "*apps\nullclaw-desktop\electron\launchDesktop.cjs*" -or
          $commandLine -like "*apps\nullclaw-desktop*" -or
          $commandLine -like "*grtninja.SkillArbiterSecurityConsole*"
        ) -and (
          $commandLine -like "*$repoRoot*" -or
          $commandLine -like "*skill-arbiter*" -or
          $commandLine -like "*skill_arbiter*"
        )) -or
        ($executablePath -and (
          $executablePath -like "*$repoRoot*" -or
          $executablePath -like "*skill-arbiter\apps\nullclaw-desktop\node_modules\electron\dist\electron.exe"
        )) -or
        [string]$_.Name -ieq "SkillArbiterSecurityConsole.exe" -or
        [string]$_.ExecutablePath -like "*SkillArbiterSecurityConsole.exe"
      )
    }
}

function Get-ProtectedProcessIds {
  $rows = @{}
  $cursor = $PID
  while ($cursor -and -not $rows.ContainsKey($cursor)) {
    $rows[$cursor] = $true
    try {
      $proc = Get-CimInstance Win32_Process -Filter ("ProcessId = " + $cursor) -ErrorAction Stop
      $parentId = [int]$proc.ParentProcessId
    } catch {
      break
    }
    if (-not $parentId -or $parentId -eq $cursor) {
      break
    }
    $cursor = $parentId
  }
  return $rows
}

function Test-SecurityConsoleHealth {
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -TimeoutSec 4 -Uri $healthUrl
    return ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300)
  } catch {
    return $false
  }
}

function Stop-StaleSecurityConsoleProcesses {
  param([object[]]$Processes)

  foreach ($proc in @($Processes)) {
    try {
      Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
    } catch {
      Write-Warning ("failed to stop stale skill-arbiter process {0}: {1}" -f $proc.ProcessId, $_.Exception.Message)
    }
  }
}

if ($RestartExisting) {
  & (Join-Path $PSScriptRoot "stop_security_console.ps1")
}

$existingDesktop = Get-SecurityConsoleProcesses | Where-Object {
  ([string]$_.CommandLine -like "*nullclaw_desktop.py*") -or
  ([string]$_.ExecutablePath -like "*skill-arbiter\apps\nullclaw-desktop\node_modules\electron\dist\electron.exe") -or
  ([string]$_.Name -ieq "SkillArbiterSecurityConsole.exe")
}
if ($existingDesktop -and (Test-SecurityConsoleHealth)) {
  Write-Output "Skill Arbiter Security Console is already running."
  return
}
if ($existingDesktop) {
  Stop-StaleSecurityConsoleProcesses -Processes $existingDesktop
  Start-Sleep -Milliseconds 500
}

if (-not (Test-ElectronRuntimeReady)) {
  throw "Missing repo-local Electron runtime for Skill Arbiter. Run `npm install` in apps/nullclaw-desktop and retry this launcher."
}

if ((Test-Path $launcherScript) -and (Test-Path $wscriptPath)) {
  Start-Process -FilePath $wscriptPath -ArgumentList "`"$launcherScript`"" -WorkingDirectory $repoRoot -WindowStyle Hidden | Out-Null
} elseif ((Test-Path $desktopLaunchScript) -and $node) {
  Start-Process -FilePath $node.Source -ArgumentList "`"$desktopLaunchScript`"" -WorkingDirectory $desktopRoot -WindowStyle Hidden | Out-Null
} else {
  throw "A repo-local Electron launcher is required for Skill Arbiter startup. Ensure Node.js is installed and keep the hidden VBS launcher available."
}
Write-Output "Skill Arbiter Security Console launch requested."
