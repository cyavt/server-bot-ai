-- Thêm index cho audio_id trong bảng lịch sử chat của agent
ALTER TABLE ai_agent_chat_history ADD INDEX idx_ai_agent_chat_history_audio_id (audio_id);
