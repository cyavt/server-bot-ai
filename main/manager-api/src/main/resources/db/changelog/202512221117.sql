-- Cập nhật provider ASR streaming Đậu Bao, thêm cấu hình end_window_size
delete from `ai_model_provider` where id = 'SYSTEM_ASR_DoubaoStreamASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_DoubaoStreamASR', 'ASR', 'doubao_stream', 'Nhận dạng giọng nói Núi Lửa (streaming)', '[{"key":"appid","label":"ID ứng dụng","type":"string"},{"key":"access_token","label":"Token truy cập","type":"string"},{"key":"cluster","label":"Cluster","type":"string"},{"key":"boosting_table_name","label":"Tên file từ khóa","type":"string"},{"key":"correct_table_name","label":"Tên file từ thay thế","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"},{"key":"end_window_size","label":"Thời lượng phán đoán im lặng (ms)","type":"number"}]', 3, 1, NOW(), 1, NOW());


-- Cập nhật cấu hình mô hình ASR streaming Đậu Bao, thêm giá trị mặc định end_window_size
UPDATE `ai_model_config` SET
`config_json` = JSON_SET(`config_json`, '$.end_window_size', 200)
WHERE `id` = 'ASR_DoubaoStreamASR' AND JSON_EXTRACT(`config_json`, '$.end_window_size') IS NULL;
