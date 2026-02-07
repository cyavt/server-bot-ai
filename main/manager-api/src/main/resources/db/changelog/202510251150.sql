-- Bảng cơ sở tri thức
DROP TABLE IF EXISTS `ai_rag_dataset`;
CREATE TABLE `ai_rag_dataset` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Định danh duy nhất',
    `dataset_id` VARCHAR(64) NOT NULL COMMENT 'ID cơ sở tri thức',
    `rag_model_id` VARCHAR(64) COMMENT 'ID cấu hình mô hình RAG',
    `name` VARCHAR(100) NOT NULL COMMENT 'Tên cơ sở tri thức',
    `description` TEXT COMMENT 'Mô tả cơ sở tri thức',
    `status` TINYINT(1) DEFAULT 1 COMMENT 'Trạng thái：0 tắt 1 bật',
    `creator` BIGINT COMMENT 'Người tạo',
    `created_at` DATETIME COMMENT 'Thời gian tạo',
    `updater` BIGINT COMMENT 'Người cập nhật',
    `updated_at` DATETIME COMMENT 'Thời gian cập nhật',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_dataset_id` (`dataset_id`),
    INDEX `idx_ai_rag_dataset_status` (`status`),
    INDEX `idx_ai_rag_dataset_creator` (`creator`),
    INDEX `idx_ai_rag_dataset_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng cơ sở tri thức';