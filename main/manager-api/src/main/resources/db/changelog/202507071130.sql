-- Thêm provider ASR streaming Alibaba Cloud
delete from `ai_model_provider` where id = 'SYSTEM_ASR_AliyunStreamASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_AliyunStreamASR', 'ASR', 'aliyun_stream', 'Nhận dạng giọng nói Alibaba Cloud (streaming)', '[{"key":"appkey","label":"AppKey ứng dụng","type":"string"},{"key":"token","label":"Token tạm thời","type":"string"},{"key":"access_key_id","label":"AccessKey ID","type":"string"},{"key":"access_key_secret","label":"AccessKey Secret","type":"string"},{"key":"host","label":"Địa chỉ dịch vụ","type":"string"},{"key":"max_sentence_silence","label":"Thời gian phát hiện ngắt câu","type":"number"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]', 6, 1, NOW(), 1, NOW());

-- Thêm cấu hình mô hình ASR streaming Alibaba Cloud
delete from `ai_model_config` where id = 'ASR_AliyunStreamASR';
INSERT INTO `ai_model_config` VALUES ('ASR_AliyunStreamASR', 'ASR', 'AliyunStreamASR', 'Nhận dạng giọng nói Alibaba Cloud (streaming)', 0, 1, '{\"type\": \"aliyun_stream\", \"appkey\": \"\", \"token\": \"\", \"access_key_id\": \"\", \"access_key_secret\": \"\", \"host\": \"nls-gateway-cn-shanghai.aliyuncs.com\", \"max_sentence_silence\": 800, \"output_dir\": \"tmp/\"}', NULL, NULL, 8, NULL, NULL, NULL, NULL);

-- Cập nhật hướng dẫn cấu hình ASR streaming Alibaba Cloud
UPDATE `ai_model_config` SET 
`doc_link` = 'https://nls-portal.console.aliyun.com/',
`remark` = 'Hướng dẫn cấu hình ASR streaming Alibaba Cloud：
1. Sự khác biệt giữa ASR Alibaba Cloud và ASR Alibaba Cloud (streaming) là：ASR Alibaba Cloud là nhận dạng một lần, ASR Alibaba Cloud (streaming) là nhận dạng streaming thời gian thực
2. ASR streaming có độ trễ thấp hơn và tính thời gian thực tốt hơn, phù hợp với các tình huống tương tác giọng nói
3. Cần tạo ứng dụng trong bảng điều khiển tương tác giọng nói thông minh Alibaba Cloud và lấy thông tin xác thực
4. Hỗ trợ nhận dạng giọng nói thời gian thực tiếng Trung, hỗ trợ dự đoán dấu câu và chuẩn hóa văn bản ngược
5. Cần kết nối mạng, file đầu ra được lưu trong thư mục tmp/
Các bước đăng ký：
1. Truy cập https://nls-portal.console.aliyun.com/ để mở dịch vụ tương tác giọng nói thông minh
2. Truy cập https://nls-portal.console.aliyun.com/applist để tạo dự án và lấy appkey
3. Truy cập https://nls-portal.console.aliyun.com/overview để lấy token tạm thời (hoặc cấu hình access_key_id và access_key_secret để tự động lấy)
4. Nếu cần quản lý token động, khuyến nghị cấu hình access_key_id và access_key_secret
5. Tham số max_sentence_silence điều khiển thời gian phát hiện ngắt câu (mili giây), mặc định 800ms
Nếu cần tìm hiểu thêm cấu hình tham số, tham khảo：https://help.aliyun.com/zh/isi/developer-reference/real-time-speech-recognition
' WHERE `id` = 'ASR_AliyunStreamASR';
