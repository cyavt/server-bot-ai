-- Provider mô hình ASR OpenAI
delete from `ai_model_provider` where id = 'SYSTEM_ASR_OpenaiASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_OpenaiASR', 'ASR', 'openai', 'Nhận dạng giọng nói OpenAI', '[{"key": "base_url", "type": "string", "label": "URL cơ sở"}, {"key": "model_name", "type": "string", "label": "Tên mô hình"}, {"key": "api_key", "type": "string", "label": "Khóa API"}, {"key": "output_dir", "type": "string", "label": "Thư mục đầu ra"}]', 9, 1, NOW(), 1, NOW());


-- Cấu hình mô hình ASR OpenAI
delete from `ai_model_config` where id = 'ASR_OpenaiASR';
INSERT INTO `ai_model_config` VALUES ('ASR_OpenaiASR', 'ASR', 'OpenaiASR', 'Nhận dạng giọng nói OpenAI', 0, 1, '{\"type\": \"openai\", \"api_key\": \"\", \"base_url\": \"https://api.openai.com/v1/audio/transcriptions\", \"model_name\": \"gpt-4o-mini-transcribe\", \"output_dir\": \"tmp/\"}', NULL, NULL, 9, NULL, NULL, NULL, NULL);

-- Cấu hình mô hình ASR Groq
delete from `ai_model_config` where id = 'ASR_GroqASR';
INSERT INTO `ai_model_config` VALUES ('ASR_GroqASR', 'ASR', 'GroqASR', 'Nhận dạng giọng nói Groq', 0, 1, '{\"type\": \"openai\", \"api_key\": \"\", \"base_url\": \"https://api.groq.com/openai/v1/audio/transcriptions\", \"model_name\": \"whisper-large-v3-turbo\", \"output_dir\": \"tmp/\"}', NULL, NULL, 10, NULL, NULL, NULL, NULL);


-- Cập nhật hướng dẫn cấu hình ASR OpenAI
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.openai.com/docs/api-reference/audio/createTranscription',
`remark` = 'Hướng dẫn cấu hình ASR OpenAI：
1. Cần tạo tổ chức trên nền tảng mở OpenAI và lấy api_key
2. Hỗ trợ nhận dạng giọng nói nhiều ngôn ngữ như Trung, Anh, Nhật, Hàn, tham khảo tài liệu https://platform.openai.com/docs/guides/speech-to-text
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký：
**Các bước đăng ký OpenAi ASR：**
1.Đăng nhập OpenAI Platform。https://auth.openai.com/log-in
2.Tạo api-key  https://platform.openai.com/settings/organization/api-keys
3.Mô hình có thể chọn gpt-4o-transcribe hoặc GPT-4o mini Transcribe
' WHERE `id` = 'ASR_OpenaiASR';

-- Cập nhật hướng dẫn cấu hình ASR Groq
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.groq.com/docs/speech-to-text',
`remark` = 'Hướng dẫn cấu hình ASR Groq：
1.Đăng nhập groq Console。https://console.groq.com/home
2.Tạo api-key  https://console.groq.com/keys
3.Mô hình có thể chọn whisper-large-v3-turbo hoặc whisper-large-v3 (distil-whisper-large-v3-en chỉ hỗ trợ phiên âm tiếng Anh)
' WHERE `id` = 'ASR_GroqASR';