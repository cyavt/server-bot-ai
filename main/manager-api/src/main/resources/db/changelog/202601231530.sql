-- Cập nhật cấu hình provider HuoshanDoubleStreamTTS, chuyển các tham số rời rạc thành cấu hình JSON dictionary
-- Tích hợp các tham số speech_rate, loudness_rate, pitch, emotion, emotion_scale thành 3 JSON dictionary: audio_params, additions, mix_speaker

UPDATE `ai_model_provider`
SET `fields` = '[
  {"key": "ws_url", "type": "string", "label": "Địa chỉ WebSocket"},
  {"key": "appid", "type": "string", "label": "ID ứng dụng"},
  {"key": "access_token", "type": "string", "label": "Token truy cập"},
  {"key": "resource_id", "type": "string", "label": "ID tài nguyên"},
  {"key": "speaker", "type": "string", "label": "Giọng mặc định"},
  {"key": "enable_ws_reuse", "type": "boolean", "label": "Có bật tái sử dụng kết nối không", "default": true},
  {"key": "audio_params", "type": "dict", "label": "Cấu hình đầu ra âm thanh"},
  {"key": "additions", "type": "dict", "label": "Cấu hình xử lý văn bản nâng cao"},
  {"key": "mix_speaker", "type": "dict", "label": "Cấu hình điều khiển trộn âm"}
]'
WHERE `id` = 'SYSTEM_TTS_HSDSTTS';

-- Cập nhật cấu hình hiện có, di chuyển các tham số rời rạc cũ sang cấu trúc JSON dictionary mới
UPDATE `ai_model_config`
SET `config_json` = JSON_SET(
    `config_json`,
    '$.audio_params', JSON_OBJECT(
        'speech_rate', CAST(COALESCE(NULLIF(JSON_UNQUOTE(JSON_EXTRACT(`config_json`, '$.speech_rate')), ''), '0') AS SIGNED),
        'loudness_rate', CAST(COALESCE(NULLIF(JSON_UNQUOTE(JSON_EXTRACT(`config_json`, '$.loudness_rate')), ''), '0') AS SIGNED)
    ),
    '$.additions', JSON_OBJECT(
        'aigc_metadata', JSON_OBJECT(),
        'cache_config', JSON_OBJECT(),
        'post_process', JSON_OBJECT(
            'pitch', CAST(COALESCE(NULLIF(JSON_UNQUOTE(JSON_EXTRACT(`config_json`, '$.pitch')), ''), '0') AS SIGNED)
        )
    ),
    '$.mix_speaker', JSON_OBJECT()
)
WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';

-- Xóa các trường tham số rời rạc cũ
UPDATE `ai_model_config`
SET `config_json` = JSON_REMOVE(
    `config_json`,
    '$.speech_rate',
    '$.loudness_rate',
    '$.pitch',
    '$.emotion',
    '$.emotion_scale'
)
WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';

-- Cập nhật liên kết tài liệu và ghi chú
UPDATE `ai_model_config` SET
`doc_link` = 'https://www.volcengine.com/docs/6561/1329505',
`remark` = 'Hướng dẫn cấu hình TTS streaming hai chiều Núi Lửa:
1. Truy cập https://www.volcengine.com/ để đăng ký và mở tài khoản Núi Lửa
2. Truy cập https://console.volcengine.com/speech/service/10007 để mở mô hình lớn tổng hợp giọng nói, mua giọng
3. Lấy appid và access_token ở cuối trang
4. ID tài nguyên cố định là: volc.service_type.10029 (tổng hợp giọng nói mô hình lớn và trộn âm)
5. Tái sử dụng kết nối: Bật tái sử dụng kết nối WebSocket, mặc định true để giảm hao phí kết nối (Lưu ý: Sau khi tái sử dụng, khi thiết bị ở trạng thái lắng nghe, kết nối rảnh sẽ chiếm số đồng thời)

Tài liệu tham số chi tiết: https://www.volcengine.com/docs/6561/1329505
【audio_params】Cấu hình đầu ra âm thanh - Người dùng có thể tự thêm bất kỳ tham số âm thanh nào được Núi Lửa hỗ trợ
  - speech_rate: Tốc độ nói(-50~100), mặc định 0
  - loudness_rate: Âm lượng(-50~100), mặc định 0
  - emotion: Loại cảm xúc (chỉ một số giọng hỗ trợ), giá trị có thể chọn: neutral、happy、sad、angry、fearful、disgusted、surprised
  - emotion_scale: Cường độ cảm xúc(1~5), mặc định 4
  Ví dụ: {"speech_rate": 10, "loudness_rate": 5, "emotion": "happy", "emotion_scale": 4}

【additions】Cấu hình xử lý văn bản nâng cao - Người dùng có thể tự thêm bất kỳ tham số nâng cao nào được Núi Lửa hỗ trợ
  - post_process.pitch: Độ cao giọng(-12~12), mặc định 0
  - aigc_metadata: Cấu hình metadata AIGC
  - cache_config: Cấu hình cache
  Ví dụ: {"post_process": {"pitch": 2}, "aigc_metadata": {}, "cache_config": {}}

【mix_speaker】Cấu hình điều khiển trộn âm - Trộn đa giọng (chỉ TTS 1.0)
  Ví dụ:
    {"speakers": [
      {"source_speaker": "zh_male_bvlazysheep","mix_factor": 0.3}, 
      {"source_speaker": "BV120_streaming","mix_factor": 0.3}, 
      {"source_speaker": "zh_male_ahu_conversation_wvae_bigtts","mix_factor": 0.4}
    ]}

Lưu ý:
- Tham số giọng đa cảm xúc (emotion、emotion_scale) chỉ một số giọng hỗ trợ
- Danh sách giọng liên quan: https://www.volcengine.com/docs/6561/1257544
- Người dùng có thể tự thêm nhiều tham số theo tài liệu API Núi Lửa
- Chức năng trộn âm chủ yếu áp dụng cho giọng mô hình tổng hợp giọng nói 1.0 Đậu Bao, khi sử dụng cần đặt req_params.speaker thành custom_mix_bigtts
'
WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';
