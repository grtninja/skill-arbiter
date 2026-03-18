[CmdletBinding()]
param()

$repoRoot = Split-Path -Parent $PSScriptRoot

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

$protected = Get-ProtectedProcessIds
$matches = Get-CimInstance Win32_Process |
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

if (-not $matches) {
  Write-Output "Skill Arbiter Security Console is not running."
  return
}

foreach ($proc in $matches) {
  try {
    Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
    Write-Output ("Stopped process {0}" -f $proc.ProcessId)
  } catch {
    Write-Warning ("failed to stop process {0}: {1}" -f $proc.ProcessId, $_.Exception.Message)
  }
}

Start-Sleep -Milliseconds 500
