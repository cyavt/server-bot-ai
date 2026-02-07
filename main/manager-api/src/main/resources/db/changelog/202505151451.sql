-- Sửa đổi định nghĩa yêu cầu giao diện TTS tùy chỉnh
update `ai_model_provider` set `fields` =
'[{"key":"url","label":"Địa chỉ dịch vụ","type":"string"},{"key":"method","label":"Phương thức yêu cầu","type":"string"},{"key":"params","label":"Tham số yêu cầu","type":"dict","dict_name":"params"},{"key":"headers","label":"Header yêu cầu","type":"dict","dict_name":"headers"},{"key":"format","label":"Định dạng âm thanh","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]'
where `id` = 'SYSTEM_TTS_custom';

-- Sửa đổi hướng dẫn cấu hình TTS tùy chỉnh
UPDATE `ai_model_config` SET
`doc_link` = NULL,
`remark` = 'Hướng dẫn cấu hình TTS tùy chỉnh：
1. Dịch vụ giao diện TTS tùy chỉnh, tham số yêu cầu có thể tùy chỉnh, có thể kết nối nhiều dịch vụ TTS
2. Lấy KokoroTTS triển khai local làm ví dụ
3. Nếu chỉ có cpu chạy：docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest
4. Nếu có gpu chạy：docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:latest
Hướng dẫn cấu hình：
1. Cấu hình tham số yêu cầu trong params, sử dụng định dạng JSON
   Ví dụ KokoroTTS：{ "input": "{prompt_text}", "speed": 1, "voice": "zm_yunxi", "stream": true, "download_format": "mp3", "response_format": "mp3", "return_download_link": true }
2. Cấu hình header yêu cầu trong headers
3. Thiết lập định dạng âm thanh trả về' WHERE `id` = 'TTS_CustomTTS';