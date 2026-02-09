# Xiaozhi ESP32 Server

Hệ thống quản lý và điều khiển thiết bị ESP32 với các module: Python Server, Backend API (Spring Boot), Frontend (Vue.js), Database (MySQL) và Cache (Redis).

## 📋 Mục lục

- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Sử dụng](#sử-dụng)
- [Các Services và Ports](#các-services-và-ports)
- [Development Mode](#development-mode)
- [Production Mode](#production-mode)
- [Quản lý Services](#quản-lý-services)
- [Troubleshooting](#troubleshooting)

## 🏗️ Kiến trúc hệ thống

Hệ thống bao gồm các thành phần chính:

```
┌─────────────────┐
│  Frontend (Vue) │  Port 8001 - Hot Reload
└────────┬────────┘
         │
┌────────▼────────┐
│  Backend API    │  Port 8003 - Spring Boot
│  (Spring Boot)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ MySQL │ │ Redis │
│ 3366  │ │ 6379  │
└───────┘ └───────┘
    │
┌───▼──────────────┐
│ Python Server    │  Port 8000 - Hot Reload
│ (ESP32 Handler)  │
└──────────────────┘
```

## 📦 Yêu cầu hệ thống

- **Docker**: Version 20.10 trở lên
- **Docker Compose**: Version 2.0 trở lên
- **Dung lượng ổ cứng**: Tối thiểu 5GB (cho images, volumes, models)
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB)
- **OS**: Windows 10+, Linux, hoặc macOS

## 🚀 Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd SERVER/main/xiaozhi-server
```

### 2. Kiểm tra Docker

```bash
docker --version
docker compose version
```

### 3. Tạo network (nếu chưa có)

```bash
docker network create main_default
```

## 💻 Sử dụng

### Development Mode (Khuyến nghị cho phát triển)

Development mode cung cấp hot reload cho Frontend và Python Server, build từ Dockerfile cho Backend API.

#### Windows

```bash
cd main\xiaozhi-server
scripts\start-dev.bat
```

#### Linux/Mac

```bash
cd main/xiaozhi-server
./scripts/start-dev.sh
```

#### Hoặc sử dụng Docker Compose trực tiếp

```bash
cd main/xiaozhi-server
docker compose -f docker-compose-dev.yml up -d
```

### Production Mode

Sử dụng images từ container registry:

```bash
cd main/xiaozhi-server
docker compose -f docker-compose_all.yml up -d
```

## 🌐 Các Services và Ports

| Service | Container Name | Port | Mô tả |
|---------|---------------|------|-------|
| **Frontend (Vue)** | `xiaozhi-esp32-manager-web-dev` | 8001 | Web interface với hot reload |
| **Backend API** | `xiaozhi-manager-api-dev` | 8003 | REST API (Spring Boot) |
| **Python Server** | `xiaozhi-esp32-server` | 8000 | ESP32 WebSocket server |
| **Test Page** | `xiaozhi-esp32-test-page` | 8006 | Static test page với auto-reload |
| **MySQL** | `xiaozhi-esp32-server-db` | 3366 | Database server |
| **Redis** | `xiaozhi-esp32-server-redis` | 6379 | Cache server (internal) |

### URLs truy cập

- **Frontend**: http://localhost:8001
- **Backend API**: http://localhost:8003/xiaozhi
- **Python Server**: http://localhost:8000
- **Test Page**: http://localhost:8006/test_page.html
- **Database**: localhost:3366 (user: `root`, password: `123456`)

## 🔧 Development Mode

### Đặc điểm

- ✅ **Frontend (Vue)**: Hot reload - thay đổi code tự động reload
- ✅ **Python Server**: Hot reload với volume mount - thay đổi code tự động reload
- ✅ **Backend API**: Build từ Dockerfile - cần rebuild khi thay đổi code
- ✅ **Test Page**: Auto-reload với live-server

### Rebuild Backend API sau khi thay đổi code

```bash
# Rebuild image
docker compose -f docker-compose-dev.yml build manager-api-dev

# Restart service
docker compose -f docker-compose-dev.yml up -d manager-api-dev
```

### Xem logs

```bash
# Tất cả services
docker compose -f docker-compose-dev.yml logs -f

# Từng service cụ thể
docker logs -f xiaozhi-manager-api-dev      # Backend API
docker logs -f xiaozhi-esp32-manager-web-dev  # Frontend
docker logs -f xiaozhi-esp32-server         # Python Server
docker logs -f xiaozhi-esp32-server-db      # Database
docker logs -f xiaozhi-esp32-server-redis   # Redis
```

## 🏭 Production Mode

Production mode sử dụng pre-built images từ container registry, không có hot reload.

### Cấu hình

File: `docker-compose_all.yml`

- Sử dụng images từ `ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server`
- Không mount source code (chỉ mount data volumes)
- Tối ưu cho production

## 🛠️ Quản lý Services

### Dừng tất cả services

#### Windows
```bash
scripts\stop-dev.bat
```

#### Linux/Mac
```bash
./scripts/stop-dev.sh
```

#### Hoặc
```bash
docker compose -f docker-compose-dev.yml down
```

### Dừng và xóa volumes (⚠️ Xóa dữ liệu)

```bash
docker compose -f docker-compose-dev.yml down -v
```

### Restart một service cụ thể

```bash
docker compose -f docker-compose-dev.yml restart manager-api-dev
```

### Xem trạng thái services

```bash
docker compose -f docker-compose-dev.yml ps
```

### Xem resource usage

```bash
docker stats
```

## 🔍 Troubleshooting

### Port đã được sử dụng

Nếu port đã được sử dụng, bạn có thể:

1. **Thay đổi port trong docker-compose-dev.yml**:
   ```yaml
   ports:
     - "8001:8001"  # Thay đổi port bên trái (host)
   ```

2. **Hoặc dừng service đang sử dụng port đó**

### Database connection error

1. Kiểm tra database đã sẵn sàng:
   ```bash
   docker logs xiaozhi-esp32-server-db
   ```

2. Kiểm tra health check:
   ```bash
   docker inspect xiaozhi-esp32-server-db | grep -A 10 Health
   ```

3. Đợi database khởi động hoàn toàn (có thể mất 30-60 giây lần đầu)

### Backend API không start

1. Kiểm tra logs:
   ```bash
   docker logs xiaozhi-manager-api-dev
   ```

2. Rebuild image:
   ```bash
   docker compose -f docker-compose-dev.yml build --no-cache manager-api-dev
   docker compose -f docker-compose-dev.yml up -d manager-api-dev
   ```

3. Kiểm tra environment variables trong `docker-compose-dev.yml`

### Frontend không hot reload

1. Kiểm tra volumes mount:
   ```bash
   docker inspect xiaozhi-esp32-manager-web-dev | grep -A 5 Mounts
   ```

2. Restart service:
   ```bash
   docker compose -f docker-compose-dev.yml restart manager-web-dev
   ```

### Python Server không hot reload

1. Kiểm tra volume mount:
   ```bash
   docker inspect xiaozhi-esp32-server | grep -A 5 Mounts
   ```

2. Kiểm tra file permissions trên Windows (có thể cần chạy Docker Desktop với quyền admin)

### Xóa và rebuild từ đầu

```bash
# Dừng và xóa tất cả
docker compose -f docker-compose-dev.yml down -v

# Xóa images
docker rmi manager-api:dev xiaozhi-server:local

# Rebuild và start lại
docker compose -f docker-compose-dev.yml up -d --build
```

## 📁 Cấu trúc thư mục

```
main/xiaozhi-server/
├── docker-compose-dev.yml      # Development mode config
├── docker-compose_all.yml       # Production mode config
├── scripts/                     # Utility scripts
│   ├── start-dev.bat/sh         # Start development mode
│   ├── stop-dev.bat/sh          # Stop development mode
│   └── ...
├── data/                        # Data directory (mounted)
├── models/                      # AI models (mounted)
├── mysql/data/                  # MySQL data (mounted)
├── test/                        # Test page files
└── README.md                    # File này
```

## 🔐 Environment Variables

### Backend API

Các biến môi trường quan trọng trong `docker-compose-dev.yml`:

- `SPRING_PROFILES_ACTIVE`: Profile Spring Boot (dev/prod)
- `SPRING_DATASOURCE_DRUID_URL`: Database connection URL
- `SPRING_DATASOURCE_DRUID_USERNAME`: Database username
- `SPRING_DATASOURCE_DRUID_PASSWORD`: Database password
- `SPRING_DATA_REDIS_HOST`: Redis host
- `SPRING_DATA_REDIS_PORT`: Redis port
- `SPRING_DATA_REDIS_PASSWORD`: Redis password

### Database

- `MYSQL_ROOT_PASSWORD`: Root password (mặc định: `123456`)
- `MYSQL_DATABASE`: Database name (mặc định: `xiaozhi_esp32_server`)

## 📝 Notes

- **Development mode**: Sử dụng cho phát triển với hot reload
- **Production mode**: Sử dụng cho môi trường production với images từ registry
- **Database**: Dữ liệu được lưu trong `./mysql/data/` (persistent)
- **Models**: AI models được mount từ `./models/`
- **Data**: Application data được mount từ `./data/`

## 🤝 Đóng góp

Khi thêm tính năng mới hoặc sửa lỗi, vui lòng:

1. Cập nhật documentation này nếu cần
2. Test trên development mode trước
3. Đảm bảo không break existing services

## 📄 License

[Thêm thông tin license nếu có]
