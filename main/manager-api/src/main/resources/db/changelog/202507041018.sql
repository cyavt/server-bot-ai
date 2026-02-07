DROP TABLE IF EXISTS ai_agent_voice_print;
create table ai_agent_voice_print (
  id varchar(32) NOT NULL COMMENT 'ID vân tay giọng nói',
  agent_id varchar(32)  NOT NULL COMMENT 'ID agent liên kết',
  source_name varchar(50)  NOT NULL COMMENT 'Tên người nguồn vân tay giọng nói',
  introduce varchar(200) COMMENT 'Mô tả người nguồn vân tay giọng nói này',
  create_date DATETIME COMMENT 'Thời gian tạo',
  creator bigint COMMENT 'Người tạo',
  update_date DATETIME COMMENT 'Thời gian sửa',
  updater bigint COMMENT 'Người sửa',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Bảng vân tay giọng nói agent'