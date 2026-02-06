# Hướng dẫn Backup và Restore Docker Data

## Vấn đề
Khi chuyển sang máy khác chạy Docker, dữ liệu có thể bị mất nếu không được backup đúng cách.

## Giải pháp
Script backup và restore tự động sẽ giúp bạn:
- Backup tất cả dữ liệu quan trọng trước khi chuyển máy
- Restore dữ liệu trên máy mới

## Các thư mục được backup
1. **`data/`** - Cấu hình và dữ liệu ứng dụng
2. **`models/`** - Model files (SenseVoiceSmall, etc.)
3. **`uploadfile/`** - Files đã upload
4. **`mysql/data/`** - Dữ liệu MySQL database
5. **docker-compose files** - Cấu hình Docker

## Cách sử dụng

### Trên Windows

#### PowerShell (khuyến nghị)
```powershell
.\backup.bat
.\restore.bat
```

#### Command Prompt (CMD)
```cmd
backup.bat
restore.bat
```

**Lưu ý**: Trong PowerShell, luôn dùng `.\` trước tên file (ví dụ: `.\backup.bat`)

### Trên Linux/Mac

#### Backup
```bash
chmod +x backup.sh
./backup.sh
```

#### Restore
```bash
chmod +x restore.sh
./restore.sh
```

## Quy trình chuyển máy

### Bước 1: Backup trên máy cũ
1. Chạy `.\backup.bat` (PowerShell) hoặc `backup.bat` (CMD) hoặc `./backup.sh` (Linux/Mac)
2. Backup sẽ được lưu trong thư mục `backups/backup_YYYYMMDD_HHMMSS/`
3. Copy toàn bộ thư mục `backups/` sang máy mới (qua USB, network, cloud, etc.)

### Bước 2: Restore trên máy mới
1. Đảm bảo đã cài đặt Docker và Docker Compose
2. Copy thư mục `backups/` vào thư mục dự án
3. Chạy `.\restore.bat` (PowerShell) hoặc `restore.bat` (CMD) hoặc `./restore.sh` (Linux/Mac)
4. Chọn backup cần restore
5. Khởi động lại containers:
   ```bash
   docker-compose up -d
   # hoặc
   docker-compose -f docker-compose_all.yml up -d
   ```

## Lưu ý quan trọng

1. **Backup định kỳ**: Nên backup thường xuyên, đặc biệt trước khi cập nhật hoặc thay đổi cấu hình
2. **Kiểm tra dung lượng**: Backup có thể chiếm nhiều dung lượng, đặc biệt là thư mục `models/` và `mysql/data/`
3. **Dừng containers**: Script restore sẽ tự động dừng containers, nhưng nên kiểm tra trước khi restore
4. **Quyền truy cập**: Trên Linux/Mac, đảm bảo script có quyền thực thi (`chmod +x`)
5. **MySQL**: Khi restore MySQL data, đảm bảo MySQL container được khởi động lại đúng cách

## Backup tự động (tùy chọn)

Bạn có thể thiết lập backup tự động bằng cron (Linux/Mac) hoặc Task Scheduler (Windows):

### Linux/Mac - Cron
```bash
# Backup hàng ngày lúc 2 giờ sáng
0 2 * * * cd /path/to/xiaozhi-server && ./backup.sh
```

### Windows - Task Scheduler
1. Mở Task Scheduler
2. Tạo task mới
3. Trigger: Daily, 2:00 AM
4. Action: Start program `backup.bat` trong thư mục dự án

## Khắc phục sự cố

### Backup không tạo được
- Kiểm tra quyền ghi trong thư mục dự án
- Kiểm tra dung lượng đĩa còn trống

### Restore không hoạt động
- Đảm bảo containers đã được dừng
- Kiểm tra đường dẫn backup có đúng không
- Kiểm tra quyền truy cập file

### MySQL không khởi động sau restore
- Kiểm tra quyền sở hữu của thư mục `mysql/data/`
- Xem logs: `docker-compose logs xiaozhi-esp32-server-db`
