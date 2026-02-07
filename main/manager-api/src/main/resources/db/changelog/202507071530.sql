-- Thêm provider TTS streaming Alibaba Cloud
delete from `ai_model_provider` where id = 'SYSTEM_TTS_AliyunStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_AliyunStreamTTS', 'TTS', 'aliyun_stream', 'Tổng hợp giọng nói Alibaba Cloud (streaming)', '[{"key":"appkey","label":"AppKey ứng dụng","type":"string"},{"key":"token","label":"Token tạm thời","type":"string"},{"key":"access_key_id","label":"AccessKey ID","type":"string"},{"key":"access_key_secret","label":"AccessKey Secret","type":"string"},{"key":"host","label":"Địa chỉ dịch vụ","type":"string"},{"key":"voice","label":"Giọng mặc định","type":"string"},{"key":"format","label":"Định dạng âm thanh","type":"string"},{"key":"sample_rate","label":"Tần số lấy mẫu","type":"number"},{"key":"volume","label":"Âm lượng","type":"number"},{"key":"speech_rate","label":"Tốc độ nói","type":"number"},{"key":"pitch_rate","label":"Độ cao giọng","type":"number"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]', 15, 1, NOW(), 1, NOW());

-- Thêm cấu hình mô hình TTS streaming Alibaba Cloud
delete from `ai_model_config` where id = 'TTS_AliyunStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_AliyunStreamTTS', 'TTS', 'AliyunStreamTTS', 'Tổng hợp giọng nói Alibaba Cloud (streaming)', 0, 1, '{\"type\": \"aliyun_stream\", \"appkey\": \"\", \"token\": \"\", \"access_key_id\": \"\", \"access_key_secret\": \"\", \"host\": \"nls-gateway-cn-beijing.aliyuncs.com\", \"voice\": \"longxiaochun\", \"format\": \"pcm\", \"sample_rate\": 16000, \"volume\": 50, \"speech_rate\": 0, \"pitch_rate\": 0, \"output_dir\": \"tmp/\"}', NULL, NULL, 18, NULL, NULL, NULL, NULL);

-- Cập nhật hướng dẫn cấu hình TTS streaming Alibaba Cloud
UPDATE `ai_model_config` SET 
`doc_link` = 'https://nls-portal.console.aliyun.com/',
`remark` = 'Hướng dẫn cấu hình TTS streaming Alibaba Cloud：
1. Sự khác biệt giữa TTS Alibaba Cloud và TTS Alibaba Cloud (streaming) là：TTS Alibaba Cloud là tổng hợp một lần, TTS Alibaba Cloud (streaming) là tổng hợp streaming thời gian thực
2. TTS streaming có độ trễ thấp hơn và tính thời gian thực tốt hơn, phù hợp với các tình huống tương tác giọng nói
3. Cần tạo ứng dụng trong bảng điều khiển tương tác giọng nói thông minh Alibaba Cloud và lấy thông tin xác thực
4. Hỗ trợ giọng mô hình lớn CosyVoice, chất lượng âm thanh tự nhiên hơn
5. Hỗ trợ điều chỉnh thời gian thực âm lượng, tốc độ nói, độ cao giọng và các tham số khác
Các bước đăng ký：
1. Truy cập https://nls-portal.console.aliyun.com/ để mở dịch vụ tương tác giọng nói thông minh
2. Truy cập https://nls-portal.console.aliyun.com/applist để tạo dự án và lấy appkey
3. Truy cập https://nls-portal.console.aliyun.com/overview để lấy token tạm thời (hoặc cấu hình access_key_id và access_key_secret để tự động lấy)
4. Nếu cần quản lý token động, khuyến nghị cấu hình access_key_id và access_key_secret
5. Có thể chọn máy chủ ở các khu vực khác nhau như Bắc Kinh, Thượng Hải để tối ưu độ trễ
6. Tham số voice hỗ trợ giọng mô hình lớn CosyVoice, như longxiaochun、longyueyue, v.v.
Nếu cần tìm hiểu thêm cấu hình tham số, tham khảo：https://help.aliyun.com/zh/isi/developer-reference/real-time-speech-synthesis
' WHERE `id` = 'TTS_AliyunStreamTTS';

