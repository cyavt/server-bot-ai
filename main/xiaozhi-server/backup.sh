#!/bin/bash

echo "========================================"
echo "   Backup Docker Data Script"
echo "========================================"
echo ""

# Tạo thư mục backup với timestamp
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"

echo "Đang tạo thư mục backup: $BACKUP_PATH"
mkdir -p "$BACKUP_PATH"

echo ""
echo "[1/5] Đang backup thư mục data..."
if [ -d "data" ]; then
    cp -r "data" "$BACKUP_PATH/" 2>/dev/null
    echo "✓ Đã backup data"
else
    echo "⚠ Thư mục data không tồn tại"
fi

echo ""
echo "[2/5] Đang backup thư mục models..."
if [ -d "models" ]; then
    cp -r "models" "$BACKUP_PATH/" 2>/dev/null
    echo "✓ Đã backup models"
else
    echo "⚠ Thư mục models không tồn tại"
fi

echo ""
echo "[3/5] Đang backup thư mục uploadfile..."
if [ -d "uploadfile" ]; then
    cp -r "uploadfile" "$BACKUP_PATH/" 2>/dev/null
    echo "✓ Đã backup uploadfile"
else
    echo "⚠ Thư mục uploadfile không tồn tại"
fi

echo ""
echo "[4/5] Đang backup MySQL data..."
if [ -d "mysql/data" ]; then
    cp -r "mysql/data" "$BACKUP_PATH/mysql_data" 2>/dev/null
    echo "✓ Đã backup MySQL data"
else
    echo "⚠ Thư mục mysql/data không tồn tại"
fi

echo ""
echo "[5/5] Đang backup docker-compose files..."
cp docker-compose.yml "$BACKUP_PATH/" 2>/dev/null
cp docker-compose_all.yml "$BACKUP_PATH/" 2>/dev/null
cp docker-compose_dev.yml "$BACKUP_PATH/" 2>/dev/null
cp docker-compose_hotreload.yml "$BACKUP_PATH/" 2>/dev/null
echo "✓ Đã backup docker-compose files"

echo ""
echo "========================================"
echo "   Backup hoàn tất!"
echo "========================================"
echo "Backup được lưu tại: $BACKUP_PATH"
echo ""
echo "Để restore, chạy: ./restore.sh"
echo ""
