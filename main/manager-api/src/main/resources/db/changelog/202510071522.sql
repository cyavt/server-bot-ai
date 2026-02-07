-- Bảng clone giọng nói
DROP TABLE IF EXISTS `ai_voice_clone`;
CREATE TABLE `ai_voice_clone` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Định danh duy nhất',
    `name` VARCHAR(64) COMMENT 'Tên giọng nói',
    `model_id` VARCHAR(32) COMMENT 'ID mô hình',
    `voice_id` VARCHAR(32) COMMENT 'ID giọng nói',
    `user_id` BIGINT COMMENT 'ID người dùng (liên kết bảng người dùng)',
    `voice` LONGBLOB COMMENT 'Giọng nói',
    `train_status` TINYINT(1) DEFAULT 0 COMMENT 'Trạng thái huấn luyện：0 chờ huấn luyện 1 đang huấn luyện 2 huấn luyện thành công 3 huấn luyện thất bại',
    `train_error` VARCHAR(255) COMMENT 'Nguyên nhân lỗi huấn luyện',
    `creator` BIGINT COMMENT 'ID người tạo',
    `create_date` DATETIME COMMENT 'Thời gian tạo',
    PRIMARY KEY (`id`),
    INDEX idx_ai_voice_clone_user_id_model_id_train_status (model_id,user_id, train_status),
    INDEX idx_ai_voice_clone_voice_id (voice_id),
    INDEX idx_ai_voice_clone_user_id (user_id),
    INDEX idx_ai_voice_clone_model_id_voice_id (model_id, voice_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng clone giọng nói';