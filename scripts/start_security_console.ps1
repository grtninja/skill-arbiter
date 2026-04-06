[CmdletBinding()]
param()

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopRoot = Join-Path $repoRoot "apps\nullclaw-desktop"
$launcherHelper = Join-Path $PSScriptRoot "nullclaw_desktop.py"
$launcherScript = Join-Path $PSScriptRoot "launch_security_console.vbs"
$wscriptExe = Join-Path $env:SystemRoot "System32\wscript.exe"

if (-not (Test-Path $launcherHelper)) {
  throw "Missing launcher helper: $launcherHelper"
}
if (-not (Test-Path $launcherScript)) {
  throw "Missing launcher script: $launcherScript"
}
if (-not (Test-Path $wscriptExe)) {
  throw "Missing Windows Script Host executable: $wscriptExe"
}

Start-Process -FilePath $wscriptExe -ArgumentList @("//B", "//Nologo", $launcherScript) -WorkingDirectory $desktopRoot | Out-Null
Write-Output "Skill Arbiter Security Console developer-shell launch requested. Canonical no-shell launch surfaces are launch_security_console.vbs and the installed shortcuts."
