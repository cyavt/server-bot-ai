-- Thêm provider TTS streaming Alibaba Bách Luyện
delete from `ai_model_provider` where id = 'SYSTEM_TTS_AliBLStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_AliBLStreamTTS', 'TTS', 'alibl_stream', 'Tổng hợp giọng nói streaming Alibaba Bách Luyện', '[{"key":"api_key","label":"Khóa API","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"},{"key":"model","label":"Mô hình","type":"string"},{"key":"voice","label":"Giọng","type":"string"},{"key":"format","label":"Định dạng âm thanh","type":"string"},{"key":"sample_rate","label":"Tần số lấy mẫu","type":"number"},{"key": "volume", "type": "number", "label": "Âm lượng"},{"key": "rate", "type": "number", "label": "Tốc độ nói"},{"key": "pitch", "type": "number", "label": "Độ cao giọng"}]', 19, 1, NOW(), 1, NOW());

-- Thêm cấu hình mô hình TTS streaming Alibaba Bách Luyện
delete from `ai_model_config` where id = 'TTS_AliBLStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_AliBLStreamTTS', 'TTS', 'AliBLStreamTTS', 'Tổng hợp giọng nói streaming Alibaba Bách Luyện', 0, 1, '{\"type\": \"alibl_stream\", \"appkey\": \"\", \"output_dir\": \"tmp/\", \"model\": \"cosyvoice-v2\", \"voice\": \"longcheng_v2\", \"format\": \"pcm\", \"sample_rate\": 24000, \"volume\": 50, \"rate\": 1, \"pitch\": 1}', NULL, NULL, 22, NULL, NULL, NULL, NULL);

-- Cập nhật hướng dẫn cấu hình TTS streaming Alibaba Bách Luyện
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
`remark` = 'Hướng dẫn TTS streaming Alibaba Bách Luyện：
1. Truy cập https://bailian.console.aliyun.com/?apiKey=1#/api-key để tạo dự án và lấy appkey
2. Hỗ trợ tổng hợp streaming thời gian thực, có độ trễ thấp
3. Hỗ trợ thiết lập nhiều giọng và điều chỉnh tham số âm thanh
4. Hỗ trợ giọng mô hình lớn CosyVoice-V3, giá cả hợp lý (0.4 nhân dân tệ/10 nghìn ký tự)
5. Hỗ trợ điều chỉnh thời gian thực âm lượng, tốc độ nói, độ cao giọng và các tham số khác
6. Nếu cần sử dụng mô hình CosyVoice-V3 và một số loại giọng bị hạn chế, cần liên hệ dịch vụ khách hàng Alibaba Bách Luyện để đăng ký
' WHERE `id` = 'TTS_AliBLStreamTTS';

-- Thêm giọng TTS streaming Alibaba Bách Luyện
delete from `ai_tts_voice` where tts_model_id = 'TTS_AliBLStreamTTS';

-- Trợ lý giọng nói
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0001', 'TTS_AliBLStreamTTS', 'Long Tiểu Thuần - Nữ tri thức tích cực', 'longxiaochun_v2', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0002', 'TTS_AliBLStreamTTS', 'Long Tiểu Hạ - Nữ uy quyền điềm đạm', 'longxiaoxia_v2', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 2, NULL, NULL, NULL, NULL);

-- Bán hàng trực tiếp
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0003', 'TTS_AliBLStreamTTS', 'Long An Nhiên - Nữ hoạt bát có chất lượng', 'longanran', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0004', 'TTS_AliBLStreamTTS', 'Long An Tuyên - Nữ livestream kinh điển', 'longanxuan', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 4, NULL, NULL, NULL, NULL);

-- Đồng hành xã hội
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0005', 'TTS_AliBLStreamTTS', 'Long Hàn - Nam ấm áp si tình', 'longhan_v2', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0006', 'TTS_AliBLStreamTTS', 'Long Nhan - Nữ ấm áp như gió xuân', 'longyan_v2', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0007', 'TTS_AliBLStreamTTS', 'Long Phi Phi - Nữ ngọt ngào làm dáng', 'longfeifei_v2', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 7, NULL, NULL, NULL, NULL);

-- Phương ngữ
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0008', 'TTS_AliBLStreamTTS', 'Long Lão Thiết - Nam Đông Bắc thẳng thắn', 'longlaotie_v2', 'Tiếng Trung (Đông Bắc) và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0009', 'TTS_AliBLStreamTTS', 'Long Gia Di - Nữ tri thức Quảng Đông', 'longjiayi_v2', 'Tiếng Trung (Quảng Đông) và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 9, NULL, NULL, NULL, NULL);

-- Giọng trẻ em
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0010', 'TTS_AliBLStreamTTS', 'Long Kiệt Lực Đậu - Nam nghịch ngợm tươi sáng', 'longjielidou_v2', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 10, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0011', 'TTS_AliBLStreamTTS', 'Long Linh - Nữ ngây thơ cứng nhắc', 'longling_v2', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 11, NULL, NULL, NULL, NULL);

-- Đọc thơ
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0012', 'TTS_AliBLStreamTTS', 'Lý Bạch - Nam tiên thơ cổ đại', 'libai_v2', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 12, NULL, NULL, NULL, NULL);

-- Marketing xuất khẩu
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0013', 'TTS_AliBLStreamTTS', 'loongeva - Nữ tiếng Anh tri thức', 'loongeva_v2', 'Tiếng Anh Anh', NULL, NULL, NULL, NULL, 13, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0014', 'TTS_AliBLStreamTTS', 'loongbrian - Nam tiếng Anh điềm đạm', 'loongbrian_v2', 'Tiếng Anh Anh', NULL, NULL, NULL, NULL, 14, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0015', 'TTS_AliBLStreamTTS', 'loongkyong - Nữ tiếng Hàn', 'loongkyong_v2', 'Tiếng Hàn', NULL, NULL, NULL, NULL, 15, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0016', 'TTS_AliBLStreamTTS', 'loongtomoka - Nữ tiếng Nhật', 'loongtomoka_v2', 'Tiếng Nhật', NULL, NULL, NULL, NULL, 16, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0017', 'TTS_AliBLStreamTTS', 'loongtomoya - Nam tiếng Nhật', 'loongtomoya_v2', 'Tiếng Nhật', NULL, NULL, NULL, NULL, 17, NULL, NULL, NULL, NULL);