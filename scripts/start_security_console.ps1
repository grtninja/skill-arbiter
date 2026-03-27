[CmdletBinding()]
param()

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopRoot = Join-Path $repoRoot "apps\nullclaw-desktop"
$electronExe = Join-Path $desktopRoot "node_modules\electron\dist\SkillArbiterSecurityConsole.exe"
$launcherScript = Join-Path $PSScriptRoot "launch_security_console.vbs"
$wscriptExe = Join-Path $env:SystemRoot "System32\wscript.exe"

if (-not (Test-Path $electronExe)) {
  throw "Missing repo-local Electron binary: $electronExe"
}
if (-not (Test-Path $launcherScript)) {
  throw "Missing launcher script: $launcherScript"
}
if (-not (Test-Path $wscriptExe)) {
  throw "Missing Windows Script Host executable: $wscriptExe"
}

$env:ELECTRON_RUN_AS_NODE = ""
Start-Process -FilePath $wscriptExe -ArgumentList @("//B", "//Nologo", $launcherScript) -WorkingDirectory $desktopRoot | Out-Null
Write-Output "Skill Arbiter Security Console launch requested."
