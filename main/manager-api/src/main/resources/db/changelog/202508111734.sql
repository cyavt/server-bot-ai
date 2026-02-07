-- Cập nhật provider HuoshanDoubleStreamTTS thêm cấu hình tốc độ nói, độ cao giọng, v.v.
UPDATE `ai_model_provider`
SET fields = '[{"key": "ws_url", "type": "string", "label": "Địa chỉ WebSocket"}, {"key": "appid", "type": "string", "label": "ID ứng dụng"}, {"key": "access_token", "type": "string", "label": "Token truy cập"}, {"key": "resource_id", "type": "string", "label": "ID tài nguyên"}, {"key": "speaker", "type": "string", "label": "Giọng mặc định"}, {"key": "speech_rate", "type": "number", "label": "Tốc độ nói(-50~100)"}, {"key": "loudness_rate", "type": "number", "label": "Âm lượng(-50~100)"}, {"key": "pitch", "type": "number", "label": "Độ cao giọng(-12~12)"}]'
WHERE id = 'SYSTEM_TTS_HSDSTTS';

UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/service/10007',
`remark` = 'Hướng dẫn cấu hình dịch vụ tổng hợp giọng nói Núi Lửa：
1. Truy cập https://www.volcengine.com/ để đăng ký và mở tài khoản Núi Lửa
2. Truy cập https://console.volcengine.com/speech/service/10007 để mở mô hình lớn tổng hợp giọng nói, mua giọng
3. Lấy appid và access_token ở cuối trang
5. ID tài nguyên cố định là：volc.service_type.10029 (tổng hợp giọng nói mô hình lớn và trộn âm)
6. Tốc độ nói：-50~100, có thể không điền, giá trị mặc định bình thường 0, có thể điền -50~100
7. Âm lượng：-50~100, có thể không điền, giá trị mặc định bình thường 0, có thể điền -50~100
8. Độ cao giọng：-12~12, có thể không điền, giá trị mặc định bình thường 0, có thể điền -12~12
9. Điền vào file cấu hình' WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';