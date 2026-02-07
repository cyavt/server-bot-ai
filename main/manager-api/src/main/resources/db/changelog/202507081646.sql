-- Thêm trường mới cho vân tay giọng nói agent
ALTER TABLE ai_agent_voice_print
    ADD COLUMN audio_id VARCHAR(32) NOT NULL COMMENT 'ID âm thanh';