-- Khởi tạo bản ghi chat agent
DROP TABLE IF EXISTS ai_chat_history;
DROP TABLE IF EXISTS ai_chat_message;
DROP TABLE IF EXISTS ai_agent_chat_history;
CREATE TABLE ai_agent_chat_history
(
    id          BIGINT AUTO_INCREMENT COMMENT 'ID khóa chính' PRIMARY KEY,
    mac_address VARCHAR(50) COMMENT 'Địa chỉ MAC',
    agent_id VARCHAR(32) COMMENT 'ID agent',
    session_id  VARCHAR(50) COMMENT 'ID phiên',
    chat_type   TINYINT(3) COMMENT 'Loại tin nhắn: 1-người dùng, 2-agent',
    content     VARCHAR(1024) COMMENT 'Nội dung chat',
    audio_id    VARCHAR(32) COMMENT 'ID âm thanh',
    created_at  DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL COMMENT 'Thời gian tạo',
    updated_at  DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL ON UPDATE CURRENT_TIMESTAMP(3) COMMENT 'Thời gian cập nhật',
    INDEX idx_ai_agent_chat_history_mac (mac_address),
    INDEX idx_ai_agent_chat_history_session_id (session_id),
    INDEX idx_ai_agent_chat_history_agent_id (agent_id),
    INDEX idx_ai_agent_chat_history_agent_session_created (agent_id, session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT 'Bảng bản ghi chat agent';

DROP TABLE IF EXISTS ai_agent_chat_audio;
CREATE TABLE ai_agent_chat_audio
(
    id          VARCHAR(32) COMMENT 'ID khóa chính' PRIMARY KEY,
    audio       LONGBLOB COMMENT 'Dữ liệu âm thanh opus'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT 'Bảng dữ liệu âm thanh chat agent'; 