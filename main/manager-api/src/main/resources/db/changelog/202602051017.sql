-- Thêm provider mô hình nhớ powermem
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`)
VALUES ('SYSTEM_Memory_powermem', 'Memory', 'powermem', 'PowerMem nhớ', '[
  {"key":"enable_user_profile","label":"Bật hình ảnh người dùng","type":"boolean"},
  {"key":"llm_provider","label":"Nhà cung cấp LLM","type":"string"},
  {"key":"llm_api_key","label":"Khóa API LLM","type":"string"},
  {"key":"llm_model","label":"Mô hình LLM","type":"string"},
  {"key":"openai_base_url","label":"URL cơ sở OpenAI","type":"string"},
  {"key":"embedding_provider","label":"Nhà cung cấp Embedding","type":"string"},
  {"key":"embedding_api_key","label":"Khóa API Embedding","type":"string"},
  {"key":"embedding_model","label":"Mô hình Embedding","type":"string"},
  {"key":"embedding_openai_base_url","label":"URL cơ sở OpenAI Embedding","type":"string"},
  {"key":"embedding_dims","label":"Chiều Embedding","type":"integer"},
  {"key":"vector_store","label":"Cấu hình lưu trữ vector (JSON)","type":"dict"}
]', 4, 1, NOW(), 1, NOW());

-- Thêm cấu hình mô hình nhớ PowerMem
INSERT INTO `ai_model_config` VALUES (
  'Memory_powermem',
  'Memory',
  'powermem',
  'PowerMem nhớ',
  0,
  1,
  '{\"type\": \"powermem\", \"enable_user_profile\": true, \"llm_provider\": \"openai\", \"llm_api_key\": \"Khóa API LLM của bạn\", \"llm_model\": \"qwen-plus\", \"openai_base_url\": \"\", \"embedding_provider\": \"openai\", \"embedding_api_key\": \"Khóa API mô hình embedding của bạn\", \"embedding_model\": \"text-embedding-v4\", \"embedding_openai_base_url\": \"https://api.openai.com/v1\", \"embedding_dims\": \"\", \"vector_store\": {\"provider\": \"sqlite\", \"config\": {}}}',
  NULL,
  NULL,
  4,
  NULL,
  NULL,
  NULL,
  NULL
);


-- Hướng dẫn cấu hình nhớ PowerMem
UPDATE `ai_model_config` SET
`doc_link` = 'https://github.com/oceanbase/powermem',
`remark` = 'PowerMem là component nhớ agent mã nguồn mở của OceanBase, tổng hợp nhớ thông qua LLM local
GitHub: https://github.com/oceanbase/powermem
Website: https://www.powermem.ai/
Ví dụ sử dụng: https://github.com/oceanbase/powermem/tree/main/examples

【Thông tin chi phí】
PowerMem miễn phí, chi phí thực tế phụ thuộc vào LLM và database được chọn:
- Sử dụng sqlite + LLM miễn phí (như glm-4-flash) = hoàn toàn miễn phí
- Sử dụng LLM hoặc database trên đám mây = tính phí theo dịch vụ tương ứng

【enable_user_profile】Chức năng hình ảnh người dùng
- false: Sử dụng chế độ nhớ thông thường (AsyncMemory)
- true: Sử dụng chế độ hình ảnh người dùng (UserMemory), tự động trích xuất thông tin người dùng
- Chức năng hình ảnh người dùng hỗ trợ: oceanbase、seekdb、sqlite (powermem 0.3.0+)

【llm】Cấu hình LLM - Dùng cho tổng hợp nhớ và trích xuất hình ảnh người dùng
  provider: Nhà cung cấp LLM, giá trị có thể chọn:
    - qwen: Thông Nghĩa Thiên Vấn (https://bailian.console.aliyun.com/?apiKey=1#/api-key)
    - openai: Giao diện tương thích OpenAI
    - zhipu: Trí Phổ AI (https://bigmodel.cn/usercenter/proj-mgmt/apikeys) - Khuyến nghị dùng glm-4-flash miễn phí
  config: Tham số cấu hình LLM
    - api_key: Khóa API (bắt buộc)
    - model: Tên mô hình, như qwen-plus、glm-4-flash, v.v.
    - openai_base_url: Địa chỉ dịch vụ tùy chỉnh (tùy chọn), như https://api.openai.com/v1
  Ví dụ:
    {"provider": "zhipu", "config": {"api_key": "your_key", "model": "glm-4-flash"}}
    {"provider": "qwen", "config": {"api_key": "your_key", "model": "qwen-plus"}}

【embedder】Cấu hình Embedding - Dùng cho vector hóa nội dung nhớ
  provider: Nhà cung cấp mô hình embedding, giá trị có thể chọn:
    - qwen: Thông Nghĩa Thiên Vấn
    - openai: Giao diện tương thích OpenAI
  config: Tham số cấu hình Embedding
    - api_key: Khóa API (bắt buộc)
    - model: Tên mô hình, như text-embedding-v4、text-embedding-3-small, v.v.
    - openai_base_url: Địa chỉ dịch vụ tùy chỉnh (tùy chọn)
    - embedding_dims: Chiều vector (tùy chọn), cần cấu hình nếu không phải 1536
  Ví dụ:
    {"provider": "openai", "config": {"api_key": "your_key", "model": "text-embedding-v4", "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"}}

【vector_store】Cấu hình lưu trữ database - Dùng cho lưu trữ nhớ đã vector hóa
  provider: Loại database, giá trị có thể chọn:
    - sqlite: Database local nhẹ (khuyến nghị cho người mới, không cần cấu hình thêm)
    - oceanbase: Database OceanBase (khuyến nghị cho môi trường production, hiệu suất tốt nhất)
    - seekdb: SeekDB (khuyến nghị, lưu trữ tích hợp ứng dụng AI)
    - postgres: Database PostgreSQL

  Cấu hình SQLite (không cần cấu hình thêm):
    {"provider": "sqlite", "config": {}}

  Ví dụ cấu hình OceanBase:
    {"provider": "oceanbase", "config": {
      "host": "127.0.0.1",
      "port": 2881,
      "user": "root@test",
      "password": "your_password",
      "db_name": "powermem",
      "collection_name": "memories",
      "embedding_model_dims": 1024
    }}
  Lưu ý:
    - collection_name: Tên bảng mặc định, nếu tạo sai chiều hãy xóa bảng này hoặc đổi tên
    - embedding_model_dims: Chiều vector embedding, cần khớp với chiều mô hình embedder
      Ví dụ Trí Phổ: embedding-2 có chiều là 1024, embedding-3 có chiều là 2048

【Các cấu hình được khuyến nghị】
1. Giải pháp hoàn toàn miễn phí:
   - LLM: zhipu + glm-4-flash (miễn phí)
   - Embedder: Thông Nghĩa Thiên Vấn text-embedding-v4
   - Database: sqlite

2. Giải pháp môi trường production:
   - LLM: qwen-plus hoặc mô hình thương mại khác
   - Embedder: text-embedding-v4
   - Database: oceanbase hoặc seekdb
'
WHERE `id` = 'Memory_powermem';
