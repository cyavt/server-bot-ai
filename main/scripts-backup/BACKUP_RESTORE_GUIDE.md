# Hướng dẫn Backup và Restore Database

## 📋 Tổng quan

### Migration có làm mất dữ liệu không?

**KHÔNG!** Migration chỉ:
- ✅ Chạy các changeset **chưa được thực thi** (chưa có trong DATABASECHANGELOG)
- ✅ Thêm/sửa cấu trúc bảng (ALTER TABLE, ADD COLUMN, ...)
- ✅ INSERT dữ liệu mặc định mới
- ❌ **KHÔNG xóa** dữ liệu người dùng hiện có

**Lưu ý:** Nếu migration có lệnh DELETE hoặc DROP TABLE, dữ liệu sẽ bị xóa. Luôn kiểm tra nội dung migration trước khi chạy.

---

## 🔄 Backup Tổng Hợp (Database + Files)

### Cách 1: Sử dụng script tự động (Khuyến nghị)

#### Windows:
```bash
cd main
..\scripts-backup\windows\backup.bat
```

#### Linux/Mac:
```bash
cd main
chmod +x ../scripts-backup/linux/*.sh
../scripts-backup/linux/backup.sh
```

Script sẽ tự động backup:
- ✅ **Database:** Export toàn bộ database MySQL thành file SQL (tự động nén trên Linux)
- ✅ **Files:** Copy các thư mục data, models, uploadfile, mysql/data
- ✅ **Config:** Copy các file docker-compose
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

### Cách 2: Backup chỉ Database (thủ công)

```bash
# Tạo thư mục backup
mkdir -p main/scripts-backup/backups/database

# Backup database
docker exec xiaozhi-esp32-server-db mysqldump \
  -uroot -p123456 \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --hex-blob \
  --default-character-set=utf8mb4 \
  xiaozhi_esp32_server > main/scripts-backup/backups/database/xiaozhi_db_backup_$(date +%Y%m%d_%H%M%S).sql

# Nén file (tùy chọn)
gzip main/scripts-backup/backups/database/xiaozhi_db_backup_*.sql
```

### Cách 3: Backup chỉ dữ liệu (không có cấu trúc)

```bash
# Backup chỉ dữ liệu, không có CREATE TABLE
docker exec xiaozhi-esp32-server-db mysqldump \
  -uroot -p123456 \
  --no-create-info \
  --skip-triggers \
  xiaozhi_esp32_server > main/scripts-backup/backups/data_only_backup.sql
```

---

## 🔙 Restore Tổng Hợp (Database + Files)

### Cách 1: Sử dụng script tự động (Khuyến nghị)

#### Windows:
```bash
cd main
..\scripts-backup\windows\restore.bat
# Hoặc chỉ định tên backup cụ thể
..\scripts-backup\windows\restore.bat backup_20260208_213000
```

#### Linux/Mac:
```bash
cd main
chmod +x ../scripts-backup/linux/*.sh
../scripts-backup/linux/restore.sh
# Hoặc chỉ định tên backup cụ thể
../scripts-backup/linux/restore.sh backup_20260208_213000
```

Script sẽ tự động restore:
- ✅ **Database:** Import file SQL vào database
- ✅ **Files:** Copy lại các thư mục đã backup
- ✅ **Tự động dừng containers:** Để tránh conflict
- ✅ **Xác nhận:** Yêu cầu xác nhận trước khi restore

### Cách 2: Restore chỉ Database (thủ công)

```bash
# Dừng ứng dụng để tránh conflict
docker stop xiaozhi-manager-api-dev

# Restore database
docker exec -i xiaozhi-esp32-server-db mysql \
  -uroot -p123456 \
  xiaozhi_esp32_server < main/scripts-backup/backups/backup_20260208_213000/database/xiaozhi_db_backup_20260208_213000.sql

# Khởi động lại ứng dụng
docker start xiaozhi-manager-api-dev
```

### Nếu file backup đã nén (.gz):

```bash
# Giải nén và restore
gunzip -c main/scripts-backup/backups/backup_20260208_213000/database/xiaozhi_db_backup_20260208_213000.sql.gz | \
  docker exec -i xiaozhi-esp32-server-db mysql -uroot -p123456 xiaozhi_esp32_server
```

---

## 🚀 Chuyển Server (Migration)

### Bước 1: Backup tổng hợp trên server cũ

```bash
# Trên server cũ - Windows
cd main
..\scripts-backup\windows\backup.bat

# Trên server cũ - Linux/Mac
cd main
../scripts-backup/linux/backup.sh

# Backup sẽ được lưu tại: main/scripts-backup/backups/backup_YYYYMMDD_HHMMSS/
```

### Bước 2: Copy thư mục backup sang server mới

