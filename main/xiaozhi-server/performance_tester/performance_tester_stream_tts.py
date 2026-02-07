import asyncio
import time
import json
import uuid
import os
import sys
import aiohttp
import websockets
import hmac
import base64
import hashlib
from urllib.parse import urlparse, urlencode
from tabulate import tabulate

# Thêm thư mục gốc dự án vào đường dẫn Python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from config.settings import load_config

description = "Kiểm tra thời gian trễ từ đầu của TTS streaming tổng hợp giọng nói"
class StreamTTSPerformanceTester:
    def __init__(self):
        self.config = load_config()
        self.test_texts = [
            "Xin chào, đây là một câu."
        ]
        self.results = []
    
    async def test_aliyun_tts(self, text=None, test_count=5):
        """Kiểm tra độ trễ từ đầu của TTS streaming Aliyun (kiểm tra nhiều lần lấy trung bình)"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["AliyunStreamTTS"]
                appkey = tts_config["appkey"]
                token = tts_config["token"]
                voice = tts_config["voice"]
                host = tts_config["host"]
                ws_url = f"wss://{host}/ws/v1"

                # Điểm bắt đầu tính thời gian thống nhất: Bắt đầu tính trước khi thiết lập kết nối
                start_time = time.time()
                async with websockets.connect(ws_url, extra_headers={"X-NLS-Token": token}) as ws:
                    task_id = str(uuid.uuid4())
                    message_id = str(uuid.uuid4())

                    start_request = {
                        "header": {
                            "message_id": message_id,
                            "task_id": task_id,
                            "namespace": "FlowingSpeechSynthesizer",
                            "name": "StartSynthesis",
                            "appkey": appkey,
                        },
                        "payload": {
                            "voice": voice,
                            "format": "pcm",
                            "sample_rate": 16000,
                            "volume": 50,
                            "speech_rate": 0,
                            "pitch_rate": 0,
                            "enable_subtitle": True,
                        }
                    }
                    await ws.send(json.dumps(start_request))

                    start_response = json.loads(await ws.recv())
                    if start_response["header"]["name"] != "SynthesisStarted":
                        raise Exception("Khởi động tổng hợp thất bại")

                    run_request = {
                        "header": {
                            "message_id": str(uuid.uuid4()),
                            "task_id": task_id,
                            "namespace": "FlowingSpeechSynthesizer",
                            "name": "RunSynthesis",
                            "appkey": appkey,
                        },
                        "payload": {"text": text}
                    }
                    await ws.send(json.dumps(run_request))

                    while True:
                        response = await ws.recv()
                        if isinstance(response, bytes):
                            latency = time.time() - start_time
                            latencies.append(latency)
                            print(f"[Aliyun TTS] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")
                            break
                        elif isinstance(response, str):
                            data = json.loads(response)
                            if data["header"]["name"] == "TaskFailed":
                                raise Exception(f"Tổng hợp thất bại: {data['payload']['error_info']}")

            except Exception as e:
                print(f"[Aliyun TTS] Lần {i+1} kiểm tra thất bại: {str(e)}")
                latencies.append(None)
        
        return self._calculate_result("Aliyun TTS", latencies, test_count)

    async def test_alibl_tts(self, text=None, test_count=5):
        """Kiểm tra độ trễ từ đầu của TTS streaming Aliyun BaiLian CosyVoice"""
        text = text or self.test_texts[0]
        latencies = []

        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["AliBLTTS"]
                api_key = tts_config["api_key"]
                model = tts_config.get("model", "cosyvoice-v2")
                voice = tts_config.get("voice", "longxiaochun_v2")
                format_type = tts_config.get("format", "pcm")
                sample_rate = int(tts_config.get("sample_rate", "24000"))

                ws_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference/"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "X-DashScope-DataInspection": "enable",
                }

                start_time = time.time()

                async with websockets.connect(
                    ws_url,
                    additional_headers=headers,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10,
                    max_size=10 * 1024 * 1024,
                ) as ws:
                    session_id = uuid.uuid4().hex

                    # 1. Gửi run-task (khởi động task)
                    run_task_message = {
                        "header": {
                            "action": "run-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {
                            "task_group": "audio",
                            "task": "tts",
                            "function": "SpeechSynthesizer",
                            "model": model,
                            "parameters": {
                                "text_type": "PlainText",
                                "voice": voice,
                                "format": format_type,
                                "sample_rate": sample_rate,
                                "volume": 50,
                                "rate": 1.0,
                                "pitch": 1.0,
                            },
                            "input": {}
                        },
                    }
                    await ws.send(json.dumps(run_task_message))

                    # 2. Chờ sự kiện task-started (Quan trọng! Phải đợi cái này rồi mới gửi text)
                    task_started = False
                    while not task_started:
                        msg = await ws.recv()
                        if isinstance(msg, str):
                            data = json.loads(msg)
                            header = data.get("header", {})
                            event = header.get("event")
                            if event == "task-started":
                                task_started = True
                                print(f"[Aliyun BaiLian TTS] Lần {i+1} task khởi động thành công")
                            elif event == "task-failed":
                                raise Exception(f"Khởi động thất bại: {header.get('error_message', 'Lỗi không xác định')}")

                    # 3. Gửi continue-task (Gửi text! Đây là hành động đúng)
                    continue_task_message = {
                        "header": {
                            "action": "continue-task",  # Đổi lại continue-task
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {"input": {"text": text}},
                    }
                    await ws.send(json.dumps(continue_task_message))

                    # 4. Gửi finish-task (Kết thúc task)
                    finish_task_message = {
                        "header": {
                            "action": "finish-task",
                            "task_id": session_id,
                            "streaming": "duplex",
                        },
                        "payload": {"input": {}}
                    }
                    await ws.send(json.dumps(finish_task_message))

                    # 5. Chờ khối dữ liệu audio đầu tiên
                    while True:
                        msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
                        if isinstance(msg, (bytes, bytearray)) and len(msg) > 0:
                            latency = time.time() - start_time
                            print(f"[Aliyun BaiLian TTS] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")
                            latencies.append(latency)
                            break
                        elif isinstance(msg, str):
                            data = json.loads(msg)
                            event = data.get("header", {}).get("event")
                            if event == "task-failed":
                                raise Exception(f"Tổng hợp thất bại: {data}")
                            elif event == "task-finished":
                                if not latencies or latencies[-1] is None:
                                    raise Exception("Task kết thúc nhưng chưa nhận được audio")

            except Exception as e:
                print(f"[Aliyun BaiLian TTS] Lần {i+1} thất bại: {str(e)}")
                latencies.append(None)

        return self._calculate_result("Aliyun BaiLian TTS", latencies, test_count)

    async def test_doubao_tts(self, text=None, test_count=5):
        """Kiểm tra độ trễ từ đầu của TTS streaming Huoshan Engine (kiểm tra nhiều lần lấy trung bình)"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["HuoshanDoubleStreamTTS"]
                ws_url = tts_config["ws_url"]
                app_id = tts_config["appid"]
                access_token = tts_config["access_token"]
                resource_id = tts_config["resource_id"]
                speaker = tts_config["speaker"]

                start_time = time.time()
                ws_header = {
                    "X-Api-App-Key": app_id,
                    "X-Api-Access-Key": access_token,
                    "X-Api-Resource-Id": resource_id,
                    "X-Api-Connect-Id": str(uuid.uuid4()),
                }
                async with websockets.connect(ws_url, additional_headers=ws_header, max_size=1000000000) as ws:
                    session_id = uuid.uuid4().hex

                    # Gửi yêu cầu khởi động phiên
                    header = bytes([
                        (0b0001 << 4) | 0b0001,  
                        0b0001 << 4 | 0b1011,     
                        0b0001 << 4 | 0b0000,
                    ])
                    optional = bytearray()
                    optional.extend((1).to_bytes(4, "big", signed=True))
                    session_id_bytes = session_id.encode()
                    optional.extend(len(session_id_bytes).to_bytes(4, "big", signed=True))
                    optional.extend(session_id_bytes)
                    payload = json.dumps({"speaker": speaker}).encode()
                    await ws.send(header + optional + len(payload).to_bytes(4, "big", signed=True) + payload)

                    # Gửi text
                    header = bytes([
                        (0b0001 << 4) | 0b0001,  
                        0b0001 << 4 | 0b1011,    
                        0b0001 << 4 | 0b0000,
                        0
                    ])
                    optional = bytearray()
                    optional.extend((200).to_bytes(4, "big", signed=True))
                    session_id_bytes = session_id.encode()
                    optional.extend(len(session_id_bytes).to_bytes(4, "big", signed=True))
                    optional.extend(session_id_bytes)
                    payload = json.dumps({"text": text, "speaker": speaker}).encode()
                    await ws.send(header + optional + len(payload).to_bytes(4, "big", signed=True) + payload)

                    first_chunk = await ws.recv()
                    latency = time.time() - start_time
                    latencies.append(latency)
                    print(f"[Huoshan Engine TTS] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")

            except Exception as e:
                print(f"[Huoshan Engine TTS] Lần {i+1} kiểm tra thất bại: {str(e)}")
                latencies.append(None)
        
        return self._calculate_result("Huoshan Engine TTS", latencies, test_count)

    async def test_paddlespeech_tts(self, text=None, test_count=5):
        """Kiểm tra độ trễ từ đầu của TTS streaming PaddleSpeech (kiểm tra nhiều lần lấy trung bình)"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["PaddleSpeechTTS"]
                tts_url = tts_config["url"]
                spk_id = tts_config["spk_id"]
                speed = tts_config["speed"]
                volume = tts_config["volume"]

                start_time = time.time()
                async with websockets.connect(tts_url) as ws:
                    # Gửi yêu cầu bắt đầu
                    await ws.send(json.dumps({
                        "task": "tts",
                        "signal": "start"
                    }))
                    
                    start_response = json.loads(await ws.recv())
                    if start_response.get("status") != 0:
                        raise Exception("Kết nối thất bại")
                    
                    # Gửi dữ liệu text
                    await ws.send(json.dumps({
                        "text": text,
                        "spk_id": spk_id,
                        "speed": speed,
                        "volume": volume
                    }))
                    
                    # Nhận khối dữ liệu đầu tiên
                    first_chunk = await ws.recv()
                    latency = time.time() - start_time
                    latencies.append(latency)
                    print(f"[PaddleSpeechTTS] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")

                    # Gửi yêu cầu kết thúc
                    end_request = {
                        "task": "tts",
                        "signal": "end"
                    }
                    await ws.send(json.dumps(end_request))

                    # Đảm bảo kết nối đóng bình thường
                    try:
                        await ws.recv()
                    except websockets.exceptions.ConnectionClosedOK:
                        pass

            except Exception as e:
                print(f"[PaddleSpeechTTS] Lần {i+1} kiểm tra thất bại: {str(e)}")
                latencies.append(None)
        
        return self._calculate_result("PaddleSpeechTTS", latencies, test_count)
            
    async def test_indexstream_tts(self, text=None, test_count=5):
        """Kiểm tra độ trễ từ đầu của TTS streaming IndexStream (kiểm tra nhiều lần lấy trung bình)"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["IndexStreamTTS"]
                api_url = tts_config.get("api_url")
                voice = tts_config.get("voice")

                # Điểm bắt đầu tính thời gian thống nhất: Bắt đầu tính trước khi thiết lập kết nối
                start_time = time.time()

                async with aiohttp.ClientSession() as session:
                    payload = {"text": text, "character": voice}
                    async with session.post(api_url, json=payload, timeout=10) as resp:
                        if resp.status != 200:
                            raise Exception(f"Yêu cầu thất bại: {resp.status}, {await resp.text()}")

                        async for chunk in resp.content.iter_any():
                            data = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
                            if not data:
                                continue

                            latency = time.time() - start_time
                            latencies.append(latency)
                            print(f"[IndexStreamTTS] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")
                            resp.close()
                            break
                        else:
                            latencies.append(None)

            except Exception as e:
                print(f"[IndexStreamTTS] Lần {i+1} kiểm tra thất bại: {str(e)}")
                latencies.append(None)
        
        return self._calculate_result("IndexStreamTTS", latencies, test_count)

    async def test_linkerai_tts(self, text=None, test_count=5):
        """Kiểm tra độ trễ từ đầu của TTS streaming Linkerai (kiểm tra nhiều lần lấy trung bình)"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["LinkeraiTTS"]
                api_url = tts_config["api_url"]
                access_token = tts_config["access_token"]
                voice = tts_config["voice"]

                # Điểm bắt đầu tính thời gian thống nhất: Bắt đầu tính trước khi thiết lập kết nối
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    params = {
                        "tts_text": text,
                        "spk_id": voice,
                        "frame_durition": 60,
                        "stream": "true",
                        "target_sr": 16000,
                        "audio_format": "pcm",
                        "instruct_text": "Vui lòng tạo một đoạn giọng nói tự nhiên và mượt mà",
                    }
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    }

                    async with session.get(api_url, params=params, headers=headers, timeout=10) as resp:
                        if resp.status != 200:
                            raise Exception(f"Yêu cầu thất bại: {resp.status}, {await resp.text()}")

                        # Nhận khối dữ liệu đầu tiên
                        async for _ in resp.content.iter_any():
                            latency = time.time() - start_time
                            latencies.append(latency)
                            print(f"[LinkeraiTTS] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")
                            break
                        else:
                            latencies.append(None)

            except Exception as e:
                print(f"[LinkeraiTTS] Lần {i+1} kiểm tra thất bại: {str(e)}")
                latencies.append(None)
        
        return self._calculate_result("LinkeraiTTS", latencies, test_count)
    
    async def test_xunfei_tts(self, text=None, test_count=5):
        """Kiểm tra độ trễ từ đầu của TTS streaming XunFei (kiểm tra nhiều lần lấy trung bình)"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                # Sửa tên node cấu hình, khớp với XunFeiTTS trong file cấu hình
                tts_config = self.config["TTS"]["XunFeiTTS"]
                app_id = tts_config["app_id"]
                api_key = tts_config["api_key"]
                api_secret = tts_config["api_secret"]
                api_url = tts_config.get("api_url", "wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6")
                voice = tts_config.get("voice", "x5_lingxiaoxuan_flow")
                # Tạo URL xác thực
                auth_url = self._create_xunfei_auth_url(api_key, api_secret, api_url)
                start_time = time.time()
                async with websockets.connect(
                    auth_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10,
                    max_size=1000000000
                ) as ws:
                    # Tạo yêu cầu
                    request = self._build_xunfei_request(app_id, text, voice)
                    await ws.send(json.dumps(request))
                    # Chờ khối dữ liệu audio đầu tiên
                    first_audio_received = False
                    while not first_audio_received:
                        msg = await asyncio.wait_for(ws.recv(), timeout=10)
                        data = json.loads(msg)
                        header = data.get("header", {})
                        code = header.get("code")

                        if code != 0:
                            message = header.get("message", "Lỗi không xác định")
                            raise Exception(f"Tổng hợp thất bại: {code} - {message}")

                        payload = data.get("payload", {})
                        audio_payload = payload.get("audio", {})

                        if audio_payload:
                            status = audio_payload.get("status", 0)
                            audio_data = audio_payload.get("audio", "")
                            if status == 1 and audio_data:
                                # Nhận khối dữ liệu audio đầu tiên
                                latency = time.time() - start_time
                                latencies.append(latency)
                                print(f"[XunFei TTS] Lần {i+1} độ trễ từ đầu: {latency:.3f}s")
                                first_audio_received = True
                                break
            except Exception as e:
                print(f"[XunFei TTS] Lần {i+1} kiểm tra thất bại: {str(e)}")
                latencies.append(None)
        
        return self._calculate_result("XunFei TTS", latencies, test_count)
    
    def _create_xunfei_auth_url(self, api_key, api_secret, api_url):
        """Tạo URL xác thực WebSocket XunFei"""
        parsed_url = urlparse(api_url)
        host = parsed_url.netloc
        path = parsed_url.path
        
        # Lấy thời gian UTC, XunFei yêu cầu sử dụng định dạng RFC1123
        now = time.gmtime()
        date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', now)
        
        # Tạo chuỗi chữ ký
        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        
        # Tính toán chữ ký
        signature_sha = hmac.new(
            api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        # Tạo authorization
        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # Tạo WebSocket URL cuối cùng
        v = {
            "authorization": authorization,
            "date": date,
            "host": host
        }
        url = api_url + '?' + urlencode(v)
        return url
    
    def _build_xunfei_request(self, app_id, text, voice):
        """Tạo cấu trúc yêu cầu TTS XunFei"""
        return {
            "header": {
                "app_id": app_id,
                "status": 2,
            },
            "parameter": {
                "oral": {
                    "oral_level": "mid",
                    "spark_assist": 1,
                    "stop_split": 0,
                    "remain": 0
                },
                "tts": {
                    "vcn": voice,
                    "speed": 50,
                    "volume": 50,
                    "pitch": 50,
                    "bgs": 0,
                    "reg": 0,
                    "rdn": 0,
                    "rhy": 0,
                    "audio": {
                        "encoding": "raw",
                        "sample_rate": 24000,
                        "channels": 1,
                        "bit_depth": 16,
                        "frame_size": 0
                    }
                }
            },
            "payload": {
                "text": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain",
                    "status": 2,
                    "seq": 1,
                    "text": base64.b64encode(text.encode('utf-8')).decode('utf-8')
                }
            }
        }


    def _calculate_result(self, service_name, latencies, test_count):
        """Tính toán kết quả kiểm tra (xử lý đúng giá trị None, loại bỏ các test thất bại)"""
        # Loại bỏ các test thất bại (giá trị None và độ trễ <=0), chỉ thống kê độ trễ hợp lệ
        valid_latencies = [l for l in latencies if l is not None and l > 0]
        if valid_latencies:
            avg_latency = sum(valid_latencies) / len(valid_latencies)
            status = f"Thành công ({len(valid_latencies)}/{test_count} lần hợp lệ)"
        else:
            avg_latency = 0
            status = "Thất bại: Tất cả các test đều thất bại"
        return {"name": service_name, "latency": avg_latency, "status": status}

    def _print_results(self, test_text, test_count):
        """In kết quả kiểm tra"""
        if not self.results:
            print("Không có kết quả kiểm tra TTS hợp lệ")
            return

        print(f"\n{'='*60}")
        print("Kết quả kiểm tra độ trễ từ đầu TTS streaming")
        print(f"{'='*60}")
        print(f"Text kiểm tra: {test_text}")
        print(f"Số lần kiểm tra: Mỗi dịch vụ TTS kiểm tra {test_count} lần")

        # Sắp xếp kết quả: Ưu tiên thành công, sắp xếp theo độ trễ tăng dần
        success_results = sorted(
            [r for r in self.results if "Thành công" in r["status"]],
            key=lambda x: x["latency"]
        )
        failed_results = [r for r in self.results if "Thành công" not in r["status"]]

        table_data = [
            [r["name"], f"{r['latency']:.3f}", r["status"]]
            for r in success_results + failed_results
        ]

        print(tabulate(table_data, headers=["Dịch vụ TTS", "Độ trễ từ đầu (giây)", "Trạng thái"], tablefmt="grid"))
        print("\nHướng dẫn kiểm tra: Đo thời gian từ khi thiết lập kết nối đến khi nhận khối dữ liệu audio đầu tiên (bao gồm bắt tay, xác thực, gửi text), lấy trung bình nhiều lần kiểm tra")
        print("- Điểm bắt đầu tính thời gian: Trước khi thiết lập kết nối WebSocket/HTTP (thống nhất bao gồm toàn bộ quy trình kết nối mạng, bắt tay, gửi text)")
        print("- Kiểm soát timeout: Thời gian chờ tối đa cho một yêu cầu là 10 giây")
        print("- Xử lý lỗi: Các test thất bại không tính vào trung bình, chỉ thống kê độ trễ của các test thành công")
        print("- Quy tắc sắp xếp: Sắp xếp theo thời gian trung bình từ nhanh đến chậm")


    async def run(self, test_text=None, test_count=5):
        """Thực thi kiểm tra
        
        Args:
            test_text: Text cần kiểm tra, nếu là None thì sử dụng text mặc định
            test_count: Số lần kiểm tra cho mỗi dịch vụ TTS
        """
        test_text = test_text or self.test_texts[0]
        print(f"Bắt đầu kiểm tra độ trễ từ đầu TTS streaming...")
        print(f"Text kiểm tra: {test_text}")
        print(f"Số lần kiểm tra mỗi dịch vụ TTS: {test_count} lần")
        
        if not self.config.get("TTS"):
            print("Không tìm thấy cấu hình TTS trong file cấu hình")
            return
        
        # Kiểm tra từng loại dịch vụ TTS
        self.results = []
        
        # Kiểm tra Aliyun TTS
        result = await self.test_aliyun_tts(test_text, test_count)
        self.results.append(result)

        # Kiểm tra Aliyun BaiLian TTS
        if self.config.get("TTS", {}).get("AliBLTTS"):
            result = await self.test_alibl_tts(test_text, test_count)
            self.results.append(result)

        # Kiểm tra Huoshan Engine TTS
        result = await self.test_doubao_tts(test_text, test_count)
        self.results.append(result)
        
        # Kiểm tra PaddleSpeech TTS
        result = await self.test_paddlespeech_tts(test_text, test_count)
        self.results.append(result)
        
        # Kiểm tra Linkerai TTS
        result = await self.test_linkerai_tts(test_text, test_count)
        self.results.append(result)
        
        # Kiểm tra IndexStreamTTS
        result = await self.test_indexstream_tts(test_text, test_count)
        self.results.append(result)
        
        # Kiểm tra XunFei TTS
        if self.config.get("TTS", {}).get("XunFeiTTS"):
            result = await self.test_xunfei_tts(test_text, test_count)
            self.results.append(result)
        
        # In kết quả
        self._print_results(test_text, test_count)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Công cụ kiểm tra độ trễ từ đầu TTS streaming")
    parser.add_argument("--text", help="Nội dung text cần kiểm tra")
    parser.add_argument("--count", type=int, default=5, help="Số lần kiểm tra cho mỗi dịch vụ TTS")
    
    args = parser.parse_args()
    await StreamTTSPerformanceTester().run(args.text, args.count)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())