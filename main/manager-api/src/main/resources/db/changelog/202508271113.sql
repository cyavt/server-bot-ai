-- Provider mô hình ASR VOSK
delete from `ai_model_provider` where id = 'SYSTEM_ASR_VoskASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_VoskASR', 'ASR', 'vosk', 'Nhận dạng giọng nói offline VOSK', '[{"key": "model_path", "type": "string", "label": "Đường dẫn mô hình"}, {"key": "output_dir", "type": "string", "label": "Thư mục đầu ra"}]', 11, 1, NOW(), 1, NOW());

-- Cấu hình mô hình ASR VOSK
delete from `ai_model_config` where id = 'ASR_VoskASR';
INSERT INTO `ai_model_config` VALUES ('ASR_VoskASR', 'ASR', 'VoskASR', 'Nhận dạng giọng nói offline VOSK', 0, 1, '{\"type\": \"vosk\", \"model_path\": \"\", \"output_dir\": \"tmp/\"}', NULL, NULL, 11, NULL, NULL, NULL, NULL);

-- Cập nhật hướng dẫn cấu hình ASR VOSK
UPDATE `ai_model_config` SET 
`doc_link` = 'https://alphacephei.com/vosk/',
`remark` = 'Hướng dẫn cấu hình ASR VOSK：
1. VOSK là thư viện nhận dạng giọng nói offline, hỗ trợ nhiều ngôn ngữ
2. Cần tải file mô hình trước：https://alphacephei.com/vosk/models
3. Mô hình tiếng Trung khuyến nghị sử dụng vosk-model-small-cn-0.22 hoặc vosk-model-cn-0.22
4. Chạy hoàn toàn offline, không cần kết nối mạng
5. File đầu ra được lưu trong thư mục tmp/
Các bước sử dụng：
1. Truy cập https://alphacephei.com/vosk/models để tải mô hình tiếng Trung
2. Giải nén file mô hình vào thư mục models/vosk/ trong thư mục dự án
3. Chỉ định đường dẫn mô hình đúng trong cấu hình
4. Lưu ý：Mô hình tiếng Trung VOSK đầu ra không có dấu câu, giữa các từ sẽ có khoảng trắng
' WHERE `id` = 'ASR_VoskASR';