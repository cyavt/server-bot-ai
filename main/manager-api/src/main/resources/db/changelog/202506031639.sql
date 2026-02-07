-- Provider mô hình VLLM
delete from `ai_model_provider` where id = 'SYSTEM_ASR_DoubaoStreamASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_DoubaoStreamASR', 'ASR', 'doubao_stream', 'Nhận dạng giọng nói Núi Lửa (streaming)', '[{"key":"appid","label":"ID ứng dụng","type":"string"},{"key":"access_token","label":"Token truy cập","type":"string"},{"key":"cluster","label":"Cluster","type":"string"},{"key":"boosting_table_name","label":"Tên file từ khóa","type":"string"},{"key":"correct_table_name","label":"Tên file từ thay thế","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]', 3, 1, NOW(), 1, NOW());


-- Cấu hình mô hình VLLM
delete from `ai_model_config` where id = 'ASR_DoubaoStreamASR';
INSERT INTO `ai_model_config` VALUES ('ASR_DoubaoStreamASR', 'ASR', 'DoubaoStreamASR', 'Nhận dạng giọng nói Đậu Bao (streaming)', 0, 1, '{\"type\": \"doubao_stream\", \"appid\": \"\", \"access_token\": \"\", \"cluster\": \"volcengine_input_common\", \"output_dir\": \"tmp/\"}', NULL, NULL, 3, NULL, NULL, NULL, NULL);


-- Cập nhật hướng dẫn cấu hình ASR Đậu Bao
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = 'Hướng dẫn cấu hình ASR Đậu Bao：
1. Sự khác biệt giữa ASR Đậu Bao và ASR Đậu Bao (streaming) là：ASR Đậu Bao tính phí theo lần, ASR Đậu Bao (streaming) tính phí theo thời gian
2. Nói chung tính phí theo lần rẻ hơn, nhưng ASR Đậu Bao (streaming) sử dụng công nghệ mô hình lớn, hiệu quả tốt hơn
3. Cần tạo ứng dụng trong bảng điều khiển Núi Lửa và lấy appid và access_token
4. Hỗ trợ nhận dạng giọng nói tiếng Trung
5. Cần kết nối mạng
6. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký：
1. Truy cập https://console.volcengine.com/speech/app
2. Tạo ứng dụng mới
3. Lấy appid và access_token
4. Điền vào file cấu hình
Nếu cần thiết lập từ khóa, tham khảo：https://www.volcengine.com/docs/6561/155738
' WHERE `id` = 'ASR_DoubaoASR';

UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = 'Hướng dẫn cấu hình ASR Đậu Bao：
1. Sự khác biệt giữa ASR Đậu Bao và ASR Đậu Bao (streaming) là：ASR Đậu Bao tính phí theo lần, ASR Đậu Bao (streaming) tính phí theo thời gian
2. Nói chung tính phí theo lần rẻ hơn, nhưng ASR Đậu Bao (streaming) sử dụng công nghệ mô hình lớn, hiệu quả tốt hơn
3. Cần tạo ứng dụng trong bảng điều khiển Núi Lửa và lấy appid và access_token
4. Hỗ trợ nhận dạng giọng nói tiếng Trung
5. Cần kết nối mạng
6. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký：
1. Truy cập https://console.volcengine.com/speech/app
2. Tạo ứng dụng mới
3. Lấy appid và access_token
4. Điền vào file cấu hình
Nếu cần thiết lập từ khóa, tham khảo：https://www.volcengine.com/docs/6561/155738
' WHERE `id` = 'ASR_DoubaoStreamASR';
