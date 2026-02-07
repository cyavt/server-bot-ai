-- Bảng provider mô hình
DROP TABLE IF EXISTS `ai_model_provider`;
CREATE TABLE `ai_model_provider` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Khóa chính',
    `model_type` VARCHAR(20) COMMENT 'Loại mô hình(Memory/ASR/VAD/LLM/TTS)',
    `provider_code` VARCHAR(50) COMMENT 'Loại provider',
    `name` VARCHAR(50) COMMENT 'Tên provider',
    `fields` JSON COMMENT 'Danh sách trường provider (định dạng JSON)',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sắp xếp',
    `creator` BIGINT COMMENT 'Người tạo',
    `create_date` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'Người cập nhật',
    `update_date` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_provider_model_type` (`model_type`) COMMENT 'Tạo index loại mô hình, dùng để tìm nhanh tất cả thông tin provider của loại cụ thể'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng cấu hình mô hình';

-- Bảng cấu hình mô hình
DROP TABLE IF EXISTS `ai_model_config`;
CREATE TABLE `ai_model_config` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Khóa chính',
    `model_type` VARCHAR(20) COMMENT 'Loại mô hình(Memory/ASR/VAD/LLM/TTS)',
    `model_code` VARCHAR(50) COMMENT 'Mã mô hình (như AliLLM、DoubaoTTS)',
    `model_name` VARCHAR(50) COMMENT 'Tên mô hình',
    `is_default` TINYINT(1) DEFAULT 0 COMMENT 'Có phải cấu hình mặc định không (0 không 1 có)',
    `is_enabled` TINYINT(1) DEFAULT 0 COMMENT 'Có bật không',
    `config_json` JSON COMMENT 'Cấu hình mô hình (định dạng JSON)',
    `doc_link` VARCHAR(200) COMMENT 'Liên kết tài liệu chính thức',
    `remark` VARCHAR(255) COMMENT 'Ghi chú',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sắp xếp',
    `creator` BIGINT COMMENT 'Người tạo',
    `create_date` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'Người cập nhật',
    `update_date` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_config_model_type` (`model_type`) COMMENT 'Tạo index loại mô hình, dùng để tìm nhanh tất cả thông tin cấu hình của loại cụ thể'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng cấu hình mô hình';

-- Bảng giọng TTS
DROP TABLE IF EXISTS `ai_tts_voice`;
CREATE TABLE `ai_tts_voice` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Khóa chính',
    `tts_model_id` VARCHAR(32) COMMENT 'Khóa chính mô hình TTS tương ứng',
    `name` VARCHAR(20) COMMENT 'Tên giọng',
    `tts_voice` VARCHAR(50) COMMENT 'Mã giọng',
    `languages` VARCHAR(50) COMMENT 'Ngôn ngữ',
    `voice_demo` VARCHAR(500) DEFAULT NULL COMMENT 'Demo giọng',
    `remark` VARCHAR(255) COMMENT 'Ghi chú',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sắp xếp',
    `creator` BIGINT COMMENT 'Người tạo',
    `create_date` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'Người cập nhật',
    `update_date` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_tts_voice_tts_model_id` (`tts_model_id`) COMMENT 'Tạo index khóa chính mô hình TTS, dùng để tìm nhanh thông tin giọng của mô hình tương ứng'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng giọng TTS';

-- Bảng template cấu hình agent
DROP TABLE IF EXISTS `ai_agent_template`;
CREATE TABLE `ai_agent_template` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Định danh duy nhất agent',
    `agent_code` VARCHAR(36) COMMENT 'Mã agent',
    `agent_name` VARCHAR(64) COMMENT 'Tên agent',
    `asr_model_id` VARCHAR(32) COMMENT 'Định danh mô hình nhận dạng giọng nói',
    `vad_model_id` VARCHAR(64) COMMENT 'Định danh phát hiện hoạt động giọng nói',
    `llm_model_id` VARCHAR(32) COMMENT 'Định danh mô hình ngôn ngữ lớn',
    `tts_model_id` VARCHAR(32) COMMENT 'Định danh mô hình tổng hợp giọng nói',
    `tts_voice_id` VARCHAR(32) COMMENT 'Định danh giọng',
    `mem_model_id` VARCHAR(32) COMMENT 'Định danh mô hình nhớ',
    `intent_model_id` VARCHAR(32) COMMENT 'Định danh mô hình ý định',
    `system_prompt` TEXT COMMENT 'Tham số thiết lập vai trò',
    `lang_code` VARCHAR(10) COMMENT 'Mã ngôn ngữ',
    `language` VARCHAR(10) COMMENT 'Ngôn ngữ tương tác',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Trọng số sắp xếp',
    `creator` BIGINT COMMENT 'ID người tạo',
    `created_at` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'ID người cập nhật',
    `updated_at` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng template cấu hình agent';

-- Bảng cấu hình agent
DROP TABLE IF EXISTS `ai_agent`;
CREATE TABLE `ai_agent` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Định danh duy nhất agent',
    `user_id` BIGINT COMMENT 'ID người dùng sở hữu',
    `agent_code` VARCHAR(36) COMMENT 'Mã agent',
    `agent_name` VARCHAR(64) COMMENT 'Tên agent',
    `asr_model_id` VARCHAR(32) COMMENT 'Định danh mô hình nhận dạng giọng nói',
    `vad_model_id` VARCHAR(64) COMMENT 'Định danh phát hiện hoạt động giọng nói',
    `llm_model_id` VARCHAR(32) COMMENT 'Định danh mô hình ngôn ngữ lớn',
    `tts_model_id` VARCHAR(32) COMMENT 'Định danh mô hình tổng hợp giọng nói',
    `tts_voice_id` VARCHAR(32) COMMENT 'Định danh giọng',
    `mem_model_id` VARCHAR(32) COMMENT 'Định danh mô hình nhớ',
    `intent_model_id` VARCHAR(32) COMMENT 'Định danh mô hình ý định',
    `system_prompt` TEXT COMMENT 'Tham số thiết lập vai trò',
    `lang_code` VARCHAR(10) COMMENT 'Mã ngôn ngữ',
    `language` VARCHAR(10) COMMENT 'Ngôn ngữ tương tác',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Trọng số sắp xếp',
    `creator` BIGINT COMMENT 'ID người tạo',
    `created_at` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'ID người cập nhật',
    `updated_at` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_agent_user_id` (`user_id`) COMMENT 'Tạo index người dùng, dùng để tìm nhanh thông tin agent của người dùng'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng cấu hình agent';

