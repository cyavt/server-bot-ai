DROP TABLE IF EXISTS sys_user;
DROP TABLE IF EXISTS sys_params;
DROP TABLE IF EXISTS sys_user_token;
DROP TABLE IF EXISTS sys_dict_type;
DROP TABLE IF EXISTS sys_dict_data;

-- Người dùng hệ thống
CREATE TABLE sys_user (
  id bigint NOT NULL COMMENT 'id',
  username varchar(50) NOT NULL COMMENT 'Tên người dùng',
  password varchar(100) COMMENT 'Mật khẩu',
  super_admin tinyint unsigned COMMENT 'Quản trị viên siêu cấp   0：Không   1：Có',
  status tinyint COMMENT 'Trạng thái  0：Tắt   1：Bình thường',
  create_date datetime COMMENT 'Thời gian tạo',
  updater bigint COMMENT 'Người cập nhật',
  creator bigint COMMENT 'Người tạo',
  update_date datetime COMMENT 'Thời gian cập nhật',
  primary key (id),
  unique key uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Người dùng hệ thống';

-- Token người dùng hệ thống
CREATE TABLE sys_user_token (
  id bigint NOT NULL COMMENT 'id',
  user_id bigint NOT NULL COMMENT 'ID người dùng',
  token varchar(100) NOT NULL COMMENT 'Token người dùng',
  expire_date datetime COMMENT 'Thời gian hết hạn',
  update_date datetime COMMENT 'Thời gian cập nhật',
  create_date datetime COMMENT 'Thời gian tạo',
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  UNIQUE KEY token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Token người dùng hệ thống';

-- Quản lý tham số
create table sys_params
(
  id                   bigint NOT NULL COMMENT 'id',
  param_code           varchar(32) COMMENT 'Mã tham số',
  param_value          varchar(2000) COMMENT 'Giá trị tham số',
  param_type           tinyint unsigned default 1 COMMENT 'Loại   0：Tham số hệ thống   1：Tham số không phải hệ thống',
  remark               varchar(200) COMMENT 'Ghi chú',
  creator              bigint COMMENT 'Người tạo',
  create_date          datetime COMMENT 'Thời gian tạo',
  updater              bigint COMMENT 'Người cập nhật',
  update_date          datetime COMMENT 'Thời gian cập nhật',
  primary key (id),
  unique key uk_param_code (param_code)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Quản lý tham số';

-- Loại từ điển
create table sys_dict_type
(
    id                   bigint NOT NULL COMMENT 'id',
    dict_type            varchar(100) NOT NULL COMMENT 'Loại từ điển',
    dict_name            varchar(255) NOT NULL COMMENT 'Tên từ điển',
    remark               varchar(255) COMMENT 'Ghi chú',
    sort                 int unsigned COMMENT 'Sắp xếp',
    creator              bigint COMMENT 'Người tạo',
    create_date          datetime COMMENT 'Thời gian tạo',
    updater              bigint COMMENT 'Người cập nhật',
    update_date          datetime COMMENT 'Thời gian cập nhật',
    primary key (id),
    UNIQUE KEY(dict_type)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Loại từ điển';

-- Dữ liệu từ điển
create table sys_dict_data
(
    id                   bigint NOT NULL COMMENT 'id',
    dict_type_id         bigint NOT NULL COMMENT 'ID loại từ điển',
    dict_label           varchar(255) NOT NULL COMMENT 'Nhãn từ điển',
    dict_value           varchar(255) COMMENT 'Giá trị từ điển',
    remark               varchar(255) COMMENT 'Ghi chú',
    sort                 int unsigned COMMENT 'Sắp xếp',
    creator              bigint COMMENT 'Người tạo',
    create_date          datetime COMMENT 'Thời gian tạo',
    updater              bigint COMMENT 'Người cập nhật',
    update_date          datetime COMMENT 'Thời gian cập nhật',
    primary key (id),
    unique key uk_dict_type_value (dict_type_id, dict_value),
    key idx_sort (sort)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Dữ liệu từ điển';