' Silent Windows launcher - no console window.
' Shortcut target: wscript.exe "%LOCALAPPDATA%\ScrapOptimisation\launcher\ScrapOptimisation.vbs"

Set shell = CreateObject("Wscript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
installDir = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))

nodeExe = installDir & "\node.exe"
launchScript = installDir & "\launcher\launch.mjs"

If Not fso.FileExists(nodeExe) Then
  nodeExe = "node.exe"
End If

shell.CurrentDirectory = installDir
shell.Environment("Process")("APP_ROOT") = installDir
shell.Run """" & nodeExe & """ """ & launchScript & """", 0, True