@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "BIN_DIR=%USERPROFILE%\.bin"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
> "%BIN_DIR%\ask.bat" echo @python "%SCRIPT_DIR%app.py" %%*

echo Ask betigi %BIN_DIR% klasorune kuruldu.
echo PATH degiskeninde %BIN_DIR% dizini kontrol ediliyor...
rem Only the user PATH is read and updated. "setx PATH %PATH%" would copy the
rem system PATH into the user PATH and truncate it to 1024 characters.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$bin = $env:BIN_DIR; $p = [Environment]::GetEnvironmentVariable('Path', 'User'); $parts = @(\"$p\" -split ';' | Where-Object { $_ }); if ($parts -contains $bin) { exit 0 }; [Environment]::SetEnvironmentVariable('Path', (($parts + $bin) -join ';'), 'User'); exit 2"
if errorlevel 2 (
    echo %BIN_DIR% PATH degiskenine eklendi. Degisikliklerin etkili olmasi icin yeni oturum acin.
) else if errorlevel 1 (
    echo PATH guncellenemedi. %BIN_DIR% dizinini PATH'e elle ekleyin.
) else (
    echo %BIN_DIR% zaten PATH degiskeninde bulunuyor.
)
endlocal
