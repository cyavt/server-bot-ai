-- Sửa đổi tham số trước phiên bản 0.3.0
update `sys_params` set param_value = '.mp3;.wav;.p3' where  param_code = 'plugins.play_music.music_ext';
update `ai_model_config` set config_json =  '{\"type\": \"intent_llm\", \"llm\": \"LLM_ChatGLMLLM\"}' where  id = 'Intent_intent_llm';

-- Đảm bảo cột name đủ lớn trước khi insert dữ liệu
-- Sửa đổi cột name từ VARCHAR(20) lên VARCHAR(255) để chứa tên giọng dài
ALTER TABLE `ai_tts_voice` MODIFY COLUMN `name` VARCHAR(255) COMMENT 'Tên giọng';

-- Thêm giọng edge
delete from `ai_tts_voice` where tts_model_id = 'TTS_EdgeTTS';
INSERT INTO `ai_tts_voice` VALUES 
('TTS_EdgeTTS0001', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ - Tiểu Tiểu', 'zh-CN-XiaoxiaoNeural', 'Tiếng Quan Thoại', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0002', 'TTS_EdgeTTS', 'EdgeTTS giọng nam - Vân Dương', 'zh-CN-YunyangNeural', 'Tiếng Quan Thoại', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0003', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ - Tiểu Y', 'zh-CN-XiaoyiNeural', 'Tiếng Quan Thoại', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0004', 'TTS_EdgeTTS', 'EdgeTTS giọng nam - Vân Kiện', 'zh-CN-YunjianNeural', 'Tiếng Quan Thoại', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0005', 'TTS_EdgeTTS', 'EdgeTTS giọng nam - Vân Hy', 'zh-CN-YunxiNeural', 'Tiếng Quan Thoại', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0006', 'TTS_EdgeTTS', 'EdgeTTS giọng nam - Vân Hạ', 'zh-CN-YunxiaNeural', 'Tiếng Quan Thoại', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0007', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ - Liêu Ninh Tiểu Bối', 'zh-CN-liaoning-XiaobeiNeural', 'Liêu Ninh', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0008', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ - Thiểm Tây Tiểu Nê', 'zh-CN-shaanxi-XiaoniNeural', 'Thiểm Tây', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0009', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ - Hồng Kông Hải Giai', 'zh-HK-HiuGaaiNeural', 'Tiếng Quảng Đông', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0010', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ - Hồng Kông Hải Mạn', 'zh-HK-HiuMaanNeural', 'Tiếng Quảng Đông', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0011', 'TTS_EdgeTTS', 'EdgeTTS giọng nam - Hồng Kông Vạn Long', 'zh-HK-WanLungNeural', 'Tiếng Quảng Đông', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL);

-- Thêm tham số cho phép người dùng đăng ký
delete from `sys_params` where  id in (103,104);
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (103, 'server.allow_user_register', 'false', 'boolean', 1, 'Có cho phép người khác ngoài quản trị viên đăng ký không');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (104, 'server.fronted_url', 'http://xiaozhi.server.com', 'string', 1, 'Địa chỉ bảng điều khiển hiển thị khi gửi mã xác minh sáu chữ số');

-- Sửa giọng CosyVoiceSiliconflow
delete from `ai_tts_voice` where tts_model_id = 'TTS_CosyVoiceSiliconflow';
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow', 'CosyVoice giọng nam', 'FunAudioLLM/CosyVoice2-0.5B:alex', 'Tiếng Trung', 'https://example.com/cosyvoice/alex.mp3', NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0002', 'TTS_CosyVoiceSiliconflow', 'CosyVoice giọng nữ', 'FunAudioLLM/CosyVoice2-0.5B:bella', 'Tiếng Trung', 'https://example.com/cosyvoice/bella.mp3', NULL, 6, NULL, NULL, NULL, NULL);
