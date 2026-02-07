-- Thêm cấu hình tham số địa chỉ giao diện vân tay giọng nói
delete from `sys_params` where id = 114;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark)
VALUES (114, 'server.voice_print', 'null', 'string', 1, 'Địa chỉ giao diện vân tay giọng nói');