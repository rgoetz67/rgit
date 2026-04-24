
REM set TARGET='C:\LemnaTec\Software\Programs\LemnaExperiment\startLemnaExperiment.bat'
REM set SHORTCUT='%HOMEDRIVE%%HOMEPATH%\Desktop\LemnaExperiment.lnk'
REM set ICON='C:\LemnaTec\Software\Programs\LemnaExperiment\LemnaExperiment.ico'
REM set PWS=powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile

REM %PWS% -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(%SHORTCUT%); $S.TargetPath = %TARGET%; $S.IconLocation = %ICON%; $S.Save()"


py -m venv rg
rg\Scripts\activate & rg\Scripts\python.exe -m pip install -r requirements.txt

