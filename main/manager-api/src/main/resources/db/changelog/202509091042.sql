-- Xóa cấu hình TTS MiniMax không streaming, giữ lại phiên bản streaming

-- Xóa cấu hình mô hình TTS MiniMax không streaming cũ
DELETE FROM `ai_model_config` WHERE `id` = 'TTS_MinimaxTTS';

-- Xóa cấu hình provider TTS MiniMax không streaming cũ  
DELETE FROM `ai_model_provider` WHERE `id` = 'SYSTEM_TTS_minimax';

-- Xóa cấu hình giọng TTS MiniMax không streaming cũ
DELETE FROM `ai_tts_voice` WHERE `tts_model_id` = 'TTS_MinimaxTTS';
