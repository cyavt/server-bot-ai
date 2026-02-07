import asyncio
import logging
import os
import sys
import statistics
import time
import concurrent.futures
from typing import Dict, Optional
import yaml
import aiohttp
from tabulate import tabulate

# Thêm thư mục gốc dự án vào đường dẫn Python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from core.utils.llm import create_instance as create_llm_instance
from config.settings import load_config

# Thiết lập mức log toàn cục là WARNING, ức chế log mức INFO
logging.basicConfig(level=logging.WARNING)

description = "Kiểm tra hiệu suất mô hình ngôn ngữ lớn"


class LLMPerformanceTester:
    def __init__(self):
        self.config = load_config()
        # Sử dụng nội dung kiểm tra phù hợp hơn với kịch bản agent, bao gồm system prompt
        self.system_prompt = self._load_system_prompt()
        self.test_sentences = self.config.get("module_test", {}).get(
            "test_sentences",
            [
                "Xin chào, hôm nay tôi cảm thấy không tốt lắm, bạn có thể an ủi tôi không?",
                "Giúp tôi kiểm tra thời tiết ngày mai như thế nào?",
                "Tôi muốn nghe một câu chuyện thú vị, bạn có thể kể cho tôi nghe không?",
                "Bây giờ là mấy giờ? Hôm nay là thứ mấy?",
                "Tôi muốn đặt một báo thức 8 giờ sáng ngày mai để nhắc tôi họp",
            ],
        )
        self.results = {}

    def _load_system_prompt(self) -> str:
        """Tải system prompt"""
        try:
            prompt_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), self.config.get("prompt_template", "agent-base-prompt.txt")
            )
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Thay thế biến template bằng giá trị test
                content = content.replace(
                    "{{base_prompt}}", "Bạn là XiaoZhi, một trợ lý AI thông minh và dễ thương"
                )
                content = content.replace(
                    "{{emojiList}}", "😀,😃,😄,😁,😊,😍,🤔,😮,😱,😢,😭,😴,😵,🤗,🙄"
                )
                content = content.replace("{{current_time}}", "17 tháng 8 năm 2024 12:30:45")
                content = content.replace("{{today_date}}", "17 tháng 8 năm 2024")
                content = content.replace("{{today_weekday}}", "Thứ Bảy")
                content = content.replace("{{lunar_date}}", "Giáp Thìn năm tháng 7 ngày 14")
                content = content.replace("{{local_address}}", "Hà Nội")
                content = content.replace("{{weather_info}}", "Hôm nay nắng, 25-32℃")
                return content
        except Exception as e:
            print(f"Không thể tải file system prompt: {e}")
            return "Bạn là XiaoZhi, một trợ lý AI thông minh và dễ thương. Vui lòng trả lời người dùng bằng giọng điệu ấm áp và thân thiện."

    def _collect_response_sync(self, llm, messages, llm_name, sentence_start):
        """Phương thức hỗ trợ thu thập dữ liệu phản hồi đồng bộ"""
        chunks = []
        first_token_received = False
        first_token_time = None

        try:
            response_generator = llm.response("perf_test", messages)
            chunk_count = 0
            for chunk in response_generator:
                chunk_count += 1
                # Kiểm tra xem có nên ngắt sau khi xử lý một số lượng chunk nhất định
                if chunk_count % 10 == 0:
                    # Thoát sớm bằng cách kiểm tra xem thread hiện tại có được đánh dấu là ngắt không
                    import threading

                    if (
                        threading.current_thread().ident
                        != threading.main_thread().ident
                    ):
                        # Nếu không phải thread chính, kiểm tra xem có nên dừng không
                        pass

                # Kiểm tra xem chunk có chứa thông tin lỗi không
                chunk_str = str(chunk)
                if (
                    "异常" in chunk_str
                    or "错误" in chunk_str
                    or "502" in chunk_str.lower()
                ):
                    error_msg = chunk_str.lower()
                    print(f"{llm_name} phản hồi chứa thông tin lỗi: {error_msg}")
                    # Ném exception chứa thông tin lỗi
                    raise Exception(chunk_str)

                if not first_token_received and chunk.strip() != "":
                    first_token_time = time.time() - sentence_start
                    first_token_received = True
                    print(f"{llm_name} Token đầu tiên: {first_token_time:.3f}s")
                chunks.append(chunk)
        except Exception as e:
            # Thông tin lỗi chi tiết hơn
            error_msg = str(e).lower()
            print(f"{llm_name} thu thập phản hồi bất thường: {error_msg}")
            # Đối với lỗi 502 hoặc lỗi mạng, ném exception trực tiếp để lớp trên xử lý
            if (
                "502" in error_msg
                or "bad gateway" in error_msg
                or "error code: 502" in error_msg
                or "异常" in str(e)
                or "错误" in str(e)
            ):
                raise e
            # Đối với các lỗi khác, có thể trả về kết quả một phần
            return chunks, first_token_time

        return chunks, first_token_time

    async def _check_ollama_service(self, base_url: str, model_name: str) -> bool:
        """Kiểm tra trạng thái dịch vụ Ollama bất đồng bộ"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{base_url}/api/version") as response:
                    if response.status != 200:
                        print(f"Dịch vụ Ollama chưa khởi động hoặc không thể truy cập: {base_url}")
                        return False
                async with session.get(f"{base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        if not any(model["name"] == model_name for model in models):
                            print(
                                f"Mô hình Ollama {model_name} không tìm thấy, vui lòng tải xuống trước bằng `ollama pull {model_name}`"
                            )
                            return False
                    else:
                        print("Không thể lấy danh sách mô hình Ollama")
                        return False
                return True
            except Exception as e:
                print(f"Không thể kết nối đến dịch vụ Ollama: {str(e)}")
                return False

    async def _test_single_sentence(
        self, llm_name: str, llm, sentence: str
    ) -> Optional[Dict]:
        """Kiểm tra hiệu suất một câu đơn lẻ"""
        try:
            print(f"{llm_name} bắt đầu kiểm tra: {sentence[:20]}...")
            sentence_start = time.time()
            first_token_received = False
            first_token_time = None

            # Tạo message bao gồm system prompt
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": sentence},
            ]

            # Sử dụng asyncio.wait_for để kiểm soát timeout
            try:
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Tạo task thu thập phản hồi
                    future = executor.submit(
                        self._collect_response_sync,
                        llm,
                        messages,
                        llm_name,
                        sentence_start,
                    )

                    # Sử dụng asyncio.wait_for để thực hiện kiểm soát timeout
                    try:
                        response_chunks, first_token_time = await asyncio.wait_for(
                            asyncio.wrap_future(future), timeout=10.0
                        )
                    except asyncio.TimeoutError:
                        print(f"{llm_name} kiểm tra timeout (10 giây), bỏ qua")
                        # Buộc hủy future
                        future.cancel()
                        # Đợi một chút để đảm bảo task trong thread pool có thể phản hồi hủy
                        try:
                            await asyncio.wait_for(
                                asyncio.wrap_future(future), timeout=1.0
                            )
                        except (
                            asyncio.TimeoutError,
                            concurrent.futures.CancelledError,
                            Exception,
                        ):
                            # Bỏ qua tất cả exception, đảm bảo chương trình tiếp tục thực thi
                            pass
                        return None

            except Exception as timeout_error:
                print(f"{llm_name} xử lý bất thường: {timeout_error}")
                return None

            response_time = time.time() - sentence_start
            print(f"{llm_name} hoàn thành phản hồi: {response_time:.3f}s")

            return {
                "name": llm_name,
                "type": "llm",
                "first_token_time": first_token_time,
                "response_time": response_time,
            }
        except Exception as e:
            error_msg = str(e).lower()
            # Kiểm tra xem có phải lỗi 502 hoặc lỗi mạng không
            if (
                "502" in error_msg
                or "bad gateway" in error_msg
                or "error code: 502" in error_msg
            ):
                print(f"{llm_name} gặp lỗi 502, bỏ qua kiểm tra")
                return {
                    "name": llm_name,
                    "type": "llm",
                    "errors": 1,
                    "error_type": "Lỗi mạng 502",
                }
            print(f"{llm_name} kiểm tra câu thất bại: {str(e)}")
            return None

    async def _test_llm(self, llm_name: str, config: Dict) -> Dict:
        """Kiểm tra hiệu suất một LLM đơn lẻ bất đồng bộ"""
        try:
            # Đối với Ollama, bỏ qua kiểm tra api_key và xử lý đặc biệt
            if llm_name == "Ollama":
                base_url = config.get("base_url", "http://localhost:11434")
                model_name = config.get("model_name")
                if not model_name:
                    print("Ollama chưa cấu hình model_name")
                    return {
                        "name": llm_name,
                        "type": "llm",
                        "errors": 1,
                        "error_type": "Lỗi mạng",
                    }

                if not await self._check_ollama_service(base_url, model_name):
                    return {
                        "name": llm_name,
                        "type": "llm",
                        "errors": 1,
                        "error_type": "Lỗi mạng",
                    }
            else:
                if "api_key" in config and any(
                    x in config["api_key"] for x in ["你的", "placeholder", "sk-xxx"]
                ):
                    print(f"Bỏ qua LLM chưa cấu hình: {llm_name}")
                    return {
                        "name": llm_name,
                        "type": "llm",
                        "errors": 1,
                        "error_type": "Lỗi cấu hình",
                    }

            # Lấy loại thực tế (tương thích với cấu hình cũ)
            module_type = config.get("type", llm_name)
            llm = create_llm_instance(module_type, config)

            # Sử dụng mã hóa UTF-8 thống nhất
            test_sentences = [
                s.encode("utf-8").decode("utf-8") for s in self.test_sentences
            ]

            # Tạo task kiểm tra cho tất cả các câu
            sentence_tasks = []
            for sentence in test_sentences:
                sentence_tasks.append(
                    self._test_single_sentence(llm_name, llm, sentence)
                )

            # Thực thi tất cả các kiểm tra câu đồng thời, và xử lý các exception có thể xảy ra
            sentence_results = await asyncio.gather(
                *sentence_tasks, return_exceptions=True
            )

            # Xử lý kết quả, lọc bỏ exception và giá trị None
            valid_results = []
            for result in sentence_results:
                if isinstance(result, dict) and result is not None:
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    error_msg = str(result).lower()
                    if "502" in error_msg or "bad gateway" in error_msg:
                        print(f"{llm_name} gặp lỗi 502, bỏ qua kiểm tra câu đó")
                        return {
                            "name": llm_name,
                            "type": "llm",
                            "errors": 1,
                            "error_type": "Lỗi mạng 502",
                        }
                    else:
                        print(f"{llm_name} kiểm tra câu bất thường: {result}")

            if not valid_results:
                print(f"{llm_name} không có dữ liệu hợp lệ, có thể gặp vấn đề mạng hoặc lỗi cấu hình")
                return {
                    "name": llm_name,
                    "type": "llm",
                    "errors": 1,
                    "error_type": "Lỗi mạng",
                }

            # Kiểm tra số lượng kết quả hợp lệ, nếu quá ít thì coi như test thất bại
            if len(valid_results) < len(test_sentences) * 0.3:  # Ít nhất phải có 30% tỷ lệ thành công
                print(
                    f"{llm_name} số câu test thành công quá ít ({len(valid_results)}/{len(test_sentences)}), có thể mạng không ổn định hoặc API có vấn đề"
                )
                return {
                    "name": llm_name,
                    "type": "llm",
                    "errors": 1,
                    "error_type": "Lỗi mạng",
                }

            first_token_times = [
                r["first_token_time"]
                for r in valid_results
                if r.get("first_token_time")
            ]
            response_times = [r["response_time"] for r in valid_results]

            # Lọc dữ liệu bất thường (dữ liệu vượt quá 3 độ lệch chuẩn)
            if len(response_times) > 1:
                mean = statistics.mean(response_times)
                stdev = statistics.stdev(response_times)
                filtered_times = [t for t in response_times if t <= mean + 3 * stdev]
            else:
                filtered_times = response_times

            return {
                "name": llm_name,
                "type": "llm",
                "avg_response": sum(response_times) / len(response_times),
                "avg_first_token": (
                    sum(first_token_times) / len(first_token_times)
                    if first_token_times
                    else 0
                ),
                "success_rate": f"{len(valid_results)}/{len(test_sentences)}",
                "errors": 0,
            }
        except Exception as e:
            error_msg = str(e).lower()
            if "502" in error_msg or "bad gateway" in error_msg:
                print(f"LLM {llm_name} gặp lỗi 502, bỏ qua kiểm tra")
            else:
                print(f"LLM {llm_name} kiểm tra thất bại: {str(e)}")
            error_type = "Lỗi mạng"
            if "timeout" in str(e).lower():
                error_type = "Kết nối timeout"
            return {
                "name": llm_name,
                "type": "llm",
                "errors": 1,
                "error_type": error_type,
            }

    def _print_results(self):
        """In kết quả kiểm tra"""
        print("\n" + "=" * 50)
        print("Kết quả kiểm tra hiệu suất LLM")
        print("=" * 50)

        if not self.results:
            print("Không có kết quả kiểm tra khả dụng")
            return

        headers = ["Tên mô hình", "Thời gian phản hồi trung bình (s)", "Thời gian Token đầu tiên (s)", "Tỷ lệ thành công", "Trạng thái"]
        table_data = []

        # Thu thập và phân loại tất cả dữ liệu
        valid_results = []
        error_results = []

        for name, data in self.results.items():
            if data["errors"] == 0:
                # Kết quả bình thường
                avg_response = f"{data['avg_response']:.3f}"
                avg_first_token = (
                    f"{data['avg_first_token']:.3f}"
                    if data["avg_first_token"] > 0
                    else "-"
                )
                success_rate = data.get("success_rate", "N/A")
                status = "✅ Bình thường"

                # Lưu giá trị dùng để sắp xếp
                first_token_value = (
                    data["avg_first_token"]
                    if data["avg_first_token"] > 0
                    else float("inf")
                )

                valid_results.append(
                    {
                        "name": name,
                        "avg_response": avg_response,
                        "avg_first_token": avg_first_token,
                        "success_rate": success_rate,
                        "status": status,
                        "sort_key": first_token_value,
                    }
                )
            else:
                # Kết quả lỗi
                avg_response = "-"
                avg_first_token = "-"
                success_rate = "0/5"

                # Lấy loại lỗi cụ thể
                error_type = data.get("error_type", "Lỗi mạng")
                status = f"❌ {error_type}"

                error_results.append(
                    [name, avg_response, avg_first_token, success_rate, status]
                )

        # Sắp xếp theo thời gian Token đầu tiên tăng dần
        valid_results.sort(key=lambda x: x["sort_key"])

        # Chuyển đổi kết quả hợp lệ đã sắp xếp thành dữ liệu bảng
        for result in valid_results:
            table_data.append(
                [
                    result["name"],
                    result["avg_response"],
                    result["avg_first_token"],
                    result["success_rate"],
                    result["status"],
                ]
            )

        # Thêm kết quả lỗi vào cuối dữ liệu bảng
        table_data.extend(error_results)

        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print("\nHướng dẫn kiểm tra:")
        print("- Nội dung kiểm tra: Kịch bản đối thoại agent bao gồm system prompt đầy đủ")
        print("- Kiểm soát timeout: Thời gian chờ tối đa cho một yêu cầu là 10 giây")
        print("- Xử lý lỗi: Tự động bỏ qua các mô hình có lỗi 502 và lỗi mạng bất thường")
        print("- Tỷ lệ thành công: Số lượng câu phản hồi thành công / Tổng số câu kiểm tra")
        print("\nKiểm tra hoàn tất!")

    async def run(self):
        """Thực thi kiểm tra bất đồng bộ toàn bộ"""
        print("Bắt đầu lọc các module LLM khả dụng...")

        # Tạo tất cả các task kiểm tra
        all_tasks = []

        # Task kiểm tra LLM
        if self.config.get("LLM") is not None:
            for llm_name, config in self.config.get("LLM", {}).items():
                # Kiểm tra tính hợp lệ của cấu hình
                if llm_name == "CozeLLM":
                    if any(x in config.get("bot_id", "") for x in ["你的"]) or any(
                        x in config.get("user_id", "") for x in ["你的"]
                    ):
                        print(f"LLM {llm_name} chưa cấu hình bot_id/user_id, đã bỏ qua")
                        continue
                elif "api_key" in config and any(
                    x in config["api_key"] for x in ["你的", "placeholder", "sk-xxx"]
                ):
                    print(f"LLM {llm_name} chưa cấu hình api_key, đã bỏ qua")
                    continue

                # Đối với Ollama, kiểm tra trạng thái dịch vụ trước
                if llm_name == "Ollama":
                    base_url = config.get("base_url", "http://localhost:11434")
                    model_name = config.get("model_name")
                    if not model_name:
                        print("Ollama chưa cấu hình model_name")
                        continue

                    if not await self._check_ollama_service(base_url, model_name):
                        continue

                print(f"Thêm task kiểm tra LLM: {llm_name}")
                all_tasks.append(self._test_llm(llm_name, config))

        print(f"\nTìm thấy {len(all_tasks)} module LLM khả dụng")
        print("\nBắt đầu kiểm tra đồng thời tất cả các module...\n")

        # Thực thi tất cả các task kiểm tra đồng thời, nhưng thiết lập timeout độc lập cho mỗi task
        async def test_with_timeout(task, timeout=30):
            """Thêm bảo vệ timeout cho mỗi task kiểm tra"""
            try:
                return await asyncio.wait_for(task, timeout=timeout)
            except asyncio.TimeoutError:
                print(f"Task kiểm tra timeout ({timeout} giây), bỏ qua")
                return {
                    "name": "Unknown",
                    "type": "llm",
                    "errors": 1,
                    "error_type": "Kết nối timeout",
                }
            except Exception as e:
                print(f"Task kiểm tra bất thường: {str(e)}")
                return {
                    "name": "Unknown",
                    "type": "llm",
                    "errors": 1,
                    "error_type": "Lỗi mạng",
                }

        # Bọc bảo vệ timeout cho mỗi task
        protected_tasks = [test_with_timeout(task) for task in all_tasks]

        # Thực thi tất cả các task kiểm tra đồng thời
        all_results = await asyncio.gather(*protected_tasks, return_exceptions=True)

        # Xử lý kết quả
        for result in all_results:
            if isinstance(result, dict):
                if result.get("errors") == 0:
                    self.results[result["name"]] = result
                else:
                    # Ngay cả khi có lỗi cũng ghi lại, để hiển thị trạng thái thất bại
                    if result.get("name") != "Unknown":
                        self.results[result["name"]] = result
            elif isinstance(result, Exception):
                print(f"Xử lý kết quả kiểm tra bất thường: {str(result)}")

        # In kết quả
        print("\nĐang tạo báo cáo kiểm tra...")
        self._print_results()


async def main():
    tester = LLMPerformanceTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
