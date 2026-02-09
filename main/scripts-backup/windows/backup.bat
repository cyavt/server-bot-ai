@echo off
chcp 65001 >nul
REM Script backup tổng hợp: Database + File System
REM Usage: backup.bat [backup_directory]

setlocal enabledelayedexpansion

set BACKUP_DIR=%~1
if "%BACKUP_DIR%"=="" set BACKUP_DIR=%~dp0..\backups

REM Tạo timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
set BACKUP_PATH=%BACKUP_DIR%\backup_%TIMESTAMP%

REM Chuyển về thư mục xiaozhi-server để backup files
cd /d "%~dp0\..\xiaozhi-server"

echo ========================================
echo    Backup Tổng Hợp: Database + Files
echo ========================================
echo.
echo Đang tạo thư mục backup: %BACKUP_PATH%
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%BACKUP_PATH%" mkdir "%BACKUP_PATH%"
if not exist "%BACKUP_PATH%\database" mkdir "%BACKUP_PATH%\database"
if not exist "%BACKUP_PATH%\files" mkdir "%BACKUP_PATH%\files"

echo.
echo ========================================
echo [PHẦN 1/2] Backup Database
echo ========================================

set DB_NAME=xiaozhi_esp32_server
set DB_USER=root
set DB_PASSWORD=123456
set DB_CONTAINER=xiaozhi-esp32-server-db
set DB_BACKUP_FILE=%BACKUP_PATH%\database\xiaozhi_db_backup_%TIMESTAMP%.sql

echo Đang backup database: %DB_NAME%
docker exec %DB_CONTAINER% mysqldump -u%DB_USER% -p%DB_PASSWORD% --single-transaction --routines --triggers --events --hex-blob --default-character-set=utf8mb4 %DB_NAME% > "%DB_BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo ✓ Backup database thành công!
    echo   File: %DB_BACKUP_FILE%
    
    REM Nén file database backup (nếu có 7zip)
    REM 7z a "%DB_BACKUP_FILE%.gz" "%DB_BACKUP_FILE%" >nul 2>&1
    REM if %ERRORLEVEL% EQU 0 del "%DB_BACKUP_FILE%"
) else (
    echo ✗ Backup database thất bại!
    echo   Kiểm tra container %DB_CONTAINER% có đang chạy không
)

echo.
echo ========================================
echo [PHẦN 2/2] Backup File System
echo ========================================

echo [1/5] Đang backup thư mục data...
if exist "data" (
    xcopy /E /I /Y "data" "%BACKUP_PATH%\files\data\" >nul
    echo ✓ Đã backup data
) else (
    echo ⚠ Thư mục data không tồn tại
)

echo [2/5] Đang backup thư mục models...
if exist "models" (
    xcopy /E /I /Y "models" "%BACKUP_PATH%\files\models\" >nul
    echo ✓ Đã backup models
) else (
    echo ⚠ Thư mục models không tồn tại
)

echo [3/5] Đang backup thư mục uploadfile...
if exist "uploadfile" (
    xcopy /E /I /Y "uploadfile" "%BACKUP_PATH%\files\uploadfile\" >nul
    echo ✓ Đã backup uploadfile
) else (
    echo ⚠ Thư mục uploadfile không tồn tại
)

echo [4/5] Đang backup MySQL data files...
if exist "mysql\data" (
    xcopy /E /I /Y "mysql\data" "%BACKUP_PATH%\files\mysql_data\" >nul
    echo ✓ Đã backup MySQL data files
) else (
    echo ⚠ Thư mục mysql\data không tồn tại
)

echo [5/5] Đang backup docker-compose files...
copy /Y "docker-compose.yml" "%BACKUP_PATH%\files\docker-compose.yml" >nul 2>&1
copy /Y "docker-compose_all.yml" "%BACKUP_PATH%\files\docker-compose_all.yml" >nul 2>&1
copy /Y "docker-compose-dev.yml" "%BACKUP_PATH%\files\docker-compose-dev.yml" >nul 2>&1
copy /Y "docker-compose_hotreload.yml" "%BACKUP_PATH%\files\docker-compose_hotreload.yml" >nul 2>&1
echo ✓ Đã backup docker-compose files

echo.
echo ========================================
echo    Backup Hoàn Tất!
echo ========================================
echo Backup được lưu tại: %BACKUP_PATH%
echo   - Database: %BACKUP_PATH%\database\
echo   - Files: %BACKUP_PATH%\files\
echo.
echo Để restore, chạy: restore.bat
echo.
pause
