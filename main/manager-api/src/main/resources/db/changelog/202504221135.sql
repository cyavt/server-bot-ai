-- Xóa provider mô hình không dùng
delete from `ai_model_provider` where id = 'SYSTEM_LLM_doubao';
delete from `ai_model_provider` where id = 'SYSTEM_LLM_chatglm';
delete from `ai_model_provider` where id = 'SYSTEM_TTS_302ai';
delete from `ai_model_provider` where id = 'SYSTEM_TTS_gizwits';

-- Thêm provider mô hình
delete from `ai_model_provider` where id = 'SYSTEM_ASR_TencentASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_TencentASR', 'ASR', 'tencent', 'Nhận dạng giọng nói Tencent', '[{"key":"appid","label":"ID ứng dụng","type":"string"},{"key":"secret_id","label":"Secret ID","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]', 4, 1, NOW(), 1, NOW());

-- Thêm provider mô hình tổng hợp giọng nói Tencent
delete from `ai_model_provider` where id = 'SYSTEM_TTS_TencentTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_TencentTTS', 'TTS', 'tencent', 'Tổng hợp giọng nói Tencent', '[{"key":"appid","label":"ID ứng dụng","type":"string"},{"key":"secret_id","label":"Secret ID","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"},{"key":"region","label":"Khu vực","type":"string"},{"key":"voice","label":"ID giọng","type":"string"}]', 5, 1, NOW(), 1, NOW());


-- Thêm giọng edge
delete from `ai_tts_voice` where id in ('TTS_EdgeTTS0001', 'TTS_EdgeTTS0002', 'TTS_EdgeTTS0003', 'TTS_EdgeTTS0004', 'TTS_EdgeTTS0005', 'TTS_EdgeTTS0006', 'TTS_EdgeTTS0007', 'TTS_EdgeTTS0008', 'TTS_EdgeTTS0009', 'TTS_EdgeTTS0010', 'TTS_EdgeTTS0011');
INSERT INTO `ai_tts_voice` VALUES 
('TTS_EdgeTTS0001', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ-Tiểu Tiểu', 'zh-CN-XiaoxiaoNeural', 'Tiếng Phổ thông', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0002', 'TTS_EdgeTTS', 'EdgeTTS giọng nam-Vân Dương', 'zh-CN-YunyangNeural', 'Tiếng Phổ thông', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0003', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ-Tiểu Y', 'zh-CN-XiaoyiNeural', 'Tiếng Phổ thông', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0004', 'TTS_EdgeTTS', 'EdgeTTS giọng nam-Vân Kiện', 'zh-CN-YunjianNeural', 'Tiếng Phổ thông', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0005', 'TTS_EdgeTTS', 'EdgeTTS giọng nam-Vân Hy', 'zh-CN-YunxiNeural', 'Tiếng Phổ thông', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0006', 'TTS_EdgeTTS', 'EdgeTTS giọng nam-Vân Hạ', 'zh-CN-YunxiaNeural', 'Tiếng Phổ thông', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0007', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ-Liêu Ninh Tiểu Bối', 'zh-CN-liaoning-XiaobeiNeural', 'Liêu Ninh', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0008', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ-Thiểm Tây Tiểu Nê', 'zh-CN-shaanxi-XiaoniNeural', 'Thiểm Tây', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0009', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ-Hồng Kông Hải Giai', 'zh-HK-HiuGaaiNeural', 'Tiếng Quảng Đông', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0010', 'TTS_EdgeTTS', 'EdgeTTS giọng nữ-Hồng Kông Hải Mạn', 'zh-HK-HiuMaanNeural', 'Tiếng Quảng Đông', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0011', 'TTS_EdgeTTS', 'EdgeTTS giọng nam-Hồng Kông Vạn Long', 'zh-HK-WanLungNeural', 'Tiếng Quảng Đông', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL);

-- Giọng DoubaoTTS
delete from `ai_tts_voice` where id in ('TTS_DoubaoTTS0001', 'TTS_DoubaoTTS0002', 'TTS_DoubaoTTS0003', 'TTS_DoubaoTTS0004', 'TTS_DoubaoTTS0005');
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0001', 'TTS_DoubaoTTS', 'Giọng nữ thông dụng', 'BV001_streaming', 'Tiếng Phổ thông', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV001.mp3', NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0002', 'TTS_DoubaoTTS', 'Giọng nam thông dụng', 'BV002_streaming', 'Tiếng Phổ thông', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV002.mp3', NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0003', 'TTS_DoubaoTTS', 'Thanh niên tươi sáng', 'BV056_streaming', 'Tiếng Phổ thông', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV056.mp3', NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0004', 'TTS_DoubaoTTS', 'Em bé dễ thương', 'BV051_streaming', 'Tiếng Phổ thông', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV051.mp3', NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0005', 'TTS_DoubaoTTS', 'Tiểu Hà Vịnh Vịnh', 'zh_female_wanwanxiaohe_moon_bigtts', 'Tiếng Phổ thông', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 6, NULL, NULL, NULL, NULL);

-- Sửa giọng CosyVoiceSiliconflow
delete from `ai_tts_voice` where id in ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow0002');
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow', 'CosyVoice giọng nam', 'FunAudioLLM/CosyVoice2-0.5B:alex', 'Tiếng Trung', NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0002', 'TTS_CosyVoiceSiliconflow', 'CosyVoice giọng nữ', 'FunAudioLLM/CosyVoice2-0.5B:bella', 'Tiếng Trung', NULL, NULL, 6, NULL, NULL, NULL, NULL);

