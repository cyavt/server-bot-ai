-- Thêm provider TTS streaming Tín Phi
delete from `ai_model_provider` where id = 'SYSTEM_TTS_XunFeiStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_XunFeiStreamTTS', 'TTS', 'xunfei_stream', 'Tổng hợp giọng nói streaming Tín Phi', '[{"key":"app_id","label":"APP_ID","type":"string"},{"key":"api_secret","label":"API_Secret","type":"string"},{"key":"api_key","label":"Khóa API","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"},{"key":"voice","label":"Giọng","type":"string"},{"key":"format","label":"Định dạng âm thanh","type":"string"},{"key":"sample_rate","label":"Tần số lấy mẫu","type":"number"},{"key": "volume", "type": "number", "label": "Âm lượng"},{"key": "speed", "type": "number", "label": "Tốc độ nói"},{"key": "pitch", "type": "number", "label": "Độ cao giọng"},{"key": "oral_level", "type": "number", "label": "Cấp độ khẩu ngữ"},{"key": "spark_assist", "type": "number", "label": "Có khẩu ngữ không"},{"key": "stop_split", "type": "number", "label": "Tách câu phía server"},{"key": "remain", "type": "number", "label": "Giữ lại ngôn ngữ viết"}]', 20, 1, NOW(), 1, NOW());

-- Thêm cấu hình mô hình TTS streaming Tín Phi
delete from `ai_model_config` where id = 'TTS_XunFeiStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_XunFeiStreamTTS', 'TTS', 'XunFeiStreamTTS', 'Tổng hợp giọng nói streaming Tín Phi', 0, 1, '{\"type\": \"xunfei_stream\", \"app_id\": \"\", \"api_secret\": \"\", \"api_key\": \"\", \"output_dir\": \"tmp/\", \"voice\": \"x5_lingxiaoxuan_flow\", \"format\": \"raw\", \"sample_rate\": 24000, \"volume\": 50, \"speed\": 50, \"pitch\": 50, \"oral_level\": \"mid\", \"spark_assist\": 1, \"stop_split\": 0, \"remain\": 0}', NULL, NULL, 23, NULL, NULL, NULL, NULL);

-- Cập nhật hướng dẫn cấu hình TTS streaming Tín Phi
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.xfyun.cn/app/myapp',
`remark` = 'Hướng dẫn TTS streaming Tín Phi：
1. Đăng nhập nền tảng công nghệ giọng nói Tín Phi https://console.xfyun.cn/app/myapp để tạo ứng dụng liên quan
2. Chọn dịch vụ cần thiết để lấy cấu hình api liên quan https://console.xfyun.cn/services/uts
3. Mua dịch vụ liên quan cho ứng dụng cần sử dụng (APPID) Ví dụ：Tổng hợp siêu giống người https://console.xfyun.cn/services/uts
5. Hỗ trợ giao tiếp streaming hai chiều thời gian thực, có độ trễ thấp
6. Hỗ trợ thiết lập khẩu ngữ và điều chỉnh tham số âm thanh Lưu ý：Giọng V5 không hỗ trợ cấu hình khẩu ngữ liên quan
7. Hỗ trợ điều chỉnh thời gian thực âm lượng, tốc độ nói, độ cao giọng và các tham số khác
' WHERE `id` = 'TTS_XunFeiStreamTTS';

-- Thêm giọng TTS streaming Tín Phi
delete from `ai_tts_voice` where tts_model_id = 'TTS_XunFeiStreamTTS';

-- Vai trò cơ bản
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0001', 'TTS_XunFeiStreamTTS', 'Linh Tiểu Tuyền', 'x5_lingxiaoxuan_flow', 'Tiếng Trung', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0002', 'TTS_XunFeiStreamTTS', 'Linh Phi Dật', 'x5_lingfeiyi_flow', 'Tiếng Trung', NULL, NULL, NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0003', 'TTS_XunFeiStreamTTS', 'Linh Tiểu Nguyệt', 'x5_lingxiaoyue_flow', 'Tiếng Trung', NULL, NULL, NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0004', 'TTS_XunFeiStreamTTS', 'Linh Ngọc Chiêu', 'x5_lingyuzhao_flow', 'Tiếng Trung', NULL, NULL, NULL, NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0005', 'TTS_XunFeiStreamTTS', 'Linh Ngọc Ngôn', 'x5_lingyuyan_flow', 'Tiếng Trung', NULL, NULL, NULL, NULL, 5, NULL, NULL, NULL, NULL);

-- Cần thêm giọng vai trò tương ứng
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0006', 'TTS_XunFeiStreamTTS', 'Linh Phi Triết', 'x4_lingfeizhe_oral', 'Tiếng Trung', NULL, NULL, NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0007', 'TTS_XunFeiStreamTTS', 'Linh Tiểu Ly', 'x4_lingxiaoli_oral', 'Tiếng Trung', NULL, NULL, NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0008', 'TTS_XunFeiStreamTTS', 'Linh Tiểu Đường', 'x5_lingxiaotang_flow', 'Tiếng Trung', NULL, NULL, NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0009', 'TTS_XunFeiStreamTTS', 'Linh Tiểu Kỳ', 'x4_lingxiaoqi_oral', 'Tiếng Trung', NULL, NULL, NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0010', 'TTS_XunFeiStreamTTS', 'Linh Hữu Hữu - Giọng nữ tuổi thơ', 'x4_lingyouyou_oral', 'Tiếng Trung', NULL, NULL, NULL, NULL, 10, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0011', 'TTS_XunFeiStreamTTS', 'Tử Tân', 'x4_zijin_oral', 'Tiếng Thiên Tân', NULL, NULL, NULL, NULL, 11, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0012', 'TTS_XunFeiStreamTTS', 'Tử Dương', 'x4_ziyang_oral', 'Tiếng Đông Bắc', NULL, NULL, NULL, NULL, 12, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0013', 'TTS_XunFeiStreamTTS', 'Grant', 'x5_EnUs_Grant_flow', 'Tiếng Anh', NULL, NULL, NULL, NULL, 13, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_XunFeiStreamTTS_0014', 'TTS_XunFeiStreamTTS', 'Lila', 'x5_EnUs_Lila_flow', 'Tiếng Anh', NULL, NULL, NULL, NULL, 14, NULL, NULL, NULL, NULL);
