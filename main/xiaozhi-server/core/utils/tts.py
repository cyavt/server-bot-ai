import os
import re
import sys
import importlib

from config.logger import setup_logging
from core.utils.textUtils import check_emoji

logger = setup_logging()

punctuation_set = {
    "，",
    ",",  # Dấu phẩy tiếng Trung + dấu phẩy tiếng Anh
    "。",
    ".",  # Dấu chấm tiếng Trung + dấu chấm tiếng Anh
    "！",
    "!",  # Dấu chấm than tiếng Trung + dấu chấm than tiếng Anh
    """,
    """,
    '"',  # Dấu ngoặc kép tiếng Trung + dấu ngoặc kép tiếng Anh
    "：",
    ":",  # Dấu hai chấm tiếng Trung + dấu hai chấm tiếng Anh
    "-",
    "－",  # Dấu gạch ngang tiếng Anh + dấu gạch ngang toàn bộ tiếng Trung
    "、",  # Dấu phẩy trên tiếng Trung
    "[",
    "]",  # Dấu ngoặc vuông
    "【",
    "】",  # Dấu ngoặc vuông tiếng Trung
    "~",  # Dấu sóng
}

def create_instance(class_name, *args, **kwargs):
    # Tạo instance TTS
    if os.path.exists(os.path.join('core', 'providers', 'tts', f'{class_name}.py')):
        lib_name = f'core.providers.tts.{class_name}'
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f'{lib_name}')
        return sys.modules[lib_name].TTSProvider(*args, **kwargs)

    raise ValueError(f"Loại TTS không được hỗ trợ: {class_name}，vui lòng kiểm tra xem type của cấu hình này có được thiết lập đúng không")


class MarkdownCleaner:
    """
    Đóng gói logic làm sạch Markdown: chỉ cần dùng MarkdownCleaner.clean_markdown(text) là được
    """
    # Ký tự công thức
    NORMAL_FORMULA_CHARS = re.compile(r'[a-zA-Z\\^_{}\+\-\(\)\[\]=]')

    @staticmethod
    def _replace_inline_dollar(m: re.Match) -> str:
        """
        Chỉ cần bắt được "$...$" hoàn chỉnh:
          - Nếu bên trong có ký tự công thức điển hình => bỏ $ hai bên
          - Ngược lại (số thuần/tiền tệ v.v.) => giữ "$...$"
        """
        content = m.group(1)
        if MarkdownCleaner.NORMAL_FORMULA_CHARS.search(content):
            return content
        else:
            return m.group(0)

    @staticmethod
    def _replace_table_block(match: re.Match) -> str:
        """
        Khi khớp với một khối bảng hoàn chỉnh, gọi lại hàm này.
        """
        block_text = match.group('table_block')
        lines = block_text.strip('\n').split('\n')

        parsed_table = []
        for line in lines:
            line_stripped = line.strip()
            if re.match(r'^\|\s*[-:]+\s*(\|\s*[-:]+\s*)+\|?$', line_stripped):
                continue
            columns = [col.strip() for col in line_stripped.split('|') if col.strip() != '']
            if columns:
                parsed_table.append(columns)

        if not parsed_table:
            return ""

        headers = parsed_table[0]
        data_rows = parsed_table[1:] if len(parsed_table) > 1 else []

        lines_for_tts = []
        if len(parsed_table) == 1:
            # Chỉ có một dòng
            only_line_str = ", ".join(parsed_table[0])
            lines_for_tts.append(f"Bảng một dòng: {only_line_str}")
        else:
            lines_for_tts.append(f"Tiêu đề là: {', '.join(headers)}")
            for i, row in enumerate(data_rows, start=1):
                row_str_list = []
                for col_index, cell_val in enumerate(row):
                    if col_index < len(headers):
                        row_str_list.append(f"{headers[col_index]} = {cell_val}")
                    else:
                        row_str_list.append(cell_val)
                lines_for_tts.append(f"Dòng {i}: {', '.join(row_str_list)}")

        return "\n".join(lines_for_tts) + "\n"

    # Biên dịch trước tất cả biểu thức chính quy (sắp xếp theo tần suất thực thi)
    # Ở đây cần đặt các phương thức tĩnh replace_xxx ở đầu để có thể tham chiếu đúng trong danh sách.
    REGEXES = [
        (re.compile(r'```.*?```', re.DOTALL), ''),  # Khối mã
        (re.compile(r'^#+\s*', re.MULTILINE), ''),  # Tiêu đề
        (re.compile(r'(\*\*|__)(.*?)\1'), r'\2'),  # In đậm
        (re.compile(r'(\*|_)(?=\S)(.*?)(?<=\S)\1'), r'\2'),  # In nghiêng
        (re.compile(r'!\[.*?\]\(.*?\)'), ''),  # Hình ảnh
        (re.compile(r'\[(.*?)\]\(.*?\)'), r'\1'),  # Liên kết
        (re.compile(r'^\s*>+\s*', re.MULTILINE), ''),  # Trích dẫn
        (
            re.compile(r'(?P<table_block>(?:^[^\n]*\|[^\n]*\n)+)', re.MULTILINE),
            _replace_table_block
        ),
        (re.compile(r'^\s*[*+-]\s*', re.MULTILINE), '- '),  # Danh sách
        (re.compile(r'\$\$.*?\$\$', re.DOTALL), ''),  # Công thức cấp khối
        (
            re.compile(r'(?<![A-Za-z0-9])\$([^\n$]+)\$(?![A-Za-z0-9])'),
            _replace_inline_dollar
        ),
        (re.compile(r'\n{2,}'), '\n'),  # Dòng trống thừa
    ]

    @staticmethod
    def clean_markdown(text: str) -> str:
        """
        Phương thức đầu vào chính: thực thi tất cả biểu thức chính quy theo thứ tự, loại bỏ hoặc thay thế các phần tử Markdown
        """
        # Kiểm tra văn bản có toàn là tiếng Anh và dấu câu cơ bản không
        if text and all((c.isascii() or c.isspace() or c in punctuation_set) for c in text):
            # Giữ khoảng trắng gốc, trả về trực tiếp
            return text

        for regex, replacement in MarkdownCleaner.REGEXES:
            text = regex.sub(replacement, text)

        # Loại bỏ biểu tượng cảm xúc emoji
        text = check_emoji(text)

        return text.strip()