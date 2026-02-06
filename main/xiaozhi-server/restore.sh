#!/bin/bash

echo "========================================"
echo "   Restore Docker Data Script"
echo "========================================"
echo ""

BACKUP_DIR="backups"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Không tìm thấy thư mục backups!"
    exit 1
fi

echo "Các backup có sẵn:"
echo ""
ls -1 "$BACKUP_DIR" 2>/dev/null
echo ""

read -p "Nhập tên thư mục backup để restore (ví dụ: backup_20240101_120000): " BACKUP_NAME

BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

if [ ! -d "$BACKUP_PATH" ]; then
    echo "❌ Không tìm thấy backup: $BACKUP_PATH"
    exit 1
fi

echo ""
echo "⚠ CẢNH BÁO: Quá trình restore sẽ ghi đè dữ liệu hiện tại!"
read -p "Bạn có chắc chắn muốn tiếp tục? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Đã hủy restore."
    exit 0
fi

echo ""
echo "Đang dừng containers..."
docker-compose down 2>/dev/null
docker-compose -f docker-compose_all.yml down 2>/dev/null

echo ""
echo "[1/5] Đang restore thư mục data..."
if [ -d "$BACKUP_PATH/data" ]; then
    rm -rf "data"
    cp -r "$BACKUP_PATH/data" .
    echo "✓ Đã restore data"
else
    echo "⚠ Không tìm thấy data trong backup"
fi

echo ""
echo "[2/5] Đang restore thư mục models..."
if [ -d "$BACKUP_PATH/models" ]; then
    rm -rf "models"
    cp -r "$BACKUP_PATH/models" .
    echo "✓ Đã restore models"
else
    echo "⚠ Không tìm thấy models trong backup"
fi

echo ""
echo "[3/5] Đang restore thư mục uploadfile..."
if [ -d "$BACKUP_PATH/uploadfile" ]; then
    rm -rf "uploadfile"
    cp -r "$BACKUP_PATH/uploadfile" .
    echo "✓ Đã restore uploadfile"
else
    echo "⚠ Không tìm thấy uploadfile trong backup"
fi

echo ""
echo "[4/5] Đang restore MySQL data..."
if [ -d "$BACKUP_PATH/mysql_data" ]; then
    rm -rf "mysql/data"
    mkdir -p "mysql"
    cp -r "$BACKUP_PATH/mysql_data" "mysql/data"
    echo "✓ Đã restore MySQL data"
else
    echo "⚠ Không tìm thấy MySQL data trong backup"
fi

echo ""
echo "[5/5] Đang restore docker-compose files..."
if [ -f "$BACKUP_PATH/docker-compose.yml" ]; then
    cp "$BACKUP_PATH/docker-compose.yml" .
fi
if [ -f "$BACKUP_PATH/docker-compose_all.yml" ]; then
    cp "$BACKUP_PATH/docker-compose_all.yml" .
fi
echo "✓ Đã restore docker-compose files"

echo ""
echo "========================================"
echo "   Restore hoàn tất!"
echo "========================================"
echo ""
echo "Bạn có thể khởi động lại containers bằng:"
echo "  docker-compose up -d"
echo "hoặc"
echo "  docker-compose -f docker-compose_all.yml up -d"
echo ""
