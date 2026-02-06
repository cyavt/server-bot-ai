@echo off
chcp 65001 >nul
echo ========================================
echo    Backup Docker Data Script
echo ========================================
echo.

REM Tạo thư mục backup với timestamp
set "BACKUP_DIR=backups"
set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_PATH=%BACKUP_DIR%\backup_%TIMESTAMP%"

echo Đang tạo thư mục backup: %BACKUP_PATH%
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%BACKUP_PATH%" mkdir "%BACKUP_PATH%"

echo.
echo [1/5] Đang backup thư mục data...
if exist "data" (
    xcopy /E /I /Y "data" "%BACKUP_PATH%\data\" >nul
    echo ✓ Đã backup data
) else (
    echo ⚠ Thư mục data không tồn tại
)

echo.
echo [2/5] Đang backup thư mục models...
if exist "models" (
    xcopy /E /I /Y "models" "%BACKUP_PATH%\models\" >nul
    echo ✓ Đã backup models
) else (
    echo ⚠ Thư mục models không tồn tại
)

echo.
echo [3/5] Đang backup thư mục uploadfile...
if exist "uploadfile" (
    xcopy /E /I /Y "uploadfile" "%BACKUP_PATH%\uploadfile\" >nul
    echo ✓ Đã backup uploadfile
) else (
    echo ⚠ Thư mục uploadfile không tồn tại
)

echo.
echo [4/5] Đang backup MySQL data...
if exist "mysql\data" (
    xcopy /E /I /Y "mysql\data" "%BACKUP_PATH%\mysql_data\" >nul
    echo ✓ Đã backup MySQL data
) else (
    echo ⚠ Thư mục mysql\data không tồn tại
)

echo.
echo [5/5] Đang backup docker-compose files...
copy /Y "docker-compose.yml" "%BACKUP_PATH%\docker-compose.yml" >nul 2>&1
copy /Y "docker-compose_all.yml" "%BACKUP_PATH%\docker-compose_all.yml" >nul 2>&1
copy /Y "docker-compose_dev.yml" "%BACKUP_PATH%\docker-compose_dev.yml" >nul 2>&1
copy /Y "docker-compose_hotreload.yml" "%BACKUP_PATH%\docker-compose_hotreload.yml" >nul 2>&1
echo ✓ Đã backup docker-compose files

echo.
echo ========================================
echo    Backup hoàn tất!
echo ========================================
echo Backup được lưu tại: %BACKUP_PATH%
echo.
echo Để restore, chạy: restore.bat
echo.
pause
