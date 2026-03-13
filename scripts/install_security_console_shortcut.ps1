[CmdletBinding()]
param()

$repoRoot = Split-Path -Parent $PSScriptRoot
$launcherPath = Join-Path $repoRoot "scripts\launch_security_console.vbs"
$iconPath = Join-Path $repoRoot "apps\nullclaw-desktop\assets\skill_arbiter_ntm_v4.ico"
$shortcutName = "Skill Arbiter Security Console.lnk"
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) $shortcutName
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\grtninja"
$startMenuShortcut = Join-Path $startMenuDir $shortcutName

if (-not (Test-Path $iconPath)) {
  throw "missing icon asset: $iconPath"
}

if (-not (Test-Path $launcherPath)) {
  throw "missing launcher script: $launcherPath"
}

if (-not (Test-Path $startMenuDir)) {
  New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
}

$shell = New-Object -ComObject WScript.Shell
$targets = @($desktopShortcut, $startMenuShortcut)

foreach ($shortcutPath in $targets) {
  $shortcut = $shell.CreateShortcut($shortcutPath)
  $shortcut.TargetPath = "$env:SystemRoot\System32\wscript.exe"
  $shortcut.Arguments = "`"$launcherPath`""
  $shortcut.WorkingDirectory = $repoRoot
  $shortcut.IconLocation = $iconPath
  $shortcut.Description = "Launch Skill Arbiter Security Console"
  $shortcut.Save()
}

Write-Output ("Created shortcuts:`n- {0}`n- {1}" -f $desktopShortcut, $startMenuShortcut)
