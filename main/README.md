Truy cập: ```cd main/xiaozhi-server```
```docker compose -f docker-compose_hotreload.yml down```
```docker compose -f docker-compose_hotreload.yml up -d```

docker compose -f docker-compose_hotreload.yml build xiaozhi-esp32-server-web
docker compose -f docker-compose_hotreload.yml restart xiaozhi-esp32-server-web

docker compose -f docker-compose_hotreload.yml build xiaozhi-esp32-server
docker compose -f docker-compose_hotreload.yml restart xiaozhi-esp32-server