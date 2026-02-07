delete from `ai_model_config` where id = 'LLM_XunfeiSparkLLM';
INSERT INTO `ai_model_config` VALUES ('LLM_XunfeiSparkLLM', 'LLM', 'Mô hình nhận thức lớn Tia Lửa Tín Phi', 'Mô hình nhận thức lớn Tia Lửa Tín Phi', 0, 1, '{"type": "openai", "model_name": "generalv3.5", "base_url": "https://spark-api-open.xf-yun.com/v1", "api_password": "api_password của bạn", "temperature": 0.5, "max_tokens": 2048, "top_p": 1.0, "frequency_penalty": 0.0}', 'https://www.xfyun.cn/doc/spark/HTTP%E8%B0%83%E7%94%A8%E6%96%87%E6%A1%A3.html', 'Mô hình nhận thức lớn Tia Lửa Tín Phi, hỗ trợ đa hội thoại, tạo văn bản và các chức năng khác', 14, NULL, NULL, NULL, NULL);

-- Cập nhật tài liệu hướng dẫn cấu hình mô hình nhận thức lớn Tia Lửa Tín Phi
UPDATE `ai_model_config` SET
`doc_link` = 'https://www.xfyun.cn/doc/spark/HTTP%E8%B0%83%E7%94%A8%E6%96%87%E6%A1%A3.html',
`remark` = 'Hướng dẫn cấu hình mô hình nhận thức lớn Tia Lửa Tín Phi：
1. Đăng nhập nền tảng mở Tín Phi https://www.xfyun.cn/, mỗi mô hình tương ứng với một api_password, khi thay đổi mô hình cần xem api_password của mô hình tương ứng
2. Tạo ứng dụng mô hình nhận thức lớn Tia Lửa để lấy API Password
3. Giải thích tham số：
   - api_password: API Password, lấy được sau khi tạo ứng dụng trên nền tảng mở Tín Phi
   - model_name: Tên mô hình, hỗ trợ các phiên bản generalv3.5、generalv3, v.v.
   - base_url: Địa chỉ API, mặc định https://spark-api-open.xf-yun.com/v1
   - temperature: Tham số nhiệt độ, điều khiển tính ngẫu nhiên của tạo, phạm vi 0-1, mặc định 0.5
   - max_tokens: Số token đầu ra tối đa, mặc định 2048
   - top_p: Tham số lấy mẫu cốt lõi, điều khiển tính đa dạng từ vựng, mặc định 1.0
   - frequency_penalty: Phạt tần suất, giảm nội dung lặp lại, mặc định 0.0
4. Mỗi mô hình tương ứng với một api_password, khi thay đổi mô hình cần xem api_password của mô hình tương ứng。
' WHERE `id` = 'LLM_XunfeiSparkLLM';