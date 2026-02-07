-- Thêm trường nhớ tóm tắt
ALTER TABLE `ai_agent`
ADD COLUMN `summary_memory` text COMMENT 'Nhớ tóm tắt' AFTER `system_prompt`;

ALTER TABLE `ai_agent_template`
ADD COLUMN `summary_memory` text COMMENT 'Nhớ tóm tắt' AFTER `system_prompt`;
