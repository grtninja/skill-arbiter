Option Explicit

Dim shell, fso, repoRoot, desktopRoot, nodeExe, launchScript, command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repoRoot = fso.GetParentFolderName(WScript.ScriptFullName)
repoRoot = fso.GetParentFolderName(repoRoot)
desktopRoot = repoRoot & "\apps\nullclaw-desktop"
launchScript = desktopRoot & "\electron\launchDesktop.cjs"

nodeExe = shell.ExpandEnvironmentStrings("%ProgramFiles%") & "\nodejs\node.exe"
If Not fso.FileExists(nodeExe) Then
  nodeExe = shell.ExpandEnvironmentStrings("%LocalAppData%") & "\Programs\nodejs\node.exe"
End If
If Not fso.FileExists(nodeExe) Then
  nodeExe = "node.exe"
End If

shell.CurrentDirectory = desktopRoot
command = """" & nodeExe & """ """ & launchScript & """"
shell.Run command, 0, False
