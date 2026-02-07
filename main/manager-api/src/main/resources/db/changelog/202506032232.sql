-- Cấu hình mô hình VLLM
delete from `ai_model_config` where id = 'VLLM_QwenVLVLLM';
INSERT INTO `ai_model_config` VALUES ('VLLM_QwenVLVLLM', 'VLLM', 'QwenVLVLLM', 'Mô hình thị giác Thiên Vấn', 0, 1, '{\"type\": \"openai\", \"model_name\": \"qwen2.5-vl-3b-instruct\", \"base_url\": \"https://dashscope.aliyuncs.com/compatible-mode/v1\", \"api_key\": \"api_key của bạn\"}', NULL, NULL, 2, NULL, NULL, NULL, NULL);

-- Cập nhật tài liệu
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F2845564.html&renderType=iframe',
`remark` = 'Hướng dẫn cấu hình mô hình thị giác Thiên Vấn：
1. Truy cập https://bailian.console.aliyun.com/?tab=model#/api-key
2. Đăng ký và lấy khóa API
3. Điền vào file cấu hình' WHERE `id` = 'VLLM_QwenVLVLLM';

-- Xóa tham số, hai tham số này đã được chuyển sang file cấu hình python
delete from `sys_params` where id  in (113,114);
