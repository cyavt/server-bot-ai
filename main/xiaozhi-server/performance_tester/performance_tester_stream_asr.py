import asyncio
import time
import json
import uuid
import os
import sys
import websockets
import gzip
import random
from urllib import parse
from tabulate import tabulate

# Thêm thư mục gốc dự án vào đường dẫn Python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from config.settings import load_config
import tempfile
import wave
import hmac
import base64
import hashlib
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
description = "Kiểm tra độ trễ từ đầu của ASR streaming"
try:
    import dashscope
except ImportError:
    dashscope = None

class BaseASRTester:
    def __init__(self, config_key: str):
        self.config = load_config()
        self.config_key = config_key
        self.asr_config = self.config.get("ASR", {}).get(config_key, {})
        self.test_audio_files = self._load_test_audio_files()
        self.results = []

    def _load_test_audio_files(self):
        audio_root = os.path.join(os.getcwd(), "config", "assets")
        test_files = []
        if os.path.exists(audio_root):
            for file_name in os.listdir(audio_root):
                if file_name.endswith(('.wav', '.pcm')):
                    file_path = os.path.join(audio_root, file_name)
                    with open(file_path, 'rb') as f:
                        test_files.append({
                            'data': f.read(),
                            'path': file_path,
                            'name': file_name
                        })
        return test_files

    async def test(self, test_count=5):
        raise NotImplementedError

    def _calculate_result(self, service_name, latencies, test_count):
        """Tính toán kết quả kiểm tra (Sửa: Xử lý đúng giá trị None, loại bỏ các test thất bại)"""
        # Loại bỏ giá trị None (các test thất bại) và độ trễ không hợp lệ, chỉ thống kê độ trễ hợp lệ
        valid_latencies = [l for l in latencies if l is not None and l > 0]
        if valid_latencies:
            avg_latency = sum(valid_latencies) / len(valid_latencies)
            status = f"Thành công ({len(valid_latencies)}/{test_count} lần hợp lệ)"
        else:
            avg_latency = 0
            status = "Thất bại: Tất cả các test đều thất bại"
        return {"name": service_name, "latency": avg_latency, "status": status}


