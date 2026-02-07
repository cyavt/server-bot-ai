-- Provider mô hình VLLM
delete from `ai_model_provider` where id = 'SYSTEM_VLLM_openai';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_VLLM_openai', 'VLLM', 'openai', 'Giao diện OpenAI', '[{"key":"base_url","label":"URL cơ sở","type":"string"},{"key":"model_name","label":"Tên mô hình","type":"string"},{"key":"api_key","label":"Khóa API","type":"string"}]', 9, 1, NOW(), 1, NOW());

-- Cấu hình mô hình VLLM
delete from `ai_model_config` where id = 'VLLM_ChatGLMVLLM';
INSERT INTO `ai_model_config` VALUES ('VLLM_ChatGLMVLLM', 'VLLM', 'ChatGLMVLLM', 'AI thị giác Trí Phổ', 1, 1, '{\"type\": \"openai\", \"model_name\": \"glm-4v-flash\", \"base_url\": \"https://open.bigmodel.cn/api/paas/v4/\", \"api_key\": \"api_key của bạn\"}', NULL, NULL, 1, NULL, NULL, NULL, NULL);

-- Cập nhật tài liệu
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys',
`remark` = 'Hướng dẫn cấu hình AI thị giác Trí Phổ：
1. Truy cập https://bigmodel.cn/usercenter/proj-mgmt/apikeys
2. Đăng ký và lấy khóa API
3. Điền vào file cấu hình' WHERE `id` = 'VLLM_ChatGLMVLLM';


-- Thêm tham số
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (113, 'server.http_port', '8003', 'number', 1, 'Cổng dịch vụ http, dùng để khởi động giao diện phân tích thị giác');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (114, 'server.vision_explain', 'null', 'string', 1, 'Địa chỉ giao diện phân tích thị giác, dùng để gửi xuống thiết bị, nhiều địa chỉ dùng ; phân cách');

-- Bảng agent thêm cấu hình mô hình VLLM
ALTER TABLE `ai_agent` 
ADD COLUMN `vllm_model_id` varchar(32) NULL DEFAULT 'VLLM_ChatGLMVLLM' COMMENT 'Định danh mô hình thị giác' AFTER `llm_model_id`;

-- Bảng template agent thêm cấu hình mô hình VLLM
ALTER TABLE `ai_agent_template` 
ADD COLUMN `vllm_model_id` varchar(32) NULL DEFAULT 'VLLM_ChatGLMVLLM' COMMENT 'Định danh mô hình thị giác' AFTER `llm_model_id`;