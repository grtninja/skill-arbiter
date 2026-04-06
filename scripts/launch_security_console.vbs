Option Explicit

Const HIDDEN_WINDOW = 0

Dim shell, fso, repoRoot, launcherScript, pythonwExe, processClass, startupConfig, processId, result

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repoRoot = fso.GetParentFolderName(WScript.ScriptFullName)
repoRoot = fso.GetParentFolderName(repoRoot)
launcherScript = repoRoot & "\scripts\nullclaw_desktop.py"
pythonwExe = ResolvePythonw(shell, fso, repoRoot)

If Not fso.FileExists(launcherScript) Then
  WScript.Quit 2
End If

If Len(pythonwExe) = 0 Then
  WScript.Quit 3
End If

Set processClass = GetObject("winmgmts:root\cimv2:Win32_Process")
Set startupConfig = GetObject("winmgmts:root\cimv2:Win32_ProcessStartup").SpawnInstance_
startupConfig.ShowWindow = HIDDEN_WINDOW

result = processClass.Create("""" & pythonwExe & """ """ & launcherScript & """ --spawn-electron-hidden", repoRoot, startupConfig, processId)
If result <> 0 Then
  WScript.Quit result
End If

Function ResolvePythonw(shellObj, fsoObj, repoRootPath)
  Dim localAppData, candidates, candidate
  localAppData = shellObj.ExpandEnvironmentStrings("%LOCALAPPDATA%")
  candidates = Array( _
    localAppData & "\Programs\Python\Python313\pythonw.exe", _
    localAppData & "\Programs\Python\Python312\pythonw.exe", _
    localAppData & "\Programs\Python\Python311\pythonw.exe", _
    localAppData & "\Programs\Python\Python310\pythonw.exe", _
    repoRootPath & "\.venv\Scripts\pythonw.exe" _
  )
  For Each candidate In candidates
    If fsoObj.FileExists(candidate) Then
      ResolvePythonw = candidate
      Exit Function
    End If
  Next
  ResolvePythonw = ""
End Function
