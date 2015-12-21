
function CreateShortcut()
{
   wsh = new ActiveXObject('WScript.Shell');
   target_path = '"' + wsh.CurrentDirectory + '\\..\\python27\\win32\\pythonw.exe"';
   icon_path = wsh.CurrentDirectory + '\\web_ui\\favicon.ico';


   link = wsh.CreateShortcut(wsh.SpecialFolders("Desktop") + '\\OSS-FTP.lnk');
   link.TargetPath = target_path;
   link.Arguments = '"' + wsh.CurrentDirectory + '\\start.py"';
   link.WindowStyle = 7;
   link.IconLocation = icon_path;
   link.Description = 'OSS-FTP';
   link.WorkingDirectory = wsh.CurrentDirectory;
   link.Save();
}


function main(){
    CreateShortcut();
}
main();
