# Liquibase Database Migration

## Cách hoạt động

Liquibase **KHÔNG tự động** cập nhật database khi bạn thêm file mới. Nó chỉ chạy khi:

1. **Spring Boot khởi động lần đầu**
2. **Container được restart**
3. **Application được restart**

## Quy trình thêm database migration mới

### Bước 1: Tạo file SQL mới

Tạo file SQL với tên theo format: `YYYYMMDDHHMM.sql`

Ví dụ: `202602081500.sql` (ngày 8/2/2026, 15:00)

```sql
-- Mô tả thay đổi
ALTER TABLE `your_table` ADD COLUMN `new_column` VARCHAR(255);
```

### Bước 2: Thêm entry vào `db.changelog-master.yaml`

Thêm changeset mới vào cuối file:

```yaml
  - changeSet:
      id: 202602081500
      author: YourName
      changes:
        - sqlFile:
            encoding: utf8
            path: classpath:db/changelog/202602081500.sql
```

**Lưu ý quan trọng:**
- `id` phải khớp với tên file (không có extension)
- `id` phải unique (không trùng với changeset khác)
- Thêm vào **cuối** file, không sửa changeset cũ

### Bước 3: Restart container để áp dụng

**Trong Development Mode:**

```bash
# Restart container manager-api-dev
docker restart xiaozhi-manager-api-dev

# Hoặc dừng và khởi động lại
docker compose -f docker-compose-dev.yml restart manager-api-dev
```

**Sau khi restart:**
- Liquibase sẽ tự động phát hiện changeset mới
- Chạy SQL migration
- Ghi lại vào bảng `DATABASECHANGELOG`

## Kiểm tra migration đã chạy

```bash
# Xem log của container
docker logs xiaozhi-manager-api-dev | grep -i liquibase

# Hoặc kiểm tra trong database
docker exec xiaozhi-esp32-server-db mysql -uroot -p123456 -e "SELECT * FROM DATABASECHANGELOG ORDER BY DATEEXECUTED DESC LIMIT 5;" xiaozhi_esp32_server
```

## Lưu ý

1. **Không tự động:** Liquibase không watch file changes, cần restart
2. **Không sửa changeset cũ:** Chỉ tạo changeset mới
3. **ID phải unique:** Nếu trùng ID, Liquibase sẽ báo lỗi
4. **Thứ tự quan trọng:** Changeset chạy theo thứ tự trong master file

## Troubleshooting

### Migration không chạy?

1. Kiểm tra file SQL có syntax error không
2. Kiểm tra entry trong master yaml đúng format không
3. Kiểm tra ID có trùng không
4. Xem log: `docker logs xiaozhi-manager-api-dev`

### Rollback migration?

Liquibase không tự động rollback. Cần tạo changeset mới để revert.