-- Giọng CozeCnTTS
delete from `ai_tts_voice` where id = 'TTS_CozeCnTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_CozeCnTTS0001', 'TTS_CozeCnTTS', 'Giọng CozeCn', '7426720361733046281', 'Tiếng Trung', NULL, NULL, 7, NULL, NULL, NULL, NULL);

-- Giọng MinimaxTTS
delete from `ai_tts_voice` where id = 'TTS_MinimaxTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxTTS0001', 'TTS_MinimaxTTS', 'Giọng thiếu nữ Minimax', 'female-shaonv', 'Tiếng Trung', NULL, NULL, 8, NULL, NULL, NULL, NULL);

-- Giọng AliyunTTS
delete from `ai_tts_voice` where id = 'TTS_AliyunTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunTTS0001', 'TTS_AliyunTTS', 'Tiểu Vân Alibaba Cloud', 'xiaoyun', 'Tiếng Trung', NULL, NULL, 9, NULL, NULL, NULL, NULL);

-- Giọng TTS302AI
delete from `ai_tts_voice` where id = 'TTS_TTS302AI0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_TTS302AI0001', 'TTS_TTS302AI', 'Tiểu Hà Vịnh Vịnh', 'zh_female_wanwanxiaohe_moon_bigtts', 'Tiếng Trung', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 10, NULL, NULL, NULL, NULL);

-- Giọng GizwitsTTS
delete from `ai_tts_voice` where id = 'TTS_GizwitsTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_GizwitsTTS0001', 'TTS_GizwitsTTS', 'Vịnh Vịnh Gizwits', 'zh_female_wanwanxiaohe_moon_bigtts', 'Tiếng Trung', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 11, NULL, NULL, NULL, NULL);

-- Giọng ACGNTTS
delete from `ai_tts_voice` where id = 'TTS_ACGNTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_ACGNTTS0001', 'TTS_ACGNTTS', 'Giọng ACG', '1695', 'Tiếng Trung', NULL, NULL, 12, NULL, NULL, NULL, NULL);

-- Giọng OpenAITTS
delete from `ai_tts_voice` where id = 'TTS_OpenAITTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_OpenAITTS0001', 'TTS_OpenAITTS', 'OpenAI giọng nam', 'onyx', 'Tiếng Trung', NULL, NULL, 13, NULL, NULL, NULL, NULL);

-- Thêm giọng tổng hợp giọng nói Tencent
delete from `ai_tts_voice` where id = 'TTS_TencentTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_TencentTTS0001', 'TTS_TencentTTS', 'Trí Du', '101001', 'Tiếng Trung', NULL, NULL, 1, NULL, NULL, NULL, NULL);

-- Các giọng khác
delete from `ai_tts_voice` where id = 'TTS_FishSpeech0000';
INSERT INTO `ai_tts_voice` VALUES ('TTS_FishSpeech0000', 'TTS_FishSpeech', '', '', 'Tiếng Trung', '', NULL, 8, NULL, NULL, NULL, NULL);

delete from `ai_tts_voice` where id = 'TTS_GPT_SOVITS_V20000';
INSERT INTO `ai_tts_voice` VALUES ('TTS_GPT_SOVITS_V20000', 'TTS_GPT_SOVITS_V2', '', '', 'Tiếng Trung', '', NULL, 8, NULL, NULL, NULL, NULL);

delete from `ai_tts_voice` where id in ('TTS_GPT_SOVITS_V30000', 'TTS_CustomTTS0000');
INSERT INTO `ai_tts_voice` VALUES ('TTS_GPT_SOVITS_V30000', 'TTS_GPT_SOVITS_V3', '', '', 'Tiếng Trung', '', NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_CustomTTS0000', 'TTS_CustomTTS', '', '', 'Tiếng Trung', '', NULL, 8, NULL, NULL, NULL, NULL);

