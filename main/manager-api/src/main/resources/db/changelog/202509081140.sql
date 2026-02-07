-- Thêm cấu hình tham số ngưỡng độ tương đồng nhận dạng vân tay giọng nói
delete from `sys_params` where id = 115;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark)
VALUES (115, 'server.voiceprint_similarity_threshold', '0.4', 'string', 1, 'Ngưỡng độ tương đồng nhận dạng vân tay giọng nói, phạm vi 0.0-1.0, mặc định 0.4, giá trị càng cao càng nghiêm ngặt');
