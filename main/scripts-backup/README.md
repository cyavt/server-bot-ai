# Scripts Directory

Thư mục này chứa tất cả các script tiện ích để quản lý development environment.

## 📁 Cấu trúc

```
scripts/
├── windows/              # Scripts cho Windows
│   ├── backup.bat       # Backup tổng hợp (Database + Files)
│   └── restore.bat      # Restore tổng hợp (Database + Files)
│
├── linux/               # Scripts cho Linux/Mac
│   ├── backup.sh        # Backup tổng hợp (Database + Files)
│   └── restore.sh       # Restore tổng hợp (Database + Files)
│
└── BACKUP_RESTORE_GUIDE.md  # Hướng dẫn chi tiết backup/restore
```

## 🚀 Quick Start

### Windows

```bash
# Backup (Database + Files)
cd main
..\scripts-backup\windows\backup.bat

# Restore
..\scripts-backup\windows\restore.bat
```

### Linux/Mac

```bash
# Backup (Database + Files)
cd main
chmod +x ../scripts-backup/linux/*.sh
../scripts-backup/linux/backup.sh

# Restore
../scripts-backup/linux/restore.sh
```

## 📋 Các Scripts

### Backup & Restore Scripts

| Script | Mô tả | Usage |
|--------|-------|-------|
| `backup.bat/sh` | **Backup tổng hợp:** Database + File System (data, models, uploadfile, mysql data, docker-compose files) | `../scripts-backup/windows/backup.bat` |
| `restore.bat/sh` | **Restore tổng hợp:** Database + File System | `../scripts-backup/windows/restore.bat` |

## 💾 Backup & Restore

### Backup Tổng Hợp

Script backup sẽ tự động:
- ✅ **Backup Database:** Export toàn bộ database MySQL thành file SQL (tự động nén trên Linux)
- ✅ **Backup Files:** Copy các thư mục data, models, uploadfile, mysql/data
- ✅ **Backup Config:** Copy các file docker-compose
- ✅ **Tự động đặt tên:** Với timestamp (backup_YYYYMMDD_HHMMSS)
- ✅ **Tự động dọn dẹp:** Giữ lại 7 bản backup gần nhất (Linux)

**Cấu trúc backup:**
```
main/scripts-backup/backups/
└── backup_20260208_213000/
    ├── database/
    │   └── xiaozhi_db_backup_20260208_213000.sql[.gz]
    └── files/
        ├── data/
        ├── models/
        ├── uploadfile/
        ├── mysql_data/
        └── docker-compose*.yml
```

### Restore Tổng Hợp

Script restore sẽ:
- ✅ **Restore Database:** Import file SQL vào database
- ✅ **Restore Files:** Copy lại các thư mục đã backup
- ✅ **Tự động dừng containers:** Để tránh conflict
- ✅ **Xác nhận:** Yêu cầu xác nhận trước khi restore

## 📝 Lưu ý

1. **Tất cả scripts tự động chuyển về thư mục xiaozhi-server** (`main/xiaozhi-server/`) khi chạy để backup/restore files
2. **Backup được lưu tại:** `main/scripts-backup/backups/backup_YYYYMMDD_HHMMSS/`
3. **Scripts có thể chạy từ bất kỳ đâu**, nhưng khuyến nghị chạy từ thư mục `main/`
4. **Windows scripts:** Sử dụng `.bat` extension
5. **Linux/Mac scripts:** Cần `chmod +x` trước khi chạy

## 🔧 Troubleshooting

### Script không chạy được (Linux/Mac)

```bash
# Cấp quyền thực thi
chmod +x ../scripts-backup/linux/*.sh
```

### Container không tìm thấy

```bash
# Kiểm tra container có đang chạy không
docker ps | grep xiaozhi

# Kiểm tra network
docker network ls | grep main_default
```

### Backup thất bại

```bash
# Kiểm tra database container
docker ps | grep xiaozhi-esp32-server-db

# Kiểm tra log
docker logs xiaozhi-esp32-server-db
```

## 📚 Tài liệu thêm

Xem file `BACKUP_RESTORE_GUIDE.md` để biết hướng dẫn chi tiết về:
- Cách backup/restore thủ công
- Chuyển server
- Troubleshooting chi tiết
