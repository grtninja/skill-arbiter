[CmdletBinding()]
param()

$matches = Get-CimInstance Win32_Process |
  Where-Object {
    $_.CommandLine -and (
      $_.CommandLine -like "*nullclaw_desktop.py*" -or
      $_.CommandLine -like "*nullclaw_agent.py*"
    ) -and $_.CommandLine -like "*skill-arbiter*"
  }

if (-not $matches) {
  Write-Output "Skill Arbiter Security Console is not running."
  exit 0
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
