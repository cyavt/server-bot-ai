-- Thêm tham số cần thiết cho chức năng đăng ký SMS điện thoại
delete from sys_params where id in (108, 109, 110, 111, 112, 113, 114, 115);
delete from sys_params where id in (610, 611, 612, 613);
INSERT INTO sys_params
(id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
    VALUES
(108, 'server.name', 'xiaozhi-esp32-server', 'string', 1, 'Tên hệ thống', NULL, NULL, NULL, NULL),
(109, 'server.beian_icp_num', 'null', 'string', 1, 'Số đăng ký ICP, điền null thì không thiết lập', NULL, NULL, NULL, NULL),
(110, 'server.beian_ga_num', 'null', 'string', 1, 'Số đăng ký công an, điền null thì không thiết lập', NULL, NULL, NULL, NULL),
(111, 'server.enable_mobile_register', 'false', 'boolean', 1, 'Có bật đăng ký điện thoại không', NULL, NULL, NULL, NULL),
(112, 'server.sms_max_send_count', '10', 'number', 1, 'Số tin nhắn SMS tối đa gửi mỗi số mỗi ngày', NULL, NULL, NULL, NULL),
(610, 'aliyun.sms.access_key_id', '', 'string', 1, 'access_key nền tảng Alibaba Cloud', NULL, NULL, NULL, NULL),
(611, 'aliyun.sms.access_key_secret', '', 'string', 1, 'access_key_secret nền tảng Alibaba Cloud', NULL, NULL, NULL, NULL),
(612, 'aliyun.sms.sign_name', '', 'string', 1, 'Chữ ký SMS Alibaba Cloud', NULL, NULL, NULL, NULL),
(613, 'aliyun.sms.sms_code_template_code', '', 'string', 1, 'Mẫu SMS Alibaba Cloud', NULL, NULL, NULL, NULL);

update sys_params set remark = 'Có cho phép người ngoài quản trị viên đăng ký không' where param_code = 'server.allow_user_register';

-- Thêm từ điển khu vực điện thoại
-- Chèn loại từ điển loại firmware
delete from `sys_dict_type` where `id` = 102;
INSERT INTO `sys_dict_type` (`id`, `dict_type`, `dict_name`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES 
(102, 'MOBILE_AREA', 'Khu vực điện thoại', 'Từ điển khu vực điện thoại', 0, 1, NOW(), 1, NOW());

-- Chèn dữ liệu từ điển loại firmware
delete from `sys_dict_data` where `dict_type_id` = 102;
INSERT INTO `sys_dict_data` (`id`, `dict_type_id`, `dict_label`, `dict_value`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES 
(102001, 102, 'Trung Quốc đại lục', '+86', 'Trung Quốc đại lục', 1, 1, NOW(), 1, NOW()),
(102002, 102, 'Hồng Kông Trung Quốc', '+852', 'Hồng Kông Trung Quốc', 2, 1, NOW(), 1, NOW()),
(102003, 102, 'Macau Trung Quốc', '+853', 'Macau Trung Quốc', 3, 1, NOW(), 1, NOW()),
(102004, 102, 'Đài Loan Trung Quốc', '+886', 'Đài Loan Trung Quốc', 4, 1, NOW(), 1, NOW()),
(102005, 102, 'Mỹ/Canada', '+1', 'Mỹ/Canada', 5, 1, NOW(), 1, NOW()),
(102006, 102, 'Anh', '+44', 'Anh', 6, 1, NOW(), 1, NOW()),
(102007, 102, 'Pháp', '+33', 'Pháp', 7, 1, NOW(), 1, NOW()),
(102008, 102, 'Ý', '+39', 'Ý', 8, 1, NOW(), 1, NOW()),
(102009, 102, 'Đức', '+49', 'Đức', 9, 1, NOW(), 1, NOW()),
(102010, 102, 'Ba Lan', '+48', 'Ba Lan', 10, 1, NOW(), 1, NOW()),
(102011, 102, 'Thụy Sĩ', '+41', 'Thụy Sĩ', 11, 1, NOW(), 1, NOW()),
(102012, 102, 'Tây Ban Nha', '+34', 'Tây Ban Nha', 12, 1, NOW(), 1, NOW()),
(102013, 102, 'Đan Mạch', '+45', 'Đan Mạch', 13, 1, NOW(), 1, NOW()),
(102014, 102, 'Malaysia', '+60', 'Malaysia', 14, 1, NOW(), 1, NOW()),
(102015, 102, 'Úc', '+61', 'Úc', 15, 1, NOW(), 1, NOW()),
(102016, 102, 'Indonesia', '+62', 'Indonesia', 16, 1, NOW(), 1, NOW()),
(102017, 102, 'Philippines', '+63', 'Philippines', 17, 1, NOW(), 1, NOW()),
(102018, 102, 'New Zealand', '+64', 'New Zealand', 18, 1, NOW(), 1, NOW()),
(102019, 102, 'Singapore', '+65', 'Singapore', 19, 1, NOW(), 1, NOW()),
(102020, 102, 'Thái Lan', '+66', 'Thái Lan', 20, 1, NOW(), 1, NOW()),
(102021, 102, 'Nhật Bản', '+81', 'Nhật Bản', 21, 1, NOW(), 1, NOW()),
(102022, 102, 'Hàn Quốc', '+82', 'Hàn Quốc', 22, 1, NOW(), 1, NOW()),
(102023, 102, 'Việt Nam', '+84', 'Việt Nam', 23, 1, NOW(), 1, NOW()),
(102024, 102, 'Ấn Độ', '+91', 'Ấn Độ', 24, 1, NOW(), 1, NOW()),
(102025, 102, 'Pakistan', '+92', 'Pakistan', 25, 1, NOW(), 1, NOW()),
(102026, 102, 'Nigeria', '+234', 'Nigeria', 26, 1, NOW(), 1, NOW()),
(102027, 102, 'Bangladesh', '+880', 'Bangladesh', 27, 1, NOW(), 1, NOW()),
(102028, 102, 'Ả Rập Saudi', '+966', 'Ả Rập Saudi', 28, 1, NOW(), 1, NOW()),
(102029, 102, 'UAE', '+971', 'UAE', 29, 1, NOW(), 1, NOW()),
(102030, 102, 'Brazil', '+55', 'Brazil', 30, 1, NOW(), 1, NOW()),
(102031, 102, 'Mexico', '+52', 'Mexico', 31, 1, NOW(), 1, NOW()),
(102032, 102, 'Chile', '+56', 'Chile', 32, 1, NOW(), 1, NOW()),
(102033, 102, 'Argentina', '+54', 'Argentina', 33, 1, NOW(), 1, NOW()),
(102034, 102, 'Ai Cập', '+20', 'Ai Cập', 34, 1, NOW(), 1, NOW()),
(102035, 102, 'Nam Phi', '+27', 'Nam Phi', 35, 1, NOW(), 1, NOW()),
(102036, 102, 'Kenya', '+254', 'Kenya', 36, 1, NOW(), 1, NOW()),
(102037, 102, 'Tanzania', '+255', 'Tanzania', 37, 1, NOW(), 1, NOW()),
(102038, 102, 'Kazakhstan', '+7', 'Kazakhstan', 38, 1, NOW(), 1, NOW());
