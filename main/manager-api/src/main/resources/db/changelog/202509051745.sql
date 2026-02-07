-- Thêm provider TTS streaming MinimaxHTTPStream
delete from `ai_model_provider` where id = 'SYSTEM_TTS_MinimaxStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_MinimaxStreamTTS', 'TTS', 'minimax_httpstream', 'Tổng hợp giọng nói streaming Minimax', '[{"key":"group_id","label":"ID nhóm","type":"string"},{"key":"api_key","label":"Khóa API","type":"string"},{"key":"model","label":"Mô hình","type":"string"},{"key":"voice_id","label":"ID giọng","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"},{"key":"voice_setting","label":"Thiết lập giọng","type":"dict","dict_name":"voice_setting"},{"key":"pronunciation_dict","label":"Từ điển phát âm","type":"dict","dict_name":"pronunciation_dict"},{"key":"audio_setting","label":"Thiết lập âm thanh","type":"dict","dict_name":"audio_setting"},{"key":"timber_weights","label":"Trọng số giọng","type":"string"}]', 18, 1, NOW(), 1, NOW());

-- Thêm cấu hình mô hình TTS streaming Minimax
delete from `ai_model_config` where id = 'TTS_MinimaxStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_MinimaxStreamTTS', 'TTS', 'MinimaxStreamTTS', 'Tổng hợp giọng nói streaming Minimax', 0, 1, '{"type": "minimax_httpstream", "group_id": "", "api_key": "", "model": "speech-01-turbo", "voice_id": "female-shaonv", "output_dir": "tmp/", "voice_setting": {"speed": 1, "vol": 1, "pitch": 0, "emotion": "happy"}, "pronunciation_dict": {"tone": ["处理/(chu3)(li3)", "危险/dangerous"]}, "audio_setting": {"sample_rate": 24000, "bitrate": 128000, "format": "pcm", "channel": 1}}', NULL, NULL, 21, NULL, NULL, NULL, NULL);

-- Cập nhật hướng dẫn cấu hình TTS streaming Minimax
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.minimaxi.com/',
`remark` = 'Hướng dẫn cấu hình TTS streaming Minimax：
1. Cần đăng ký Minimax API Key trước
2. Cần điền Group ID
3. Hỗ trợ thiết lập nhiều giọng và điều chỉnh tham số âm thanh
4. Hỗ trợ tổng hợp streaming thời gian thực, có độ trễ thấp
5. Hỗ trợ từ điển phát âm tùy chỉnh và trọng số giọng
6. Cấu hình tham số ẩn：Thiết lập giọng (voice_setting)、Từ điển phát âm (pronunciation_dict)、Trọng số giọng (timber_weights)
   - Tốc độ nói (speed): Phạm vi [0.5,2], mặc định 1.0, giá trị càng lớn tốc độ nói càng nhanh
   - Âm lượng (vol): Phạm vi (0,10], mặc định 1.0, giá trị càng lớn âm lượng càng cao
   - Độ cao giọng (pitch): Phạm vi [-12,12], mặc định 0, giá trị phải là số nguyên
   - Cảm xúc (emotion): Điều khiển cảm xúc của giọng nói tổng hợp, hỗ trợ 7 giá trị：["happy", "sad", "angry", "fearful", "disgusted", "surprised", "calm"], tham số này chỉ có hiệu lực với speech-2.5-hd-preview、speech-2.5-turbo-preview、speech-02-hd、speech-02-turbo、speech-01-turbo、speech-01-hd
   - timbre_weights và voice_id phải chọn một trong hai
   - voice_id (ID giọng yêu cầu, phải điền đồng bộ với tham số weight)
   - weight (Trọng số, hỗ trợ tối đa 4 giọng trộn. Phạm vi [1,100])
' WHERE `id` = 'TTS_MinimaxStreamTTS';

-- Thêm giọng TTS streaming Minimax
delete from `ai_tts_voice` where tts_model_id = 'TTS_MinimaxStreamTTS';

-- Giọng mặc định
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0001', 'TTS_MinimaxStreamTTS', 'Giọng thiếu nữ', 'female-shaonv', 'Tiếng Trung', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0002', 'TTS_MinimaxStreamTTS', 'Giọng nữ trưởng thành', 'female-chengshu', 'Tiếng Trung', NULL, NULL, NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0003', 'TTS_MinimaxStreamTTS', 'Thiếu gia độc đoán', 'badao_shaoye', 'Tiếng Trung', NULL, NULL, NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0004', 'TTS_MinimaxStreamTTS', 'Em trai bệnh hoạn', 'bingjiao_didi', 'Tiếng Trung', NULL, NULL, NULL, NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0005', 'TTS_MinimaxStreamTTS', 'Học đệ thuần khiết', 'chunzhen_xuedi', 'Tiếng Trung', NULL, NULL, NULL, NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0006', 'TTS_MinimaxStreamTTS', 'Học trưởng lạnh lùng', 'lengdan_xiongzhang', 'Tiếng Trung', NULL, NULL, NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0007', 'TTS_MinimaxStreamTTS', 'Tiểu Linh ngọt ngào', 'tianxin_xiaoling', 'Tiếng Trung', NULL, NULL, NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0008', 'TTS_MinimaxStreamTTS', 'Mèo con tinh nghịch', 'qiaopi_mengmei', 'Tiếng Trung', NULL, NULL, NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0009', 'TTS_MinimaxStreamTTS', 'Ngự tỷ quyến rũ', 'wumei_yujie', 'Tiếng Trung', NULL, NULL, NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0010', 'TTS_MinimaxStreamTTS', 'Học muội dễ thương', 'diadia_xuemei', 'Tiếng Trung', NULL, NULL, NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0011', 'TTS_MinimaxStreamTTS', 'Học tỷ thanh tao', 'danya_xuejie', 'Tiếng Trung', NULL, NULL, NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0012', 'TTS_MinimaxStreamTTS', 'Santa Claus', 'Santa_Claus', 'Tiếng Trung', NULL, NULL, NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0013', 'TTS_MinimaxStreamTTS', 'Grinch', 'Grinch', 'Tiếng Trung', NULL, NULL, NULL, NULL, 10, NULL, NULL, NULL, NULL);
