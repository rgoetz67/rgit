
set "var=%string1%%string2%%string3%"

set "TARGET='%~dp0%rgit.bat'"
set SHORTCUT='%HOMEDRIVE%%HOMEPATH%\Desktop\RGit.lnk'
set "ICON='%~dp0%icons\rgit.ico'"
set PWS=powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile

%PWS% -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(%SHORTCUT%); $S.TargetPath = %TARGET%; $S.IconLocation = %ICON%; $S.Save()"


py -m venv rg
rg\Scripts\activate & rg\Scripts\python.exe -m pip install -r requirements.txt

