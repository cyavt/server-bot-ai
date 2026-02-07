-- Thêm provider và cấu hình mô hình LinkeraiTTS
delete from `ai_model_provider` where id = 'SYSTEM_TTS_LinkeraiTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_LinkeraiTTS', 'TTS', 'linkerai', 'Tổng hợp giọng nói Linkerai', '[{"key":"api_url","label":"Địa chỉ API","type":"string"},{"key":"audio_format","label":"Định dạng âm thanh","type":"string"},{"key":"access_token","label":"Token truy cập","type":"string"},{"key":"voice","label":"Giọng mặc định","type":"string"}]', 14, 1, NOW(), 1, NOW());

delete from `ai_model_config` where id = 'TTS_LinkeraiTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_LinkeraiTTS', 'TTS', 'LinkeraiTTS', 'Tổng hợp giọng nói Linkerai', 0, 1, '{\"type\": \"linkerai\", \"api_url\": \"https://tts.linkerai.cn/tts\", \"audio_format\": \"pcm\", \"access_token\": \"U4YdYXVfpwWnk2t5Gp822zWPCuORyeJL\", \"voice\": \"OUeAo1mhq6IBExi\"}', NULL, NULL, 17, NULL, NULL, NULL, NULL);

-- Tài liệu hướng dẫn cấu hình mô hình LinkeraiTTS
UPDATE `ai_model_config` SET 
`doc_link` = 'https://tts.linkerai.cn/docs',
`remark` = 'Hướng dẫn cấu hình dịch vụ tổng hợp giọng nói Linkerai：
1. Truy cập https://linkerai.cn để đăng ký và lấy token truy cập
2. access_token mặc định dùng để kiểm thử, vui lòng không sử dụng cho mục đích thương mại
3. Hỗ trợ chức năng clone giọng nói, có thể tự tải lên âm thanh, điền vào tham số voice
4. Nếu tham số voice trống, sẽ sử dụng giọng mặc định' WHERE `id` = 'TTS_LinkeraiTTS';


delete from `ai_tts_voice` where tts_model_id = 'TTS_LinkeraiTTS';
INSERT INTO `ai_tts_voice` VALUES ('TTS_LinkeraiTTS_0001', 'TTS_LinkeraiTTS', 'Chỉ Nhược', 'OUeAo1mhq6IBExi', 'Tiếng Trung', NULL, NULL, 1, NULL, NULL, NULL, NULL);
