-- File này dùng để khởi tạo dữ liệu tham số hệ thống, không cần thực thi thủ công, sẽ tự động thực thi khi khởi động dự án
-- --------------------------------------------------------
-- Khởi tạo cấu hình quản lý tham số
DROP TABLE IF EXISTS sys_params;
-- Quản lý tham số
create table sys_params
(
  id                   bigint NOT NULL COMMENT 'id',
  param_code           varchar(100) COMMENT 'Mã tham số',
  param_value          varchar(2000) COMMENT 'Giá trị tham số',
  value_type           varchar(20) default 'string' COMMENT 'Loại giá trị：string-chuỗi，number-số，boolean-boolean，array-mảng',
  param_type           tinyint unsigned default 1 COMMENT 'Loại   0：Tham số hệ thống   1：Tham số phi hệ thống',
  remark               varchar(200) COMMENT 'Ghi chú',
  creator              bigint COMMENT 'Người tạo',
  create_date          datetime COMMENT 'Thời gian tạo',
  updater              bigint COMMENT 'Người cập nhật',
  update_date          datetime COMMENT 'Thời gian cập nhật',
  primary key (id),
  unique key uk_param_code (param_code)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Quản lý tham số';

-- Cấu hình máy chủ
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (100, 'server.ip', '0.0.0.0', 'string', 1, 'Địa chỉ IP lắng nghe của máy chủ');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (101, 'server.port', '8000', 'number', 1, 'Cổng lắng nghe của máy chủ');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (102, 'server.secret', 'null', 'string', 1, 'Khóa máy chủ');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (201, 'log.log_format', '<green>{time:YYMMDD HH:mm:ss}</green>[<light-blue>{version}-{selected_module}</light-blue>][<light-blue>{extra[tag]}</light-blue>]-<level>{level}</level>-<light-green>{message}</light-green>', 'string', 1, 'Định dạng nhật ký console');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (202, 'log.log_format_file', '{time:YYYY-MM-DD HH:mm:ss} - {version}_{selected_module} - {name} - {level} - {extra[tag]} - {message}', 'string', 1, 'Định dạng nhật ký file');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (203, 'log.log_level', 'INFO', 'string', 1, 'Mức độ nhật ký');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (204, 'log.log_dir', 'tmp', 'string', 1, 'Thư mục nhật ký');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (205, 'log.log_file', 'server.log', 'string', 1, 'Tên file nhật ký');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (206, 'log.data_dir', 'data', 'string', 1, 'Thư mục dữ liệu');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (301, 'delete_audio', 'true', 'boolean', 1, 'Có xóa file âm thanh sau khi sử dụng không');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (302, 'close_connection_no_voice_time', '120', 'number', 1, 'Thời gian ngắt kết nối khi không có giọng nói đầu vào (giây)');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (303, 'tts_timeout', '10', 'number', 1, 'Thời gian chờ yêu cầu TTS (giây)');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (304, 'enable_wakeup_words_response_cache', 'false', 'boolean', 1, 'Có bật tăng tốc từ khóa đánh thức không');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (305, 'enable_greeting', 'true', 'boolean', 1, 'Có bật phản hồi mở đầu không');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (306, 'enable_stop_tts_notify', 'false', 'boolean', 1, 'Có bật âm thanh thông báo kết thúc không');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (307, 'stop_tts_notify_voice', 'config/assets/tts_notify.mp3', 'string', 1, 'Đường dẫn file âm thanh thông báo kết thúc');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (308, 'exit_commands', '退出;关闭', 'array', 1, 'Danh sách lệnh thoát');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (309, 'xiaozhi', '{
  "type": "hello",
  "version": 1,
  "transport": "websocket",
  "audio_params": {
    "format": "opus",
    "sample_rate": 16000,
    "channels": 1,
    "frame_duration": 60
  }
}', 'json', 1, 'Loại xiaozhi');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (310, 'wakeup_words', '你好小智;你好小志;小爱同学;你好小鑫;你好小新;小美同学;小龙小龙;喵喵同学;小滨小滨;小冰小冰', 'array', 1, 'Danh sách từ khóa đánh thức, dùng để nhận dạng từ khóa đánh thức');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (400, 'plugins.get_weather.api_key', 'a861d0d5e7bf4ee1a83d9a9e4f96d4da', 'string', 1, 'Khóa API plugin thời tiết');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (401, 'plugins.get_weather.default_location', '广州', 'string', 1, 'Thành phố mặc định của plugin thời tiết');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (410, 'plugins.get_news.default_rss_url', 'https://www.chinanews.com.cn/rss/society.xml', 'string', 1, 'Địa chỉ RSS mặc định của plugin tin tức');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (411, 'plugins.get_news.category_urls', '{"society":"https://www.chinanews.com.cn/rss/society.xml","world":"https://www.chinanews.com.cn/rss/world.xml","finance":"https://www.chinanews.com.cn/rss/finance.xml"}', 'json', 1, 'Địa chỉ RSS phân loại của plugin tin tức');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (421, 'plugins.home_assistant.devices', '客厅,玩具灯,switch.cuco_cn_460494544_cp1_on_p_2_1;卧室,台灯,switch.iot_cn_831898993_socn1_on_p_2_1', 'array', 1, 'Danh sách thiết bị Home Assistant');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (422, 'plugins.home_assistant.base_url', 'http://homeassistant.local:8123', 'string', 1, 'Địa chỉ máy chủ Home Assistant');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (423, 'plugins.home_assistant.api_key', '你的home assistant api访问令牌', 'string', 1, 'Khóa API Home Assistant');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (430, 'plugins.play_music.music_dir', './music', 'string', 1, 'Đường dẫn lưu trữ file nhạc');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (431, 'plugins.play_music.music_ext', 'mp3;wav;p3', 'array', 1, 'Loại file nhạc');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (432, 'plugins.play_music.refresh_time', '300', 'number', 1, 'Khoảng thời gian làm mới danh sách nhạc (giây)');
