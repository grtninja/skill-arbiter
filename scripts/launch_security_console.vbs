Option Explicit

Const HIDDEN_WINDOW = 0

Dim shell, fso, repoRoot, desktopRoot, electronExe

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
shell.Environment("PROCESS")("ELECTRON_RUN_AS_NODE") = ""

repoRoot = fso.GetParentFolderName(WScript.ScriptFullName)
repoRoot = fso.GetParentFolderName(repoRoot)
desktopRoot = repoRoot & "\apps\nullclaw-desktop"
electronExe = desktopRoot & "\node_modules\electron\dist\SkillArbiterSecurityConsole.exe"

If Not fso.FileExists(electronExe) Then
  WScript.Quit 2
End If

shell.CurrentDirectory = desktopRoot
shell.Run """" & electronExe & """ .", HIDDEN_WINDOW, False
