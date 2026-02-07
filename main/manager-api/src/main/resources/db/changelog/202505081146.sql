-- Thêm cấu hình mô hình ASR Baidu
delete from `ai_model_config` where `id` = 'ASR_BaiduASR';
INSERT INTO `ai_model_config` VALUES ('ASR_BaiduASR', 'ASR', 'BaiduASR', 'Nhận dạng giọng nói Baidu', 0, 1, '{\"type\": \"baidu\", \"app_id\": \"\", \"api_key\": \"\", \"secret_key\": \"\", \"dev_pid\": 1537, \"output_dir\": \"tmp/\"}', NULL, NULL, 7, NULL, NULL, NULL, NULL);


-- Thêm nhà cung cấp ASR Baidu
delete from `ai_model_provider` where `id` = 'SYSTEM_ASR_BaiduASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_BaiduASR', 'ASR', 'baidu', 'Nhận dạng giọng nói Baidu', '[{"key":"app_id","label":"AppID ứng dụng","type":"string"},{"key":"api_key","label":"API Key","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"dev_pid","label":"Tham số ngôn ngữ","type":"number"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]', 7, 1, NOW(), 1, NOW());


-- Cập nhật hướng dẫn cấu hình ASR Baidu
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.bce.baidu.com/ai-engine/old/#/ai/speech/app/list',
`remark` = 'Hướng dẫn cấu hình ASR Baidu:
1. Truy cập https://console.bce.baidu.com/ai-engine/old/#/ai/speech/app/list
2. Tạo ứng dụng mới
3. Lấy AppID, API Key và Secret Key
4. Điền vào file cấu hình
Xem hạn mức tài nguyên: https://console.bce.baidu.com/ai-engine/old/#/ai/speech/overview/resource/list
Giải thích tham số ngôn ngữ: https://ai.baidu.com/ai-doc/SPEECH/0lbxfnc9b
' WHERE `id` = 'ASR_BaiduASR';

-- Cập nhật trường nhà cung cấp Đậu Bao
update `ai_model_provider` set `fields` = 
'[{"key":"appid","label":"ID ứng dụng","type":"string"},{"key":"access_token","label":"Mã truy cập","type":"string"},{"key":"cluster","label":"Cụm","type":"string"},{"key":"boosting_table_name","label":"Tên file từ nóng","type":"string"},{"key":"correct_table_name","label":"Tên file từ thay thế","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]'
where `id` = 'SYSTEM_ASR_DoubaoASR';

-- Cập nhật hướng dẫn cấu hình ASR Đậu Bao
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = 'Hướng dẫn cấu hình ASR Đậu Bao:
1. Cần tạo ứng dụng trên bảng điều khiển Huoshan Engine và lấy appid và access_token
2. Hỗ trợ nhận dạng giọng nói tiếng Trung
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://console.volcengine.com/speech/app
2. Tạo ứng dụng mới
3. Lấy appid và access_token
4. Điền vào file cấu hình
Nếu cần cài đặt từ nóng, vui lòng tham khảo: https://www.volcengine.com/docs/6561/155738
' WHERE `id` = 'ASR_DoubaoASR';