class DoubaoStreamASRTester(BaseASRTester):
    def __init__(self):
        super().__init__("DoubaoStreamASR")

    def _generate_header(
        self,
        version=0x01,
        message_type=0x01,
        message_type_specific_flags=0x00,
        serial_method=0x01,
        compression_type=0x01,
        reserved_data=0x00,
        extension_header: bytes = b"",
    ):
        """Tạo header giao thức (Sửa: Sử dụng định dạng Header đúng)"""
        header = bytearray()
        header_size = int(len(extension_header) / 4) + 1
        header.append((version << 4) | header_size)
        header.append((message_type << 4) | message_type_specific_flags)
        header.append((serial_method << 4) | compression_type)
        header.append(reserved_data)
        header.extend(extension_header)
        return header

    def _generate_audio_default_header(self):
        """Tạo Header dữ liệu audio"""
        return self._generate_header(
            version=0x01,
            message_type=0x02,
            message_type_specific_flags=0x00,  # Frame audio thông thường
            serial_method=0x01,
            compression_type=0x01,
        )

    def _generate_last_audio_header(self):
        """Tạo Header cho frame audio cuối cùng (đánh dấu audio kết thúc)"""
        return self._generate_header(
            version=0x01,
            message_type=0x02,
            message_type_specific_flags=0x02,  # 0x02 biểu thị đây là frame cuối cùng
            serial_method=0x01,
            compression_type=0x01,
        )

    def _parse_response(self, res: bytes) -> dict:
        try:
            if len(res) < 4:
                return {"error": "Độ dài dữ liệu phản hồi không đủ"}
            header = res[:4]
            message_type = header[1] >> 4
            if message_type == 0x0F:
                code = int.from_bytes(res[4:8], "big", signed=False)
                msg_length = int.from_bytes(res[8:12], "big", signed=False)
                error_msg = json.loads(res[12:].decode("utf-8"))
                return {
                    "code": code,
                    "msg_length": msg_length,
                    "payload_msg": error_msg
                }
            try:
                json_data = res[12:].decode("utf-8")
                return {"payload_msg": json.loads(json_data)}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return {"error": "Phân tích JSON thất bại"}
        except Exception:
            return {"error": "Phân tích phản hồi thất bại"}

    async def test(self, test_count=5):
        if not self.test_audio_files:
            return {"name": "Doubao Streaming ASR", "latency": 0, "status": "Thất bại: Không tìm thấy audio kiểm tra"}
        if not self.asr_config:
            return {"name": "Doubao Streaming ASR", "latency": 0, "status": "Thất bại: Chưa cấu hình"}

        latencies = []
        for i in range(test_count):
            try:
                ws_url = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
                appid = self.asr_config["appid"]
                access_token = self.asr_config["access_token"]
                cluster = self.asr_config.get("cluster", "volcengine_input_common")
                uid = self.asr_config.get("uid", "streaming_asr_service")

                start_time = time.time()

                headers = {
                    "X-Api-App-Key": appid,
                    "X-Api-Access-Key": access_token,
                    "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
                    "X-Api-Connect-Id": str(uuid.uuid4())
                }

                async with websockets.connect(
                    ws_url,
                    additional_headers=headers,
                    max_size=1000000000,
                    ping_interval=None,
                    ping_timeout=None,
                    close_timeout=10
                ) as ws:
                    request_params = {
                        "app": {"appid": appid, "cluster": cluster, "token": access_token},
                        "user": {"uid": uid},
                        "request": {
                            "reqid": str(uuid.uuid4()),
                            "workflow": "audio_in,resample,partition,vad,fe,decode,itn,nlu_punctuate",
                            "show_utterances": True,
                            "result_type": "single",
                            "sequence": 1
                        },
                        "audio": {
                            "format": "pcm",
                            "codec": "pcm",
                            "rate": 16000,
                            "language": "zh-CN",
                            "bits": 16,
                            "channel": 1,
                            "sample_rate": 16000
                        }
                    }

                    payload_bytes = str.encode(json.dumps(request_params))
                    payload_bytes = gzip.compress(payload_bytes)
                    full_client_request = self._generate_header()
                    full_client_request.extend((len(payload_bytes)).to_bytes(4, "big"))
                    full_client_request.extend(payload_bytes)
                    await ws.send(full_client_request)

                    init_res = await ws.recv()
                    result = self._parse_response(init_res)
                    if "code" in result and result["code"] != 1000:
                        raise Exception(f"Khởi tạo thất bại: {result.get('payload_msg', {}).get('error', 'Lỗi không xác định')}")

                    audio_data = self.test_audio_files[0]['data']
                    if audio_data.startswith(b'RIFF'):
                        audio_data = audio_data[44:]

                    # Gửi dữ liệu audio (sử dụng đánh dấu frame cuối cùng, báo cho server biết audio đã kết thúc)
                    payload = gzip.compress(audio_data)
                    audio_request = bytearray(self._generate_last_audio_header())  # Sửa: Sử dụng Header frame cuối cùng
                    audio_request.extend(len(payload).to_bytes(4, "big"))
                    audio_request.extend(payload)
                    await ws.send(audio_request)

                    first_chunk = await ws.recv()
                    latency = time.time() - start_time
                    latencies.append(latency)
                    print(f"[Doubao ASR] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")
                    await ws.close()

            except Exception as e:
                print(f"[Doubao ASR] Lần {i+1} kiểm tra thất bại: {str(e)}")
                latencies.append(None)

        return self._calculate_result("Doubao Streaming ASR", latencies, test_count)


