-- Cập nhật cấu hình provider HuoshanDoubleStreamTTS, thêm tùy chọn bật tái sử dụng kết nối
UPDATE `ai_model_provider`
SET fields = '[{"key": "ws_url", "type": "string", "label": "Địa chỉ WebSocket"}, {"key": "appid", "type": "string", "label": "ID ứng dụng"}, {"key": "access_token", "type": "string", "label": "Token truy cập"}, {"key": "resource_id", "type": "string", "label": "ID tài nguyên"}, {"key": "speaker", "type": "string", "label": "Giọng mặc định"}, {"key": "enable_ws_reuse", "type": "boolean", "label": "Có bật tái sử dụng kết nối không", "default": true}, {"key": "speech_rate", "type": "number", "label": "Tốc độ nói(-50~100)"}, {"key": "loudness_rate", "type": "number", "label": "Âm lượng(-50~100)"}, {"key": "pitch", "type": "number", "label": "Độ cao giọng(-12~12)"}]'
WHERE id = 'SYSTEM_TTS_HSDSTTS';

UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/service/10007',
`remark` = 'Hướng dẫn cấu hình dịch vụ tổng hợp giọng nói Núi Lửa：
1. Truy cập https://www.volcengine.com/ để đăng ký và mở tài khoản Núi Lửa
2. Truy cập https://console.volcengine.com/speech/service/10007 để mở mô hình lớn tổng hợp giọng nói, mua giọng
3. Lấy appid và access_token ở cuối trang
5. ID tài nguyên cố định là：volc.service_type.10029 (tổng hợp giọng nói mô hình lớn và trộn âm)
6. Tái sử dụng kết nối：Bật tái sử dụng kết nối WebSocket, mặc định true để giảm hao phí kết nối (Lưu ý：Sau khi tái sử dụng, khi thiết bị ở trạng thái lắng nghe, kết nối rảnh sẽ chiếm số đồng thời)
7. Tốc độ nói：-50~100, có thể không điền, giá trị mặc định bình thường 0, có thể điền -50~100
8. Âm lượng：-50~100, có thể không điền, giá trị mặc định bình thường 0, có thể điền -50~100
9. Độ cao giọng：-12~12, có thể không điền, giá trị mặc định bình thường 0, có thể điền -12~12
10. Điền vào file cấu hình' WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';