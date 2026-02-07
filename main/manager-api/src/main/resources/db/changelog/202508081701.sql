-- Thêm provider TTS streaming Index-TTS-vLLM
delete from `ai_model_provider` where id = 'SYSTEM_TTS_IndexStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_IndexStreamTTS', 'TTS', 'index_stream', 'Tổng hợp giọng nói streaming Index-TTS-vLLM', '[{"key":"api_url","label":"Địa chỉ dịch vụ API","type":"string"},{"key":"voice","label":"Giọng mặc định","type":"string"},{"key":"audio_format","label":"Định dạng âm thanh","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]', 16, 1, NOW(), 1, NOW());

-- Thêm cấu hình mô hình TTS streaming Index-TTS-vLLM
delete from `ai_model_config` where id = 'TTS_IndexStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_IndexStreamTTS', 'TTS', 'IndexStreamTTS', 'Tổng hợp giọng nói streaming Index-TTS-vLLM', 0, 1, '{\"type\": \"index_stream\", \"api_url\": \"http://127.0.0.1:11996/tts\", \"voice\": \"jay_klee\", \"audio_format\": \"pcm\", \"output_dir\": \"tmp/\"}', NULL, NULL, 19, NULL, NULL, NULL, NULL);

-- Cập nhật hướng dẫn cấu hình TTS streaming Index-TTS-vLLM
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/Ksuriuri/index-tts-vllm',
`remark` = 'Hướng dẫn cấu hình TTS streaming Index-TTS-vLLM：
1. Index-TTS-vLLM là dịch vụ suy luận vLLM dựa trên dự án Index-TTS, cung cấp chức năng tổng hợp giọng nói streaming
2. Hỗ trợ nhiều giọng, chất lượng âm thanh tự nhiên, phù hợp với các tình huống tương tác giọng nói khác nhau
3. Cần triển khai dịch vụ Index-TTS-vLLM trước, sau đó cấu hình địa chỉ API
4. Hỗ trợ tổng hợp streaming thời gian thực, có độ trễ thấp
5. Hỗ trợ giọng tùy chỉnh, có thể đăng ký giọng mới trong thư mục assets của dự án
Các bước triển khai：
1. Clone dự án：git clone https://github.com/Ksuriuri/index-tts-vllm.git
2. Cài đặt phụ thuộc：pip install -r requirements.txt
3. Khởi động dịch vụ：python app.py
4. Dịch vụ mặc định chạy tại http://127.0.0.1:11996
5. Nếu cần giọng khác, có thể đến thư mục assets của dự án để đăng ký
6. Hỗ trợ nhiều định dạng âm thanh：pcm、wav、mp3, v.v.
Nếu cần tìm hiểu thêm cấu hình, tham khảo：https://github.com/Ksuriuri/index-tts-vllm/blob/master/README.md
' WHERE `id` = 'TTS_IndexStreamTTS';

-- Thêm giọng TTS streaming Index-TTS-vLLM
delete from `ai_tts_voice` where tts_model_id = 'TTS_IndexStreamTTS';
-- Giọng mặc định
INSERT INTO `ai_tts_voice` VALUES ('TTS_IndexStreamTTS_0001', 'TTS_IndexStreamTTS', 'Jay Klee', 'jay_klee', 'Tiếng Trung và hỗn hợp Trung-Anh', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);
