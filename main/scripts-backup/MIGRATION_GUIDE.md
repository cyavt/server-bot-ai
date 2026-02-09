# Hướng dẫn Migration Scripts

## 📋 Thay đổi

Scripts đã được tổ chức lại thành cấu trúc mới:

### Cấu trúc cũ:
```
scripts/
├── backup.bat / backup.sh
├── backup-database.bat / backup-database.sh
├── restore.bat / restore.sh
├── restore-database.bat / restore-database.sh
├── start-dev.bat / start-dev.sh
└── stop-dev.bat / stop-dev.sh
```

### Cấu trúc mới:
```
main/
├── scripts-backup/       # Scripts backup/restore (đã di chuyển ra ngoài)
│   ├── windows/         # Scripts cho Windows
│   │   ├── backup.bat   # Backup tổng hợp (Database + Files)
│   │   └── restore.bat # Restore tổng hợp (Database + Files)
│   └── linux/          # Scripts cho Linux/Mac
│       ├── backup.sh   # Backup tổng hợp (Database + Files)
│       └── restore.sh  # Restore tổng hợp (Database + Files)
└── xiaozhi-server/      # Thư mục chứa ứng dụng
```

## 🔄 Thay đổi chính

### 1. Backup Tổng Hợp

**Trước đây:** Cần chạy 2 script riêng biệt:
- `backup-database.bat/sh` - Chỉ backup database
- `backup.bat/sh` - Chỉ backup files

**Bây giờ:** Chỉ cần 1 script:
- `../scripts-backup/windows/backup.bat` hoặc `../scripts-backup/linux/backup.sh` - Backup cả database và files

### 2. Restore Tổng Hợp

**Trước đây:** Cần chạy 2 script riêng biệt:
- `restore-database.bat/sh` - Chỉ restore database
- `restore.bat/sh` - Chỉ restore files

**Bây giờ:** Chỉ cần 1 script:
- `../scripts-backup/windows/restore.bat` hoặc `../scripts-backup/linux/restore.sh` - Restore cả database và files

### 3. Cấu trúc Backup Mới

Backup mới có cấu trúc rõ ràng hơn:
```
backups/
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

## 📝 Cách sử dụng mới

### Windows

```bash
# Backup tổng hợp
cd main
..\scripts-backup\windows\backup.bat

# Restore tổng hợp
..\scripts-backup\windows\restore.bat
# Hoặc chỉ định backup cụ thể
..\scripts-backup\windows\restore.bat backup_20260208_213000
```

### Linux/Mac

```bash
# Cấp quyền thực thi (chỉ cần 1 lần)
cd main
chmod +x ../scripts-backup/linux/*.sh

# Backup tổng hợp
../scripts-backup/linux/backup.sh

# Restore tổng hợp
../scripts-backup/linux/restore.sh
# Hoặc chỉ định backup cụ thể
../scripts-backup/linux/restore.sh backup_20260208_213000
```

## ⚠️ Lưu ý

1. **Scripts cũ vẫn hoạt động:** Các script cũ (`backup.bat`, `backup-database.bat`, etc.) vẫn còn trong thư mục `scripts/` để tương thích ngược, nhưng khuyến nghị sử dụng scripts mới.

2. **Backup cũ vẫn tương thích:** Backup được tạo bởi scripts cũ vẫn có thể restore bằng scripts mới (nếu có cấu trúc tương tự).

3. **Backup mới:** Scripts mới tạo backup với cấu trúc mới, rõ ràng và dễ quản lý hơn.

## 🔧 Migration từ scripts cũ

Nếu bạn đang sử dụng scripts cũ, chỉ cần:

1. **Cập nhật đường dẫn:** Thay `scripts\backup.bat` thành `..\scripts-backup\windows\backup.bat` (chạy từ thư mục `main/`)
2. **Sử dụng script tổng hợp:** Không cần chạy 2 script riêng nữa, chỉ cần 1 script
3. **Vị trí mới:** Scripts đã được di chuyển ra `main/scripts-backup/` để dễ quản lý và tái sử dụng

## 📚 Tài liệu

- Xem `README.md` để biết hướng dẫn sử dụng chi tiết
- Xem `BACKUP_RESTORE_GUIDE.md` để biết hướng dẫn backup/restore chi tiết
