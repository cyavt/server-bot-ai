@echo off
chcp 65001 >nul
echo ========================================
echo    Restore Docker Data Script
echo ========================================
echo.

set "BACKUP_DIR=backups"

if not exist "%BACKUP_DIR%" (
    echo ❌ Không tìm thấy thư mục backups!
    pause
    exit /b 1
)

echo Các backup có sẵn:
echo.
dir /B /AD "%BACKUP_DIR%" 2>nul
echo.

set /p "BACKUP_NAME=Nhập tên thư mục backup để restore (ví dụ: backup_20240101_120000): "

set "BACKUP_PATH=%BACKUP_DIR%\%BACKUP_NAME%"

if not exist "%BACKUP_PATH%" (
    echo ❌ Không tìm thấy backup: %BACKUP_PATH%
    pause
    exit /b 1
)

echo.
echo ⚠ CẢNH BÁO: Quá trình restore sẽ ghi đè dữ liệu hiện tại!
set /p "CONFIRM=Bạn có chắc chắn muốn tiếp tục? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo Đã hủy restore.
    pause
    exit /b 0
)

echo.
echo Đang dừng containers...
docker-compose down 2>nul
docker-compose -f docker-compose_all.yml down 2>nul

echo.
echo [1/5] Đang restore thư mục data...
if exist "%BACKUP_PATH%\data" (
    if exist "data" rmdir /S /Q "data"
    xcopy /E /I /Y "%BACKUP_PATH%\data" "data\" >nul
    echo ✓ Đã restore data
) else (
    echo ⚠ Không tìm thấy data trong backup
)

echo.
echo [2/5] Đang restore thư mục models...
if exist "%BACKUP_PATH%\models" (
    if exist "models" rmdir /S /Q "models"
    xcopy /E /I /Y "%BACKUP_PATH%\models" "models\" >nul
    echo ✓ Đã restore models
) else (
    echo ⚠ Không tìm thấy models trong backup
)

echo.
echo [3/5] Đang restore thư mục uploadfile...
if exist "%BACKUP_PATH%\uploadfile" (
    if exist "uploadfile" rmdir /S /Q "uploadfile"
    xcopy /E /I /Y "%BACKUP_PATH%\uploadfile" "uploadfile\" >nul
    echo ✓ Đã restore uploadfile
) else (
    echo ⚠ Không tìm thấy uploadfile trong backup
)

echo.
echo [4/5] Đang restore MySQL data...
if exist "%BACKUP_PATH%\mysql_data" (
    if exist "mysql\data" rmdir /S /Q "mysql\data"
    if not exist "mysql" mkdir "mysql"
    xcopy /E /I /Y "%BACKUP_PATH%\mysql_data" "mysql\data\" >nul
    echo ✓ Đã restore MySQL data
) else (
    echo ⚠ Không tìm thấy MySQL data trong backup
)

echo.
echo [5/5] Đang restore docker-compose files...
if exist "%BACKUP_PATH%\docker-compose.yml" (
    copy /Y "%BACKUP_PATH%\docker-compose.yml" "docker-compose.yml" >nul
)
if exist "%BACKUP_PATH%\docker-compose_all.yml" (
    copy /Y "%BACKUP_PATH%\docker-compose_all.yml" "docker-compose_all.yml" >nul
)
echo ✓ Đã restore docker-compose files

echo.
echo ========================================
echo    Restore hoàn tất!
echo ========================================
echo.
echo Bạn có thể khởi động lại containers bằng:
echo   docker-compose up -d
echo hoặc
echo   docker-compose -f docker-compose_all.yml up -d
echo.
pause
