-- Thêm cấu hình dịch vụ nhận dạng giọng nói Qwen3-ASR-Flash Thông Nghĩa Thiên Vấn
delete from `ai_model_provider` where id = 'SYSTEM_ASR_Qwen3Flash';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_Qwen3Flash', 'ASR', 'qwen3_asr_flash', 'Nhận dạng giọng nói Qwen3-ASR-Flash', '[{"key":"api_key","label":"Khóa API","type":"password"},{"key":"base_url","label":"Địa chỉ dịch vụ","type":"string"},{"key":"model_name","label":"Tên mô hình","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]', 17, 1, NOW(), 1, NOW());

delete from `ai_model_config` where id = 'ASR_Qwen3Flash';
INSERT INTO `ai_model_config` VALUES ('ASR_Qwen3Flash', 'ASR', 'Qwen3-ASR-Flash', 'Dịch vụ nhận dạng giọng nói Thông Nghĩa Thiên Vấn', 0, 1, '{"type": "qwen3_asr_flash", "api_key": "", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model_name": "qwen3-asr-flash", "output_dir": "tmp/", "enable_lid": true, "enable_itn": true}', 'https://help.aliyun.com/zh/bailian/', 'Hỗ trợ nhận dạng đa ngôn ngữ, nhận dạng hát, chức năng từ chối tiếng ồn', 20, NULL, NULL, NULL, NULL);

-- Cập nhật tài liệu hướng dẫn cấu hình mô hình Qwen3-ASR-Flash
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?apiKey=1&tab=doc#/doc/?type=model&url=2979031',
`remark` = 'Hướng dẫn cấu hình Qwen3-ASR-Flash Thông Nghĩa Thiên Vấn：
1. Đăng nhập nền tảng Alibaba Bách Luyện https://bailian.console.aliyun.com/
2. Tạo API-KEY  https://bailian.console.aliyun.com/#/api-key
3.Qwen3-ASR-Flash dựa trên nền tảng đa phương thức Thông Nghĩa Thiên Vấn, hỗ trợ nhận dạng đa ngôn ngữ, nhận dạng hát, từ chối tiếng ồn và các chức năng khác
' WHERE `id` = 'ASR_Qwen3Flash';
