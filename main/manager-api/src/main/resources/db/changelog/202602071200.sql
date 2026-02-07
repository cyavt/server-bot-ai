-- Xác nhận và đảm bảo kích thước cột đã được sửa đổi đúng
-- File này đảm bảo các cột quan trọng có kích thước đủ lớn để lưu trữ văn bản tiếng Việt dài

-- Đảm bảo cột ai_tts_voice.name là VARCHAR(255)
ALTER TABLE `ai_tts_voice` MODIFY COLUMN `name` VARCHAR(255) COMMENT 'Tên giọng';

-- Đảm bảo cột ai_model_provider.name là VARCHAR(255)
ALTER TABLE `ai_model_provider` MODIFY COLUMN `name` VARCHAR(255) COMMENT 'Tên provider';

-- Đảm bảo cột ai_model_config.model_name là VARCHAR(255)
ALTER TABLE `ai_model_config` MODIFY COLUMN `model_name` VARCHAR(255) COMMENT 'Tên mô hình';
