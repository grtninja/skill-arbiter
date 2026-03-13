[CmdletBinding()]
param(
  [switch]$RestartExisting
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopScript = Join-Path $repoRoot "scripts\nullclaw_desktop.py"
$python = (Get-Command pythonw.exe -ErrorAction SilentlyContinue)
if (-not $python) {
  $python = Get-Command python.exe -ErrorAction Stop
}

function Get-SecurityConsoleProcesses {
  Get-CimInstance Win32_Process |
    Where-Object {
      $_.CommandLine -and (
        $_.CommandLine -like "*nullclaw_desktop.py*" -or
        $_.CommandLine -like "*nullclaw_agent.py*"
      ) -and $_.CommandLine -like "*skill-arbiter*"
    }
}

if ($RestartExisting) {
  & (Join-Path $PSScriptRoot "stop_security_console.ps1")
}

$existingDesktop = Get-SecurityConsoleProcesses | Where-Object { $_.CommandLine -like "*nullclaw_desktop.py*" }
if ($existingDesktop) {
  Write-Output "Skill Arbiter Security Console is already running."
  exit 0
}

Start-Process -FilePath $python.Source -ArgumentList "`"$desktopScript`"" -WorkingDirectory $repoRoot | Out-Null
Write-Output "Skill Arbiter Security Console launch requested."
