-- Thêm server.ota, dùng để cấu hình địa chỉ ota

delete from `sys_params` where id = 100;
delete from `sys_params` where id = 101;

delete from `sys_params` where id = 106;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (106, 'server.websocket', 'null', 'string', 1, 'Địa chỉ websocket, nhiều địa chỉ dùng ; phân cách');

delete from `sys_params` where id = 107;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (107, 'server.ota', 'null', 'string', 1, 'Địa chỉ ota');


-- Thêm bảng thông tin firmware
CREATE TABLE IF NOT EXISTS `ai_ota` (
  `id` varchar(32) NOT NULL COMMENT 'ID',
  `firmware_name` varchar(100) DEFAULT NULL COMMENT 'Tên firmware',
  `type` varchar(50) DEFAULT NULL COMMENT 'Loại firmware',
  `version` varchar(50) DEFAULT NULL COMMENT 'Số phiên bản',
  `size` bigint DEFAULT NULL COMMENT 'Kích thước file (byte)',
  `remark` varchar(500) DEFAULT NULL COMMENT 'Ghi chú/Giải thích',
  `firmware_path` varchar(255) DEFAULT NULL COMMENT 'Đường dẫn firmware',
  `sort` int unsigned DEFAULT '0' COMMENT 'Sắp xếp',
  `updater` bigint DEFAULT NULL COMMENT 'Người cập nhật',
  `update_date` datetime DEFAULT NULL COMMENT 'Thời gian cập nhật',
  `creator` bigint DEFAULT NULL COMMENT 'Người tạo',
  `create_date` datetime DEFAULT NULL COMMENT 'Thời gian tạo',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng thông tin firmware';

update ai_device set auto_update = 1;
