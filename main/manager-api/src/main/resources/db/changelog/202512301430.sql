-- Thêm cấu hình dịch vụ nhận dạng giọng nói thời gian thực Paraformer của Alibaba Bách Luyện
delete from `ai_model_provider` where id = 'SYSTEM_ASR_AliyunBLStream';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_AliyunBLStream', 'ASR', 'aliyunbl_stream', 'Nhận dạng giọng nói thời gian thực Paraformer Alibaba Bách Luyện', '[{"key":"api_key","label":"Khóa API","type":"password"},{"key":"model","label":"Tên mô hình","type":"string"},{"key":"format","label":"Định dạng âm thanh","type":"string"},{"key":"sample_rate","label":"Tần số lấy mẫu","type":"number"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]', 18, 1, NOW(), 1, NOW());

delete from `ai_model_config` where id = 'ASR_AliyunBLStream';
INSERT INTO `ai_model_config` VALUES ('ASR_AliyunBLStream', 'ASR', 'AliyunBLStream', 'Nhận dạng giọng nói thời gian thực Paraformer Alibaba Bách Luyện', 0, 1, '{"type": "aliyunbl_stream", "api_key": "", "model": "paraformer-realtime-v2", "format": "pcm", "sample_rate": 16000, "disfluency_removal_enabled": false, "semantic_punctuation_enabled": false, "max_sentence_silence": 200, "multi_threshold_mode_enabled": false, "punctuation_prediction_enabled": true, "inverse_text_normalization_enabled": true, "output_dir": "tmp/"}', 'https://help.aliyun.com/zh/model-studio/websocket-for-paraformer-real-time-service', 'Hỗ trợ đa ngôn ngữ, tùy chỉnh từ khóa, ngắt câu ngữ nghĩa và các chức năng nâng cao khác', 21, NULL, NULL, NULL, NULL);

-- Cập nhật tài liệu hướng dẫn cấu hình mô hình Paraformer Alibaba Bách Luyện
UPDATE `ai_model_config` SET
`doc_link` = 'https://help.aliyun.com/zh/model-studio/websocket-for-paraformer-real-time-service',
`remark` = 'Hướng dẫn cấu hình nhận dạng giọng nói thời gian thực Paraformer Alibaba Bách Luyện：
1. Đăng nhập nền tảng Alibaba Bách Luyện https://bailian.console.aliyun.com/
2. Tạo API-KEY https://bailian.console.aliyun.com/#/api-key
3. Mô hình hỗ trợ：paraformer-realtime-v2 (khuyến nghị)、paraformer-realtime-8k-v2、paraformer-realtime-v1、paraformer-realtime-8k-v1
4. Tính năng：
   - Hỗ trợ đa ngôn ngữ (tiếng Trung bao gồm phương ngữ, tiếng Anh, tiếng Nhật, tiếng Hàn, tiếng Đức, tiếng Pháp, tiếng Nga)
   - Tùy chỉnh từ khóa (tham số vocabulary_id), tham khảo chi tiết：https://help.aliyun.com/zh/model-studio/custom-hot-words?
   - Ngắt câu ngữ nghĩa/Ngắt câu VAD (tham số semantic_punctuation_enabled)
   - Tự động dấu câu, ITN, lọc từ ngữ cảm xúc, v.v.
5. Giải thích tham số：
   - model: Tên mô hình, khuyến nghị paraformer-realtime-v2
   - sample_rate: Tần số lấy mẫu (Hz), v2 hỗ trợ tần số lấy mẫu bất kỳ, v1 chỉ hỗ trợ 16000, phiên bản 8k chỉ hỗ trợ 8000
   - semantic_punctuation_enabled: false là ngắt câu VAD (độ trễ thấp), true là ngắt câu ngữ nghĩa (độ chính xác cao)
   - max_sentence_silence: Ngưỡng thời lượng im lặng ngắt câu VAD (200-6000ms)
' WHERE `id` = 'ASR_AliyunBLStream';


-- Cập nhật provider ASR streaming Đậu Bao, thêm cấu hình
delete from `ai_model_provider` where id = 'SYSTEM_ASR_DoubaoStreamASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_DoubaoStreamASR', 'ASR', 'doubao_stream', 'Nhận dạng giọng nói Núi Lửa (streaming)', '[{"key":"appid","label":"ID ứng dụng","type":"string"},{"key":"access_token","label":"Token truy cập","type":"string"},{"key":"cluster","label":"Cluster","type":"string"},{"key":"boosting_table_name","label":"Tên file từ khóa","type":"string"},{"key":"correct_table_name","label":"Tên file từ thay thế","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"},{"key":"end_window_size","label":"Thời lượng phán đoán im lặng (ms)","type":"number"},{"key":"enable_multilingual","label":"Có bật chế độ nhận dạng đa ngôn ngữ không","type":"boolean"},{"key":"language","label":"Mã ngôn ngữ chỉ định","type":"string"}]', 3, 1, NOW(), 1, NOW());
UPDATE `ai_model_config` SET 
`remark` = 'Hướng dẫn cấu hình ASR Đậu Bao：
1. Sự khác biệt giữa ASR Đậu Bao và ASR Đậu Bao (streaming) là：ASR Đậu Bao tính phí theo lần, ASR Đậu Bao (streaming) tính phí theo thời gian
2. Nói chung tính phí theo lần rẻ hơn, nhưng ASR Đậu Bao (streaming) sử dụng công nghệ mô hình lớn, hiệu quả tốt hơn
3. Cần tạo ứng dụng trong bảng điều khiển Núi Lửa và lấy appid và access_token
4. Hỗ trợ nhận dạng giọng nói tiếng Trung
5. Cần kết nối mạng
6. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký：
1. Truy cập https://console.volcengine.com/speech/app
2. Tạo ứng dụng mới
3. Lấy appid và access_token
4. Điền vào file cấu hình
Nếu cần thiết lập từ khóa, tham khảo：https://www.volcengine.com/docs/6561/155738
Nếu bật chế độ nhận dạng đa ngôn ngữ, hãy thiết lập language, khi khóa này trống, mô hình này hỗ trợ nhận dạng tiếng Trung-Anh, tiếng Thượng Hải, tiếng Mân Nam, Tứ Xuyên, Thiểm Tây, tiếng Quảng Đông. Các ngôn ngữ khác tham khảo：https://www.volcengine.com/docs/6561/1354869
' WHERE `id` = 'ASR_DoubaoStreamASR';