```bash
# Sử dụng SCP (copy toàn bộ thư mục backup)
scp -r main/scripts-backup/backups/backup_20260208_213000 user@new-server:/path/to/backups/

# Hoặc sử dụng rsync (hiệu quả hơn)
rsync -avz main/scripts-backup/backups/backup_20260208_213000 user@new-server:/path/to/backups/

# Hoặc sử dụng FTP/SFTP
# Hoặc copy qua USB/external drive
```

### Bước 3: Trên server mới

#### 3.1. Khởi động database container (nếu chưa có)

```bash
cd main/xiaozhi-server
docker-compose -f docker-compose-dev.yml up -d xiaozhi-esp32-server-db
```

#### 3.2. Tạo database mới (nếu chưa có)

```bash
docker exec xiaozhi-esp32-server-db mysql \
  -uroot -p123456 \
  -e "CREATE DATABASE IF NOT EXISTS xiaozhi_esp32_server CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

#### 3.3. Restore tổng hợp

```bash
# Sử dụng script (Khuyến nghị)
cd main

# Windows
..\scripts-backup\windows\restore.bat backup_20260208_213000

# Linux/Mac
../scripts-backup/linux/restore.sh backup_20260208_213000

# Script sẽ tự động restore cả database và files
```

#### 3.4. Khởi động ứng dụng

```bash
cd main/xiaozhi-server
docker-compose -f docker-compose-dev.yml up -d manager-api-dev
```

#### 3.5. Kiểm tra migration

```bash
# Kiểm tra các migration đã chạy
docker exec xiaozhi-esp32-server-db mysql -uroot -p123456 xiaozhi_esp32_server \
  -e "SELECT ID, AUTHOR, DATEEXECUTED FROM DATABASECHANGELOG ORDER BY DATEEXECUTED DESC LIMIT 10;"

# Kiểm tra log ứng dụng
docker logs xiaozhi-manager-api-dev | grep -i liquibase
```

---

## 📝 Lưu ý quan trọng

### 1. Backup định kỳ

- **Khuyến nghị:** Backup hàng ngày hoặc trước mỗi lần deploy
- **Giữ lại:** Ít nhất 7 bản backup gần nhất
- **Lưu trữ:** Backup ở nhiều nơi (local, cloud, external drive)

### 2. Trước khi restore

- ✅ **Luôn backup** dữ liệu hiện tại trước khi restore
- ✅ **Kiểm tra** file backup có hợp lệ không
- ✅ **Dừng ứng dụng** để tránh conflict
- ✅ **Kiểm tra** version database và MySQL version tương thích

### 3. Migration khi chuyển server

- ✅ **Giữ nguyên** thư mục `db/changelog/` và `db.changelog-master.yaml`
- ✅ **Không xóa** bảng `DATABASECHANGELOG` và `DATABASECHANGELOGLOCK`
- ✅ Liquibase sẽ tự động phát hiện và chạy các migration mới

### 4. Kiểm tra sau khi restore

```bash
# Kiểm tra số lượng bản ghi
docker exec xiaozhi-esp32-server-db mysql -uroot -p123456 xiaozhi_esp32_server \
  -e "SELECT 'sys_user' as table_name, COUNT(*) as count FROM sys_user
      UNION ALL
      SELECT 'ai_agent', COUNT(*) FROM ai_agent
      UNION ALL
      SELECT 'ai_device', COUNT(*) FROM ai_device;"

# Kiểm tra dữ liệu người dùng
docker exec xiaozhi-esp32-server-db mysql -uroot -p123456 xiaozhi_esp32_server \
  -e "SELECT id, username, email FROM sys_user LIMIT 5;"
```

---

## 🔧 Troubleshooting

### Lỗi: "Table already exists"

```bash
# Xóa database và tạo lại (CẨN THẬN!)
docker exec xiaozhi-esp32-server-db mysql -uroot -p123456 \
  -e "DROP DATABASE xiaozhi_esp32_server; CREATE DATABASE xiaozhi_esp32_server CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### Lỗi: "Access denied"

Kiểm tra password trong script có đúng không:
```bash
docker exec xiaozhi-esp32-server-db mysql -uroot -p123456 -e "SELECT 1;"
```

### Lỗi: "Character set mismatch"

Đảm bảo backup và restore đều dùng `utf8mb4`:
```bash
# Kiểm tra character set
docker exec xiaozhi-esp32-server-db mysql -uroot -p123456 xiaozhi_esp32_server \
  -e "SHOW VARIABLES LIKE 'character_set%';"
```

---

## 📞 Liên hệ

Nếu gặp vấn đề, kiểm tra:
1. Log container: `docker logs xiaozhi-manager-api-dev`
2. Log database: `docker logs xiaozhi-esp32-server-db`
3. Kiểm tra file backup có hợp lệ không