-- Bảng thông tin thiết bị
DROP TABLE IF EXISTS `ai_device`;
CREATE TABLE `ai_device` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Định danh duy nhất thiết bị',
    `user_id` BIGINT COMMENT 'ID người dùng liên kết',
    `mac_address` VARCHAR(50) COMMENT 'Địa chỉ MAC',
    `last_connected_at` DATETIME COMMENT 'Thời gian kết nối cuối',
    `auto_update` TINYINT UNSIGNED DEFAULT 0 COMMENT 'Công tắc tự động cập nhật (0 tắt/1 bật)',
    `board` VARCHAR(50) COMMENT 'Model phần cứng thiết bị',
    `alias` VARCHAR(64) DEFAULT NULL COMMENT 'Tên thiết bị',
    `agent_id` VARCHAR(32) COMMENT 'ID agent',
    `app_version` VARCHAR(20) COMMENT 'Số phiên bản firmware',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sắp xếp',
    `creator` BIGINT COMMENT 'Người tạo',
    `create_date` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'Người cập nhật',
    `update_date` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_device_created_at` (`mac_address`) COMMENT 'Tạo index mac, dùng để tìm nhanh thông tin thiết bị'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng thông tin thiết bị';

-- Bảng nhận dạng vân tay giọng nói
DROP TABLE IF EXISTS `ai_voiceprint`;
CREATE TABLE `ai_voiceprint` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Định danh duy nhất vân tay giọng nói',
    `name` VARCHAR(64) COMMENT 'Tên vân tay giọng nói',
    `user_id` BIGINT COMMENT 'ID người dùng (liên kết bảng người dùng)',
    `agent_id` VARCHAR(32) COMMENT 'ID agent liên kết',
    `agent_code` VARCHAR(36) COMMENT 'Mã agent liên kết',
    `agent_name` VARCHAR(36) COMMENT 'Tên agent liên kết',
    `description` VARCHAR(255) COMMENT 'Mô tả vân tay giọng nói',
    `embedding` LONGTEXT COMMENT 'Vector đặc trưng vân tay giọng nói (định dạng mảng JSON)',
    `memory` TEXT COMMENT 'Dữ liệu nhớ liên kết',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Trọng số sắp xếp',
    `creator` BIGINT COMMENT 'ID người tạo',
    `created_at` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'ID người cập nhật',
    `updated_at` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng nhận dạng vân tay giọng nói';

-- Bảng lịch sử hội thoại
DROP TABLE IF EXISTS `ai_chat_history`;
CREATE TABLE `ai_chat_history` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Số hội thoại',
    `user_id` BIGINT COMMENT 'Số người dùng',
    `agent_id` VARCHAR(32) DEFAULT NULL COMMENT 'Vai trò chat',
    `device_id` VARCHAR(32) DEFAULT NULL COMMENT 'Số thiết bị',
    `message_count` INT COMMENT 'Tổng hợp thông tin',
    `creator` BIGINT COMMENT 'Người tạo',
    `create_date` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'Người cập nhật',
    `update_date` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng lịch sử hội thoại';

-- Bảng thông tin hội thoại
DROP TABLE IF EXISTS `ai_chat_message`;
CREATE TABLE `ai_chat_message` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Định danh duy nhất bản ghi hội thoại',
    `user_id` BIGINT COMMENT 'Định danh duy nhất người dùng',
    `chat_id` VARCHAR(64) COMMENT 'ID lịch sử hội thoại',
    `role` ENUM('user', 'assistant') COMMENT 'Vai trò (người dùng hoặc trợ lý)',
    `content` TEXT COMMENT 'Nội dung hội thoại',
    `prompt_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Số token prompt',
    `total_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Tổng số token',
    `completion_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Số token hoàn thành',
    `prompt_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Thời gian prompt (mili giây)',
    `total_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Tổng thời gian (mili giây)',
    `completion_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Thời gian hoàn thành (mili giây)',
    `creator` BIGINT COMMENT 'Người tạo',
    `create_date` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'Người cập nhật',
    `update_date` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_chat_message_user_id_chat_id_role` (`user_id`, `chat_id`) COMMENT 'Index kết hợp ID người dùng, ID phiên chat và vai trò, dùng để tìm nhanh bản ghi hội thoại',
    INDEX `idx_ai_chat_message_created_at` (`create_date`) COMMENT 'Index thời gian tạo, dùng để sắp xếp hoặc tìm bản ghi hội thoại theo thời gian'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng thông tin hội thoại';
