ALTER TABLE `ai_tts_voice`
ADD COLUMN `reference_audio` VARCHAR(500) DEFAULT NULL COMMENT 'Đường dẫn âm thanh tham chiếu' AFTER `remark`,
ADD COLUMN `reference_text` VARCHAR(500) DEFAULT NULL COMMENT 'Văn bản tham chiếu' AFTER `reference_audio`;
