-- Thêm provider TTS streaming paddle_speech
DELETE FROM `ai_model_provider` WHERE id = 'SYSTEM_TTS_PaddleSpeechTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) 
VALUES ('SYSTEM_TTS_PaddleSpeechTTS', 'TTS', 'paddle_speech', 'PaddleSpeechTTS', 
'[{"key":"protocol","label":"Loại giao thức","type":"string","options":["websocket","http"]},{"key":"url","label":"Địa chỉ dịch vụ","type":"string"},{"key":"spk_id","label":"Giọng","type":"int"},{"key":"sample_rate","label":"Tần số lấy mẫu","type":"float"},{"key":"speed","label":"Tốc độ nói","type":"float"},{"key":"volume","label":"Âm lượng","type":"float"},{"key":"save_path","label":"Đường dẫn lưu","type":"string"}]', 
17, 1, NOW(), 1, NOW());

-- Thêm cấu hình mô hình TTS streaming paddle_speech
DELETE FROM `ai_model_config` WHERE id = 'TTS_PaddleSpeechTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_PaddleSpeechTTS', 'TTS', 'PaddleSpeechTTS', 'PaddleSpeechTTS', 0, 1, 
'{"type": "paddle_speech", "protocol": "websocket", "url": "ws://127.0.0.1:8092/paddlespeech/tts/streaming", "spk_id": "0", "sample_rate": 24000, "speed": 1.0, "volume": 1.0, "save_path": "./streaming_tts.wav"}', 
NULL, NULL, 20, NULL, NULL, NULL, NULL);

-- Cập nhật hướng dẫn cấu hình PaddleSpeechTTS
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/PaddlePaddle/PaddleSpeech',
`remark` = 'Hướng dẫn cấu hình PaddleSpeechTTS：
1. PaddleSpeech là công cụ tổng hợp giọng nói mã nguồn mở của Baidu PaddlePaddle, hỗ trợ triển khai offline local và huấn luyện mô hình. Địa chỉ framework Baidu PaddlePaddle：https://www.paddlepaddle.org.cn/
2. Hỗ trợ giao thức WebSocket và HTTP, mặc định sử dụng WebSocket để truyền streaming (tham khảo tài liệu triển khai：https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/paddlespeech-deploy.md)。
3. Trước khi sử dụng cần triển khai dịch vụ paddlespeech local, dịch vụ mặc định chạy tại ws://127.0.0.1:8092/paddlespeech/tts/streaming
4. Hỗ trợ tùy chỉnh người phát âm, tốc độ nói, âm lượng và tần số lấy mẫu。
' WHERE `id` = 'TTS_PaddleSpeechTTS';

-- Xóa giọng cũ và thêm giọng mặc định
DELETE FROM `ai_tts_voice` WHERE tts_model_id = 'TTS_PaddleSpeechTTS';
INSERT INTO `ai_tts_voice` VALUES ('TTS_PaddleSpeechTTS_0000', 'TTS_PaddleSpeechTTS', 'Mặc định', '0', 'Tiếng Trung', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);