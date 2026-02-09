#!/bin/bash
# Script backup tổng hợp: Database + File System
# Usage: ./backup.sh [backup_directory]

set -e

BACKUP_DIR=${1:-"$(dirname "$0")/../backups"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"

# Chuyển về thư mục xiaozhi-server để backup files
cd "$(dirname "$0")/../xiaozhi-server"

echo "========================================"
echo "   Backup Tổng Hợp: Database + Files"
echo "========================================"
echo ""
echo "Đang tạo thư mục backup: ${BACKUP_PATH}"
mkdir -p "${BACKUP_PATH}/database"
mkdir -p "${BACKUP_PATH}/files"

echo ""
echo "========================================"
echo "[PHẦN 1/2] Backup Database"
echo "========================================"

DB_NAME="xiaozhi_esp32_server"
DB_USER="root"
DB_PASSWORD="123456"
DB_CONTAINER="xiaozhi-esp32-server-db"
DB_BACKUP_FILE="${BACKUP_PATH}/database/xiaozhi_db_backup_${TIMESTAMP}.sql"

echo "Đang backup database: ${DB_NAME}"

if docker exec ${DB_CONTAINER} mysqldump -u${DB_USER} -p${DB_PASSWORD} \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --hex-blob \
  --default-character-set=utf8mb4 \
  ${DB_NAME} > "${DB_BACKUP_FILE}" 2>/dev/null; then
    
    echo "✓ Backup database thành công!"
    echo "  File: ${DB_BACKUP_FILE}"
    
    # Nén file database backup
    gzip "${DB_BACKUP_FILE}"
    DB_BACKUP_FILE_GZ="${DB_BACKUP_FILE}.gz"
    echo "  File đã được nén: ${DB_BACKUP_FILE_GZ}"
    echo "  Kích thước: $(du -h "${DB_BACKUP_FILE_GZ}" | cut -f1)"
else
    echo "✗ Backup database thất bại!"
    echo "  Kiểm tra container ${DB_CONTAINER} có đang chạy không"
fi

echo ""
echo "========================================"
echo "[PHẦN 2/2] Backup File System"
echo "========================================"

echo "[1/5] Đang backup thư mục data..."
if [ -d "data" ]; then
    cp -r "data" "${BACKUP_PATH}/files/" 2>/dev/null
    echo "✓ Đã backup data"
else
    echo "⚠ Thư mục data không tồn tại"
fi

echo "[2/5] Đang backup thư mục models..."
if [ -d "models" ]; then
    cp -r "models" "${BACKUP_PATH}/files/" 2>/dev/null
    echo "✓ Đã backup models"
else
    echo "⚠ Thư mục models không tồn tại"
fi

echo "[3/5] Đang backup thư mục uploadfile..."
if [ -d "uploadfile" ]; then
    cp -r "uploadfile" "${BACKUP_PATH}/files/" 2>/dev/null
    echo "✓ Đã backup uploadfile"
else
    echo "⚠ Thư mục uploadfile không tồn tại"
fi

echo "[4/5] Đang backup MySQL data files..."
if [ -d "mysql/data" ]; then
    cp -r "mysql/data" "${BACKUP_PATH}/files/mysql_data" 2>/dev/null
    echo "✓ Đã backup MySQL data files"
else
    echo "⚠ Thư mục mysql/data không tồn tại"
fi

echo "[5/5] Đang backup docker-compose files..."
cp docker-compose.yml "${BACKUP_PATH}/files/" 2>/dev/null || true
cp docker-compose_all.yml "${BACKUP_PATH}/files/" 2>/dev/null || true
cp docker-compose-dev.yml "${BACKUP_PATH}/files/" 2>/dev/null || true
cp docker-compose_hotreload.yml "${BACKUP_PATH}/files/" 2>/dev/null || true
echo "✓ Đã backup docker-compose files"

# Giữ lại 7 bản backup gần nhất
cd "${BACKUP_DIR}"
ls -dt backup_* 2>/dev/null | tail -n +8 | xargs -r rm -rf
echo ""
echo "✓ Đã giữ lại 7 bản backup gần nhất"

echo ""
echo "========================================"
echo "   Backup Hoàn Tất!"
echo "========================================"
echo "Backup được lưu tại: ${BACKUP_PATH}"
echo "  - Database: ${BACKUP_PATH}/database/"
echo "  - Files: ${BACKUP_PATH}/files/"
echo ""
echo "Để restore, chạy: ./restore.sh"
echo ""