class QwenASRFlashTester(BaseASRTester):
    def __init__(self):
        super().__init__("Qwen3ASRFlash")

    async def _test_single(self, audio_file_info):
        temp_file_path = None

        try:
            audio_data = audio_file_info['data']

            # Tối ưu: Di chuyển công việc chuẩn bị file tạm thời ra trước khi tính thời gian, giảm ảnh hưởng của disk IO đến kiểm tra hiệu suất
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_file_path = f.name

            with wave.open(temp_file_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"audio": temp_file_path}
                    ]
                }
            ]

            api_key = self.asr_config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("Chưa cấu hình api_key")

            if dashscope is None:
                raise RuntimeError("Chưa cài đặt thư viện dashscope")

            dashscope.api_key = api_key

            # Điểm bắt đầu tính thời gian thống nhất: Bắt đầu tính trước khi gọi API (nhưng việc chuẩn bị file đã hoàn thành)
            start_time = time.time()

            response = dashscope.MultiModalConversation.call(
                model="qwen3-asr-flash",
                messages=messages,
                result_format="message",
                asr_options={"enable_lid": True, "enable_itn": False},
                stream=True
            )

            for chunk in response:
                latency = time.time() - start_time
                return latency

            raise Exception("Streaming kết thúc, chưa nhận được phản hồi nào")

        except Exception as e:
            raise Exception(f"TongYi ASR streaming thất bại: {str(e)}")

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

    async def test(self, test_count=5):
        if not self.test_audio_files:
            return {"name": "TongYi QianWen ASR", "latency": 0, "status": "Thất bại: Không tìm thấy audio kiểm tra"}
        if not self.asr_config and not os.getenv("DASHSCOPE_API_KEY"):
            return {"name": "TongYi QianWen ASR", "latency": 0, "status": "Thất bại: Chưa cấu hình api_key"}

        latencies = []
        for i in range(test_count):
            try:
                # print(f"\n[TongYi ASR] Bắt đầu lần {i+1} kiểm tra...")
                latency = await self._test_single(self.test_audio_files[0])
                latencies.append(latency)
                print(f"[TongYi ASR] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")
            except Exception as e:
                # print(f"[TongYi ASR] Lần {i+1} kiểm tra thất bại: {str(e)}")
                latencies.append(None)

        return self._calculate_result("TongYi QianWen ASR", latencies, test_count)


