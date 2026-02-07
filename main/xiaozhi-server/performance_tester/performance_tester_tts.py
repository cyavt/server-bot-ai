import asyncio
import logging
import os
import sys
import time
from typing import Dict
import yaml
from tabulate import tabulate

# Thêm thư mục gốc dự án vào đường dẫn Python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

# Đảm bảo import create_tts_instance từ core.utils.tts
from core.utils.tts import create_instance as create_tts_instance
from config.settings import load_config

# Thiết lập mức log toàn cục là WARNING
logging.basicConfig(level=logging.WARNING)

description = "Kiểm tra hiệu suất tổng hợp giọng nói không streaming"


class TTSPerformanceTester:
    def __init__(self):
        self.config = load_config()
        self.test_sentences = self.config.get("module_test", {}).get(
            "test_sentences",
            [
                "Năm Vĩnh Hòa thứ chín, năm Quý Sửu, đầu mùa xuân muộn;",
                "Người ta cùng nhau, cúi ngẩng một đời, hoặc lấy từ trong lòng, ngộ ngôn trong một căn phòng; hoặc nhờ gửi gắm, phóng túng hình hài bên ngoài. Dù thú vui muôn vẻ khác nhau, tĩnh động khác nhau,",
                "Mỗi khi xem lý do cảm xúc của người xưa, như hợp một khế, chưa từng không đối mặt với văn than thở, không thể hiểu được trong lòng. Vốn biết một cái chết sinh là hư dối, Tề Bành Thương là vọng tác.",
            ],
        )
        self.results = {}

    async def _test_tts(self, tts_name: str, config: Dict) -> Dict:
        """Kiểm tra hiệu suất một module TTS đơn lẻ"""
        try:
            token_fields = ["access_token", "api_key", "token"]
            if any(
                field in config
                and any(x in config[field] for x in ["你的", "placeholder"])
                for field in token_fields
            ):
                print(f"TTS {tts_name} chưa cấu hình access_token/api_key, đã bỏ qua")
                return {"name": tts_name, "errors": 1}

            module_type = config.get("type", tts_name)
            tts = create_tts_instance(module_type, config, delete_audio_file=True)

            print(f"Kiểm tra TTS: {tts_name}")

            # Kiểm tra kết nối
            tmp_file = tts.generate_filename()
            await tts.text_to_speak("Kiểm tra kết nối", tmp_file)

            if not tmp_file or not os.path.exists(tmp_file):
                print(f"{tts_name} kết nối thất bại")
                return {"name": tts_name, "errors": 1}

            total_time = 0
            test_count = len(self.test_sentences[:3])

            for i, sentence in enumerate(self.test_sentences[:2], 1):
                start = time.time()
                tmp_file = tts.generate_filename()
                await tts.text_to_speak(sentence, tmp_file)
                duration = time.time() - start
                total_time += duration

                if tmp_file and os.path.exists(tmp_file):
                    print(f"{tts_name} [{i}/{test_count}] kiểm tra thành công")
                else:
                    print(f"{tts_name} [{i}/{test_count}] kiểm tra thất bại")
                    return {"name": tts_name, "errors": 1}

            return {
                "name": tts_name,
                "avg_time": total_time / test_count,
                "errors": 0,
            }

        except Exception as e:
            print(f"{tts_name} kiểm tra thất bại: {str(e)}")
            return {"name": tts_name, "errors": 1}

    def _print_results(self):
        """In kết quả kiểm tra"""
        if not self.results:
            print("Không có kết quả kiểm tra TTS hợp lệ")
            return

        headers = ["Module TTS", "Thời gian trung bình (giây)", "Số câu kiểm tra", "Trạng thái"]
        table_data = []

        # Thu thập và phân loại tất cả dữ liệu
        valid_results = []
        error_results = []

        for name, data in self.results.items():
            if data["errors"] == 0:
                # Kết quả bình thường
                avg_time = f"{data['avg_time']:.3f}"
                test_count = len(self.test_sentences[:3])
                status = "✅ Bình thường"
                
                # Lưu giá trị dùng để sắp xếp
                valid_results.append({
                    "name": name,
                    "avg_time": avg_time,
                    "test_count": test_count,
                    "status": status,
                    "sort_key": data['avg_time']
                })
            else:
                # Kết quả lỗi
                avg_time = "-"
                test_count = "0/3"
                
                # Loại lỗi mặc định là lỗi mạng
                error_type = "Lỗi mạng"
                status = f"❌ {error_type}"
                
                error_results.append([name, avg_time, test_count, status])

        # Sắp xếp theo thời gian trung bình tăng dần
        valid_results.sort(key=lambda x: x["sort_key"])

        # Chuyển đổi kết quả hợp lệ đã sắp xếp thành dữ liệu bảng
        for result in valid_results:
            table_data.append([
                result["name"],
                result["avg_time"],
                result["test_count"],
                result["status"]
            ])

        # Thêm kết quả lỗi vào cuối dữ liệu bảng
        table_data.extend(error_results)

        print("\nKết quả kiểm tra hiệu suất TTS:")
        print(
            tabulate(
                table_data,
                headers=headers,
                tablefmt="grid",
                colalign=("left", "right", "right", "left"),
            )
        )
        print("\nHướng dẫn kiểm tra:")
        print("- Kiểm soát timeout: Thời gian chờ tối đa cho một yêu cầu là 10 giây")
        print("- Xử lý lỗi: Không thể kết nối và timeout được liệt kê là lỗi mạng")
        print("- Quy tắc sắp xếp: Sắp xếp theo thời gian trung bình từ nhanh đến chậm")

    async def run(self):
        """Thực thi kiểm tra"""
        print("Bắt đầu kiểm tra hiệu suất TTS...")

        if not self.config.get("TTS"):
            print("Không tìm thấy cấu hình TTS trong file cấu hình")
            return

        # Duyệt qua tất cả cấu hình TTS
        tasks = []
        for tts_name, config in self.config.get("TTS", {}).items():
            tasks.append(self._test_tts(tts_name, config))

        # Thực thi kiểm tra đồng thời
        results = await asyncio.gather(*tasks)

        # Lưu tất cả kết quả, bao gồm lỗi
        for result in results:
            self.results[result["name"]] = result

        # In kết quả
        self._print_results()


# Để đáp ứng nhu cầu gọi từ performance_tester.py
async def main():
    tester = TTSPerformanceTester()
    await tester.run()


if __name__ == "__main__":
    tester = TTSPerformanceTester()
    asyncio.run(tester.run())
