@echo off
setlocal
set SCRIPT_DIR=%~dp0
set BIN_DIR=%USERPROFILE%\.bin
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
> "%BIN_DIR%\ask.bat" echo @python "%SCRIPT_DIR%app.py" %%*

echo Ask betigi %BIN_DIR% klasorune kuruldu.
echo PATH degiskeninde %BIN_DIR% dizini kontrol ediliyor...
echo %PATH% | find /I "%BIN_DIR%" >nul
if errorlevel 1 (
    setx PATH "%PATH%;%BIN_DIR%" >nul
    echo %BIN_DIR% PATH degiskenine eklendi. Degisikliklerin etkili olmasi icin yeni oturum acin.
) else (
    echo %BIN_DIR% zaten PATH degiskeninde bulunuyor.
)
endlocal
