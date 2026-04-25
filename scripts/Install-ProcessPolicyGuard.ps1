[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$TaskName = "SkillArbiter-ProcessPolicyGuard",
  [double]$IntervalSeconds = 2.0,
  [switch]$RunNow
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
  $RepoRoot = Split-Path -Parent $PSScriptRoot
}

function Resolve-Python {
  $candidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "python.exe"
  )
  foreach ($candidate in $candidates) {
    $resolved = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($resolved) {
      return $resolved.Source
    }
  }
  throw "Unable to resolve python.exe for Skill Arbiter process guard."
}

$repo = Resolve-Path -LiteralPath $RepoRoot
$python = Resolve-Python
$script = Join-Path $repo "scripts\process_policy_guard.py"
$stateRoot = Join-Path $env:LOCALAPPDATA "SkillArbiterNullClaw"
$logDir = Join-Path $stateRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$jsonOut = Join-Path $logDir "process-policy-guard-status.json"

$actionArgs = @(
  "-NoProfile",
  "-ExecutionPolicy", "Bypass",
  "-WindowStyle", "Hidden",
  "-Command",
  "& `"$python`" `"$script`" --interval-seconds $IntervalSeconds --json-out `"$jsonOut`""
) -join " "

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settingsArgs = @{
  AllowStartIfOnBatteries = $true
  ExecutionTimeLimit = [TimeSpan]::Zero
  MultipleInstances = "IgnoreNew"
}
if ((Get-Command New-ScheduledTaskSettingsSet).Parameters.ContainsKey("DisallowStartIfOnBatteries")) {
  $settingsArgs["DisallowStartIfOnBatteries"] = $false
}
$settings = New-ScheduledTaskSettingsSet @settingsArgs
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

if ($RunNow) {
  Start-ScheduledTask -TaskName $TaskName
  Start-Sleep -Seconds 2
}

[pscustomobject]@{
  task_name = $TaskName
  repo_root = $repo.Path
  python = $python
  script = $script
  json_out = $jsonOut
  run_now = [bool]$RunNow
} | ConvertTo-Json -Depth 4
