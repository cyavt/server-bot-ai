@echo off
chcp 65001 >nul
REM Script restore tổng hợp: Database + File System
REM Usage: restore.bat <backup_folder_name>

setlocal enabledelayedexpansion

REM Chuyển về thư mục xiaozhi-server để restore files
cd /d "%~dp0\..\xiaozhi-server"

set BACKUP_DIR=%~dp0..\backups

if "%~1"=="" (
    echo ========================================
    echo    Restore Tổng Hợp: Database + Files
    echo ========================================
    echo.
    echo Các backup có sẵn:
    echo.
    dir /B /AD "%BACKUP_DIR%" 2>nul
    echo.
    set /p "BACKUP_NAME=Nhập tên thư mục backup để restore (ví dụ: backup_20260208_213000): "
) else (
    set BACKUP_NAME=%~1
)

set BACKUP_PATH=%BACKUP_DIR%\%BACKUP_NAME%

if not exist "%BACKUP_PATH%" (
    echo ✗ Không tìm thấy backup: %BACKUP_PATH%
    pause
    exit /b 1
)

echo.
echo === CẢNH BÁO ===
echo Bạn sắp restore từ backup: %BACKUP_NAME%
echo Dữ liệu hiện tại sẽ bị THAY THẾ hoàn toàn!
echo.
set /p "CONFIRM=Bạn có chắc chắn muốn tiếp tục? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo Đã hủy restore.
    pause
    exit /b 0
)

echo.
echo ========================================
echo    Restore Tổng Hợp: Database + Files
echo ========================================
echo.

REM Dừng ứng dụng để tránh conflict
echo Đang dừng containers...
docker-compose -f docker-compose-dev.yml stop 2>nul
docker stop xiaozhi-manager-api-dev 2>nul

echo.
echo ========================================
echo [PHẦN 1/2] Restore Database
echo ========================================

set DB_NAME=xiaozhi_esp32_server
set DB_USER=root
set DB_PASSWORD=123456
set DB_CONTAINER=xiaozhi-esp32-server-db

REM Tìm file database backup
set DB_BACKUP_FILE=
for %%f in ("%BACKUP_PATH%\database\*.sql") do set DB_BACKUP_FILE=%%f
for %%f in ("%BACKUP_PATH%\database\*.sql.gz") do set DB_BACKUP_FILE=%%f

if "%DB_BACKUP_FILE%"=="" (
    echo ⚠ Không tìm thấy file database backup trong %BACKUP_PATH%\database\
    echo   Bỏ qua restore database
) else (
    echo Đang restore database từ: %DB_BACKUP_FILE%
    
    REM Nếu file là .gz, giải nén tạm
    if "%DB_BACKUP_FILE:~-3%"==".gz" (
        echo Đang giải nén file backup...
        REM Cần có 7zip hoặc gunzip
        REM 7z x "%DB_BACKUP_FILE%" -o"%BACKUP_PATH%\database\" >nul 2>&1
        REM set DB_BACKUP_FILE=%DB_BACKUP_FILE:~0,-3%
        echo ⚠ File .gz cần giải nén thủ công trước khi restore
        goto :skip_db_restore
    )
    
    docker exec -i %DB_CONTAINER% mysql -u%DB_USER% -p%DB_PASSWORD% %DB_NAME% < "%DB_BACKUP_FILE%"
    
    if %ERRORLEVEL% EQU 0 (
        echo ✓ Restore database thành công!
    ) else (
        echo ✗ Restore database thất bại!
    )
    
    :skip_db_restore
)

echo.
echo ========================================
echo [PHẦN 2/2] Restore File System
echo ========================================

echo [1/5] Đang restore thư mục data...
if exist "%BACKUP_PATH%\files\data" (
    if exist "data" rmdir /S /Q "data"
    xcopy /E /I /Y "%BACKUP_PATH%\files\data" "data\" >nul
    echo ✓ Đã restore data
) else (
    echo ⚠ Không tìm thấy data trong backup
)

echo [2/5] Đang restore thư mục models...
if exist "%BACKUP_PATH%\files\models" (
    if exist "models" rmdir /S /Q "models"
    xcopy /E /I /Y "%BACKUP_PATH%\files\models" "models\" >nul
    echo ✓ Đã restore models
) else (
    echo ⚠ Không tìm thấy models trong backup
)

echo [3/5] Đang restore thư mục uploadfile...
if exist "%BACKUP_PATH%\files\uploadfile" (
    if exist "uploadfile" rmdir /S /Q "uploadfile"
    xcopy /E /I /Y "%BACKUP_PATH%\files\uploadfile" "uploadfile\" >nul
    echo ✓ Đã restore uploadfile
) else (
    echo ⚠ Không tìm thấy uploadfile trong backup
)

echo [4/5] Đang restore MySQL data files...
if exist "%BACKUP_PATH%\files\mysql_data" (
    if exist "mysql\data" rmdir /S /Q "mysql\data"
    if not exist "mysql" mkdir "mysql"
    xcopy /E /I /Y "%BACKUP_PATH%\files\mysql_data" "mysql\data\" >nul
    echo ✓ Đã restore MySQL data files
) else (
    echo ⚠ Không tìm thấy MySQL data trong backup
)

echo [5/5] Đang restore docker-compose files...
if exist "%BACKUP_PATH%\files\docker-compose.yml" (
    copy /Y "%BACKUP_PATH%\files\docker-compose.yml" "docker-compose.yml" >nul
)
if exist "%BACKUP_PATH%\files\docker-compose_all.yml" (
    copy /Y "%BACKUP_PATH%\files\docker-compose_all.yml" "docker-compose_all.yml" >nul
)
if exist "%BACKUP_PATH%\files\docker-compose-dev.yml" (
    copy /Y "%BACKUP_PATH%\files\docker-compose-dev.yml" "docker-compose-dev.yml" >nul
)
if exist "%BACKUP_PATH%\files\docker-compose_hotreload.yml" (
    copy /Y "%BACKUP_PATH%\files\docker-compose_hotreload.yml" "docker-compose_hotreload.yml" >nul
)
echo ✓ Đã restore docker-compose files

echo.
echo ========================================
echo    Restore Hoàn Tất!
echo ========================================
echo.
echo Bạn có thể khởi động lại containers bằng:
echo   docker compose -f docker-compose-dev.yml up -d
echo.
pause
