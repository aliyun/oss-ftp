Set oShell = CreateObject ("Wscript.Shell") 

strPath = Wscript.ScriptFullName
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objFile = objFSO.GetFile(strPath)
strFolder = objFSO.GetParentFolderName(objFile) 

Dim strArgs
quo = """"
strArgs = quo & strFolder & "/python27/win32/pythonw.exe" & quo & " " & quo & strFolder & "/launcher/start.py " & quo
oShell.Run strArgs, 0, false
