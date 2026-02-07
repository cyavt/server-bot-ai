-- Thêm cấu hình dịch vụ nhận dạng giọng nói streaming Tín Phi
delete from `ai_model_provider` where id = 'SYSTEM_ASR_XunfeiStream';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_XunfeiStream', 'ASR', 'xunfei_stream', 'Nhận dạng giọng nói streaming Tín Phi', '[{"key":"app_id","label":"ID ứng dụng","type":"string"},{"key":"api_key","label":"API_KEY","type":"password"},{"key":"api_secret","label":"API_SECRET","type":"password"},{"key":"domain","label":"Lĩnh vực nhận dạng","type":"string"},{"key":"language","label":"Ngôn ngữ nhận dạng","type":"string"},{"key":"accent","label":"Phương ngữ","type":"string"},{"key":"dwa","label":"Sửa đổi động","type":"string"},{"key":"output_dir","label":"Thư mục đầu ra","type":"string"}]', 18, 1, NOW(), 1, NOW());

delete from `ai_model_config` where id = 'ASR_XunfeiStream';
INSERT INTO `ai_model_config` VALUES ('ASR_XunfeiStream', 'ASR', 'Nhận dạng giọng nói streaming Tín Phi', 'Dịch vụ nhận dạng giọng nói streaming Tín Phi', 0, 1, '{"type": "xunfei_stream", "app_id": "", "api_key": "", "api_secret": "", "domain": "slm", "language": "zh_cn", "accent": "mandarin", "dwa": "wpgs", "output_dir": "tmp/"}', 'https://www.xfyun.cn/doc/spark/spark_zh_iat.html', 'Hỗ trợ nhận dạng giọng nói streaming thời gian thực, phù hợp với nhận dạng tiếng Trung phổ thông và nhiều phương ngữ', 21, NULL, NULL, NULL, NULL);

-- Cập nhật tài liệu hướng dẫn cấu hình mô hình nhận dạng giọng nói streaming Tín Phi
UPDATE `ai_model_config` SET
`doc_link` = 'https://www.xfyun.cn/doc/spark/spark_zh_iat.html',
`remark` = 'Hướng dẫn cấu hình nhận dạng giọng nói streaming Tín Phi：
1. Đăng nhập nền tảng mở Tín Phi https://www.xfyun.cn/
2. Tạo ứng dụng nhận dạng giọng nói để lấy APPID、APISecret、APIKey
3. Giải thích tham số：
   - app_id: ID ứng dụng, lấy được sau khi tạo ứng dụng trên nền tảng mở Tín Phi
   - api_key: Khóa API, dùng để xác thực giao diện
   - api_secret: Khóa API, dùng để tạo chữ ký
   - domain: Lĩnh vực nhận dạng, mặc định slm (chuyển đổi giọng nói thông minh)
   - language: Ngôn ngữ nhận dạng, mặc định zh_cn (tiếng Trung)
   - accent: Loại phương ngữ, mặc định mandarin (phổ thông), hỗ trợ cantonese (Quảng Đông), v.v.
   - dwa: Sửa đổi động, mặc định wpgs (bật sửa đổi động)
   - output_dir: Thư mục đầu ra file âm thanh, mặc định tmp/
4. Hỗ trợ nhận dạng streaming thời gian thực, phù hợp với các tình huống tương tác giọng nói thời gian thực
5. Hỗ trợ nhận dạng nhiều phương ngữ và ngôn ngữ
' WHERE `id` = 'ASR_XunfeiStream';