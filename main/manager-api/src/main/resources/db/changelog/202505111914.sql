-- Thêm trường cấu hình lịch sử trò chuyện
ALTER TABLE `ai_agent` 
ADD COLUMN `chat_history_conf` tinyint NOT NULL DEFAULT 0 COMMENT 'Cấu hình lịch sử trò chuyện（0 Không ghi 1 Chỉ ghi văn bản 2 Ghi văn bản và giọng nói）' AFTER `system_prompt`;

ALTER TABLE `ai_agent_template` 
ADD COLUMN `chat_history_conf` tinyint NOT NULL DEFAULT 0 COMMENT 'Cấu hình lịch sử trò chuyện（0 Không ghi 1 Chỉ ghi văn bản 2 Ghi văn bản và giọng nói）' AFTER `system_prompt`;