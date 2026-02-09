#!/bin/bash
# Script restore tổng hợp: Database + File System
# Usage: ./restore.sh [backup_folder_name]

set -e

# Chuyển về thư mục xiaozhi-server để restore files
cd "$(dirname "$0")/../xiaozhi-server"

BACKUP_DIR="$(dirname "$0")/../backups"

if [ $# -eq 0 ]; then
    echo "========================================"
    echo "   Restore Tổng Hợp: Database + Files"
    echo "========================================"
    echo ""
    echo "Các backup có sẵn:"
    echo ""
    ls -1 "${BACKUP_DIR}" 2>/dev/null || echo "Không có backup nào"
    echo ""
    read -p "Nhập tên thư mục backup để restore (ví dụ: backup_20260208_213000): " BACKUP_NAME
else
    BACKUP_NAME=$1
fi

BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

if [ ! -d "${BACKUP_PATH}" ]; then
    echo "✗ Không tìm thấy backup: ${BACKUP_PATH}"
    exit 1
fi

echo ""
echo "=== CẢNH BÁO ==="
echo "Bạn sắp restore từ backup: ${BACKUP_NAME}"
echo "Dữ liệu hiện tại sẽ bị THAY THẾ hoàn toàn!"
echo ""
read -p "Bạn có chắc chắn muốn tiếp tục? (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    echo "Đã hủy restore."
    exit 0
fi

echo ""
echo "========================================"
echo "   Restore Tổng Hợp: Database + Files"
echo "========================================"
echo ""

# Dừng ứng dụng để tránh conflict
echo "Đang dừng containers..."
docker-compose -f docker-compose-dev.yml stop 2>/dev/null || true
docker stop xiaozhi-manager-api-dev 2>/dev/null || true

echo ""
echo "========================================"
echo "[PHẦN 1/2] Restore Database"
echo "========================================"

DB_NAME="xiaozhi_esp32_server"
DB_USER="root"
DB_PASSWORD="123456"
DB_CONTAINER="xiaozhi-esp32-server-db"

# Tìm file database backup
DB_BACKUP_FILE=$(find "${BACKUP_PATH}/database" -name "*.sql" -o -name "*.sql.gz" | head -n 1)

if [ -z "${DB_BACKUP_FILE}" ]; then
    echo "⚠ Không tìm thấy file database backup trong ${BACKUP_PATH}/database/"
    echo "  Bỏ qua restore database"
else
    echo "Đang restore database từ: ${DB_BACKUP_FILE}"
    
    # Nếu file là .gz, giải nén tạm
    if [[ "${DB_BACKUP_FILE}" == *.gz ]]; then
        echo "Đang giải nén file backup..."
        TEMP_SQL="${BACKUP_PATH}/database/temp_restore.sql"
        gunzip -c "${DB_BACKUP_FILE}" > "${TEMP_SQL}"
        DB_BACKUP_FILE="${TEMP_SQL}"
    fi
    
    if docker exec -i ${DB_CONTAINER} mysql -u${DB_USER} -p${DB_PASSWORD} ${DB_NAME} < "${DB_BACKUP_FILE}"; then
        echo "✓ Restore database thành công!"
    else
        echo "✗ Restore database thất bại!"
    fi
    
    # Xóa file tạm nếu có
    [ -f "${BACKUP_PATH}/database/temp_restore.sql" ] && rm -f "${BACKUP_PATH}/database/temp_restore.sql"
fi

echo ""
echo "========================================"
echo "[PHẦN 2/2] Restore File System"
echo "========================================"

echo "[1/5] Đang restore thư mục data..."
if [ -d "${BACKUP_PATH}/files/data" ]; then
    rm -rf "data"
    cp -r "${BACKUP_PATH}/files/data" .
    echo "✓ Đã restore data"
else
    echo "⚠ Không tìm thấy data trong backup"
fi

echo "[2/5] Đang restore thư mục models..."
if [ -d "${BACKUP_PATH}/files/models" ]; then
    rm -rf "models"
    cp -r "${BACKUP_PATH}/files/models" .
    echo "✓ Đã restore models"
else
    echo "⚠ Không tìm thấy models trong backup"
fi

echo "[3/5] Đang restore thư mục uploadfile..."
if [ -d "${BACKUP_PATH}/files/uploadfile" ]; then
    rm -rf "uploadfile"
    cp -r "${BACKUP_PATH}/files/uploadfile" .
    echo "✓ Đã restore uploadfile"
else
    echo "⚠ Không tìm thấy uploadfile trong backup"
fi

echo "[4/5] Đang restore MySQL data files..."
if [ -d "${BACKUP_PATH}/files/mysql_data" ]; then
    rm -rf "mysql/data"
    mkdir -p "mysql"
    cp -r "${BACKUP_PATH}/files/mysql_data" "mysql/data"
    echo "✓ Đã restore MySQL data files"
else
    echo "⚠ Không tìm thấy MySQL data trong backup"
fi

echo "[5/5] Đang restore docker-compose files..."
if [ -f "${BACKUP_PATH}/files/docker-compose.yml" ]; then
    cp "${BACKUP_PATH}/files/docker-compose.yml" .
fi
if [ -f "${BACKUP_PATH}/files/docker-compose_all.yml" ]; then
    cp "${BACKUP_PATH}/files/docker-compose_all.yml" .
fi
if [ -f "${BACKUP_PATH}/files/docker-compose-dev.yml" ]; then
    cp "${BACKUP_PATH}/files/docker-compose-dev.yml" .
fi
if [ -f "${BACKUP_PATH}/files/docker-compose_hotreload.yml" ]; then
    cp "${BACKUP_PATH}/files/docker-compose_hotreload.yml" .
fi
echo "✓ Đã restore docker-compose files"

echo ""
echo "========================================"
echo "   Restore Hoàn Tất!"
echo "========================================"
echo ""
echo "Bạn có thể khởi động lại containers bằng:"
echo "  docker compose -f docker-compose-dev.yml up -d"
echo ""
