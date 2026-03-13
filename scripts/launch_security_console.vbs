Option Explicit

Dim shell, fso, repoRoot, pythonw, desktopScript, command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repoRoot = fso.GetParentFolderName(WScript.ScriptFullName)
repoRoot = fso.GetParentFolderName(repoRoot)

pythonw = shell.ExpandEnvironmentStrings("%LocalAppData%") & "\Programs\Python\Python313\pythonw.exe"
desktopScript = repoRoot & "\scripts\nullclaw_desktop.py"

If Not fso.FileExists(pythonw) Then
  pythonw = "pythonw.exe"
End If

command = """" & pythonw & """ """ & desktopScript & """"
shell.Run command, 0, False