-- Cập nhật cấu hình mô hình ASR streaming Đậu Bao, thêm giá trị mặc định enable_multilingual
UPDATE `ai_model_config` SET
`config_json` = JSON_SET(
    `config_json`, 
    '$.enable_multilingual', false,
    '$.language', 'zh-CN'
)
WHERE `id` = 'ASR_DoubaoStreamASR' 
AND JSON_EXTRACT(`config_json`, '$.enable_multilingual') IS NULL 
AND JSON_EXTRACT(`config_json`, '$.language') IS NULL;


-- Cập nhật cấu hình provider HuoshanDoubleStreamTTS, thêm tham số giọng đa cảm xúc
UPDATE `ai_model_provider`
SET `fields` = '[{"key": "ws_url", "type": "string", "label": "Địa chỉ WebSocket"}, {"key": "appid", "type": "string", "label": "ID ứng dụng"}, {"key": "access_token", "type": "string", "label": "Token truy cập"}, {"key": "resource_id", "type": "string", "label": "ID tài nguyên"}, {"key": "speaker", "type": "string", "label": "Giọng mặc định"}, {"key": "enable_ws_reuse", "type": "boolean", "label": "Có bật tái sử dụng kết nối không", "default": true}, {"key": "speech_rate", "type": "number", "label": "Tốc độ nói(-50~100)"}, {"key": "loudness_rate", "type": "number", "label": "Âm lượng(-50~100)"}, {"key": "pitch", "type": "number", "label": "Độ cao giọng(-12~12)"}, {"key": "emotion_scale", "type": "number", "label": "Cường độ cảm xúc(1-5)"}, {"key": "emotion", "type": "string", "label": "Loại cảm xúc"}]'
WHERE `id` = 'SYSTEM_TTS_HSDSTTS';

-- Cập nhật giá trị mặc định
UPDATE `ai_model_config` SET
`config_json` = JSON_SET(
    `config_json`,
    '$.emotion', 'neutral',
    '$.emotion_scale', 4
)
WHERE `id` = 'TTS_HuoshanDoubleStreamTTS'
AND JSON_EXTRACT(`config_json`, '$.emotion') IS NULL 
AND JSON_EXTRACT(`config_json`, '$.emotion_scale') IS NULL;

-- Thêm liên kết tài liệu và ghi chú
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
10. Tham số đa cảm xúc (hiện tại chỉ một số giọng hỗ trợ thiết lập cảm xúc)：
   Danh sách giọng liên quan：https://www.volcengine.com/docs/6561/1257544
   - emotion_scale：Cường độ cảm xúc, giá trị có thể chọn：1~5, giá trị mặc định là 4
   - emotion：Loại cảm xúc, giá trị có thể chọn：neutral、happy、sad、angry、fearful、disgusted、surprised
' WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';