-- Thêm giọng TTS streaming Alibaba Cloud
delete from `ai_tts_voice` where tts_model_id = 'TTS_AliyunStreamTTS';
-- Dòng giọng nữ dịu dàng
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0001', 'TTS_AliyunStreamTTS', 'Long Tiểu Thuần - Chị gái dịu dàng', 'longxiaochun', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0002', 'TTS_AliyunStreamTTS', 'Long Tiểu Hạ - Giọng nữ dịu dàng', 'longxiaoxia', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0003', 'TTS_AliyunStreamTTS', 'Long Mai - Giọng nữ dịu dàng', 'longmei', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0004', 'TTS_AliyunStreamTTS', 'Long Quỳ - Giọng nữ dịu dàng', 'longgui', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 4, NULL, NULL, NULL, NULL);
-- Dòng giọng nữ ngự tỷ
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0005', 'TTS_AliyunStreamTTS', 'Long Ngọc - Giọng nữ ngự tỷ', 'longyu', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0006', 'TTS_AliyunStreamTTS', 'Long Kiều - Giọng nữ ngự tỷ', 'longjiao', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 6, NULL, NULL, NULL, NULL);
-- Dòng giọng nam
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0007', 'TTS_AliyunStreamTTS', 'Long Thần - Giọng nam lồng tiếng', 'longchen', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0008', 'TTS_AliyunStreamTTS', 'Long Tu - Giọng nam thanh niên', 'longxiu', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0009', 'TTS_AliyunStreamTTS', 'Long Thành - Giọng nam tươi sáng', 'longcheng', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0010', 'TTS_AliyunStreamTTS', 'Long Triết - Giọng nam trưởng thành', 'longzhe', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 10, NULL, NULL, NULL, NULL);
-- Dòng phát thanh chuyên nghiệp
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0011', 'TTS_AliyunStreamTTS', 'Bella2.0 - Giọng nữ tin tức', 'loongbella', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 11, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0012', 'TTS_AliyunStreamTTS', 'Stella2.0 - Giọng nữ sảng khoái', 'loongstella', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 12, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0013', 'TTS_AliyunStreamTTS', 'Long Thư - Giọng nam tin tức', 'longshu', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 13, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0014', 'TTS_AliyunStreamTTS', 'Long Tĩnh - Giọng nữ nghiêm túc', 'longjing', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 14, NULL, NULL, NULL, NULL);
-- Dòng giọng đặc sắc
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0015', 'TTS_AliyunStreamTTS', 'Long Kỳ - Giọng trẻ em hoạt bát', 'longqi', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 15, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0016', 'TTS_AliyunStreamTTS', 'Long Hoa - Nữ nhi hoạt bát', 'longhua', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 16, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0017', 'TTS_AliyunStreamTTS', 'Long Vô - Giọng nam vô lý', 'longwu', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 17, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0018', 'TTS_AliyunStreamTTS', 'Long Đại Chùy - Giọng nam hài hước', 'longdachui', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 18, NULL, NULL, NULL, NULL);
-- Dòng tiếng Quảng Đông
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0019', 'TTS_AliyunStreamTTS', 'Long Gia Di - Giọng nữ Quảng Đông', 'longjiayi', 'Quảng Đông và hỗn hợp Quảng-Anh', NULL, NULL, NULL, NULL, 19, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0020', 'TTS_AliyunStreamTTS', 'Long Đào - Giọng nữ Quảng Đông', 'longtao', 'Quảng Đông và hỗn hợp Quảng-Anh', NULL, NULL, NULL, NULL, 20, NULL, NULL, NULL, NULL);
