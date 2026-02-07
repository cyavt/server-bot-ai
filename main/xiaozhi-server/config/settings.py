import os
from config.config_loader import read_config, get_project_dir, load_config


default_config_file = "config.yaml"
config_file_valid = False


def check_config_file():
    global config_file_valid
    if config_file_valid:
        return
    """
    Kiểm tra cấu hình đơn giản hóa, chỉ nhắc nhở người dùng về việc sử dụng file cấu hình
    """
    custom_config_file = get_project_dir() + "data/." + default_config_file
    if not os.path.exists(custom_config_file):
        raise FileNotFoundError(
            "Không tìm thấy file data/.config.yaml, vui lòng xác nhận file cấu hình này có tồn tại theo hướng dẫn"
        )

    # Kiểm tra có đọc cấu hình từ API không
    config = load_config()
    if config.get("read_config_from_api", False):
        print("Đọc cấu hình từ API")
        old_config_origin = read_config(custom_config_file)
        if old_config_origin.get("selected_module") is not None:
            error_msg = "File cấu hình của bạn có vẻ vừa chứa cấu hình bảng điều khiển thông minh vừa chứa cấu hình local:\n"
            error_msg += "\nĐề xuất:\n"
            error_msg += "1. Sao chép file config_from_api.yaml ở thư mục gốc vào data, đổi tên thành .config.yaml\n"
            error_msg += "2. Cấu hình địa chỉ interface và secret theo hướng dẫn\n"
            raise ValueError(error_msg)
    config_file_valid = True
