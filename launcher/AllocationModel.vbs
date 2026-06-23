' Silent Windows launcher — no console window.
' Desktop shortcut target: wscript.exe "C:\Program Files\AllocationModel\launcher\AllocationModel.vbs"

Set shell = CreateObject("Wscript.Shell")
installDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(
  CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
)

nodeExe = installDir & "\node.exe"
launchScript = installDir & "\launcher\launch.mjs"

If Not CreateObject("Scripting.FileSystemObject").FileExists(nodeExe) Then
  nodeExe = "node.exe"
End If

shell.CurrentDirectory = installDir
shell.Environment("Process")("APP_ROOT") = installDir
shell.Run """" & nodeExe & """ """ & launchScript & """", 0, True
