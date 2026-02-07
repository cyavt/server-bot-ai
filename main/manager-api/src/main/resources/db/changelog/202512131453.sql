-- Xóa tham số module server có bật xác thực token không
delete from `sys_params` where param_code = 'server.auth.enabled';

-- Thêm tham số module server có bật xác thực token không
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES 
(122, 'server.auth.enabled', 'true', 'boolean', 1, 'Module server có bật xác thực token không');