class XunfeiStreamASRTester(BaseASRTester):
    def __init__(self):
        super().__init__("XunfeiStreamASR")

    def _create_url(self):
        url = "wss://iat-api.xfyun.cn/v2/iat"
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = f"host: iat-api.xfyun.cn\ndate: {date}\nGET /v2/iat HTTP/1.1"
        signature_sha = hmac.new(
            self.asr_config["api_secret"].encode('utf-8'),
            signature_origin.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode()

        authorization_origin = f'api_key="{self.asr_config["api_key"]}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode()).decode()

        v = {"authorization": authorization, "date": date, "host": "iat-api.xfyun.cn"}
        return url + "?" + parse.urlencode(v)

    async def test(self, test_count: int = 5):
        if not self.test_audio_files:
            return {"name": "XunFei Streaming ASR", "latency": 0, "status": "Thất bại: Không tìm thấy audio kiểm tra"}
        if not self.asr_config:
            return {"name": "XunFei Streaming ASR", "latency": 0, "status": "Thất bại: Chưa cấu hình"}

        required = ["app_id", "api_key", "api_secret"]
        for k in required:
            if k not in self.asr_config:
                return {"name": "XunFei Streaming ASR", "latency": 0, "status": f"Thất bại: Thiếu cấu hình {k}"}

        latencies = []
        frame_size = 1280
        audio_raw = self.test_audio_files[0]['data']
        if audio_raw.startswith(b'RIFF'):
            audio_raw = audio_raw[44:]

        for i in range(test_count):
            try:
                start_time = time.time()
                ws_url = self._create_url()

                async with websockets.connect(
                    ws_url,
                    additional_headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                    max_size=1 << 30,
                    ping_interval=None,
                    ping_timeout=None,
                    close_timeout=30,
                ) as ws:

                    # Frame đầu tiên: Loại bỏ trường punc, tránh lỗi tham số không xác định
                    await ws.send(json.dumps({
                        "common": {"app_id": self.asr_config["app_id"]},
                        "business": {
                            "domain": "iat",
                            "language": "zh_cn",
                            "accent": "mandarin",
                            "dwa": "wpgs",
                            "vad_eos": 5000
                            # Đã loại bỏ "punc": True
                        },
                        "data": {
                            "status": 0,
                            "format": "audio/L16;rate=16000",
                            "encoding": "raw",
                            "audio": base64.b64encode(audio_raw[:frame_size]).decode()
                        }
                    }, ensure_ascii=False))

                    # Tất cả các frame tiếp theo
                    pos = frame_size
                    while pos < len(audio_raw):
                        chunk = audio_raw[pos:pos + frame_size]
                        status = 2 if (pos + frame_size >= len(audio_raw)) else 1
                        await ws.send(json.dumps({
                            "data": {
                                "status": status,
                                "format": "audio/L16;rate=16000",
                                "encoding": "raw",
                                "audio": base64.b64encode(chunk).decode()
                            }
                        }, ensure_ascii=False))
                        if status == 2:
                            break
                        pos += frame_size

                    # Nhận từ đầu tiên
                    first_token = True
                    async for message in ws:
                        data = json.loads(message)
                        if data.get("code") != 0:
                            raise Exception(f"Lỗi XunFei: {data.get('message')}")

                        ws_result = data.get("data", {}).get("result", {}).get("ws")
                        if ws_result:
                            text = "".join(cw.get("w", "") for seg in ws_result for cw in seg.get("cw", []))
                            if text.strip() and first_token:
                                latency = time.time() - start_time
                                latencies.append(latency)
                                print(f"[XunFei ASR] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")
                                first_token = False
                                break

            except Exception as e:
                print(f"[XunFei ASR] Lần {i+1} kiểm tra thất bại: {str(e)}")
                latencies.append(None)

        return self._calculate_result("XunFei Streaming ASR", latencies, test_count)
class ASRPerformanceSuite:
    def __init__(self):
        self.testers = []
        self.results = []

    def register_tester(self, tester_class):
        try:
            tester = tester_class()
            self.testers.append(tester)
            print(f"Đã đăng ký tester: {tester.config_key}")
        except Exception as e:
            name_map = {
                "DoubaoStreamASRTester": "Doubao Streaming ASR",
                "QwenASRFlashTester": "TongYi QianWen ASR",
                "XunfeiStreamASRTester": "XunFei Streaming ASR"
            }
            name = name_map.get(tester_class.__name__, tester_class.__name__)
            print(f"Bỏ qua {name}: {str(e)}")

    def _print_results(self, test_count):
        if not self.results:
            print("Không có kết quả kiểm tra ASR hợp lệ")
            return

        print(f"\n{'='*60}")
        print("Kết quả kiểm tra thời gian phản hồi từ đầu ASR streaming")
        print(f"{'='*60}")
        print(f"Số lần kiểm tra: Mỗi dịch vụ ASR kiểm tra {test_count} lần")

        success_results = sorted(
            [r for r in self.results if "Thành công" in r["status"]],
            key=lambda x: x["latency"]
        )
        failed_results = [r for r in self.results if "Thành công" not in r["status"]]

        table_data = [
            [r["name"], f"{r['latency']:.3f}s" if r['latency'] > 0 else "N/A", r["status"]]
            for r in success_results + failed_results
        ]

        print(tabulate(table_data, headers=["Dịch vụ ASR", "Độ trễ từ đầu", "Trạng thái"], tablefmt="grid"))
        print("\nHướng dẫn kiểm tra:")
        print("- Điểm bắt đầu tính thời gian: Trước khi thiết lập kết nối (bao gồm toàn bộ quy trình bắt tay, gửi audio, nhận kết quả nhận dạng đầu tiên)")
        print("- Tối ưu TongYi QianWen: Chuẩn bị file tạm thời hoàn thành trước khi tính thời gian, giảm ảnh hưởng của disk IO đến kiểm tra")
        print("- Xử lý lỗi: Các test thất bại không tính vào trung bình, chỉ thống kê độ trễ của các test thành công")
        print("- Quy tắc sắp xếp: Các test thành công sắp xếp theo độ trễ tăng dần, các test thất bại xếp ở sau")

    async def run(self, test_count=5):
        print(f"Bắt đầu kiểm tra thời gian phản hồi từ đầu ASR streaming...")
        print(f"Số lần kiểm tra mỗi dịch vụ ASR: {test_count} lần\n")

        self.results = []
        for tester in self.testers:
            print(f"\n--- Kiểm tra {tester.config_key} ---")
            result = await tester.test(test_count)
            self.results.append(result)

        self._print_results(test_count)


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Công cụ kiểm tra thời gian phản hồi từ đầu ASR streaming")
    parser.add_argument("--count", type=int, default=5, help="Số lần kiểm tra")
    args = parser.parse_args()

    suite = ASRPerformanceSuite()
    suite.register_tester(DoubaoStreamASRTester)
    suite.register_tester(QwenASRFlashTester)
    suite.register_tester(XunfeiStreamASRTester)

    await suite.run(args.count)


if __name__ == "__main__":
    asyncio.run(main())