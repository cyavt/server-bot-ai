-- Thêm tham số khóa thuật toán mật mã quốc gia SM2
-- Dùng cho chức năng mã hóa/giải mã SM2 phía server

-- Thêm tham số khóa SM2
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES 
(120, 'server.public_key', '', 'string', 1, 'Khóa công khai SM2 của server'),
(121, 'server.private_key', '', 'string', 1, 'Khóa riêng tư SM2 của server');