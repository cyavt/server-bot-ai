import io
import wave
import json
import base64
import asyncio
import websockets
import numpy as np
from datetime import datetime
from config.logger import setup_logging
from core.providers.tts.base import TTSProviderBase



TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.url = config.get("url", "ws://192.168.1.10:8092/paddlespeech/tts/streaming")
        self.protocol = config.get("protocol", "websocket")
        
        if config.get("private_voice"):
            self.spk_id = int(config.get("private_voice"))
        else:
            self.spk_id = int(config.get("spk_id", "0"))

        speed = config.get("speed", 1.0)
        self.speed = float(speed) if speed else 1.0
        
        volume = config.get("volume", 1.0)
        self.volume = float(volume) if volume else 1.0
        
        self.delete_audio_file = config.get("delete_audio", True)
        if not self.delete_audio_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = config.get("save_path")
            if save_path:
                if not save_path.endswith('.wav'):
                    save_path = f"{save_path}_{timestamp}.wav"
                else:
                    other_path = save_path[:-4]
                    save_path = f"{other_path}_{timestamp}.wav"
                self.save_path = save_path
            else:
                self.save_path = f"./streaming_tts_{timestamp}.wav"
        else:
            self.save_path = None

    async def pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 24000, num_channels: int = 1,
                         bits_per_sample: int = 16) -> bytes:
        """
        Chuyển đổi dữ liệu PCM sang file WAV và trả về dữ liệu byte
        :param pcm_data: Dữ liệu PCM (luồng byte gốc)
        :param sample_rate: Tần số lấy mẫu audio, mặc định 24000
        :param num_channels: Số kênh, mặc định mono
        :param bits_per_sample: Số bit mỗi mẫu, mặc định 16
        :return: Dữ liệu byte định dạng WAV
        """
        byte_data = np.frombuffer(pcm_data, dtype=np.int16)  # PCM 16-bit
        wav_io = io.BytesIO()

        with wave.open(wav_io, "wb") as wav_file:
            wav_file.setnchannels(num_channels)
            wav_file.setsampwidth(bits_per_sample // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(byte_data.tobytes())

        return wav_io.getvalue()

    async def text_to_speak(self, text, output_file):
        if self.protocol == "websocket":
            return await self.text_streaming(text, output_file)
        else:
            raise ValueError("Unsupported protocol. Please use 'websocket' or 'http'.")

    async def text_streaming(self, text, output_file):
        try:
            # Sử dụng websockets kết nối bất đồng bộ đến WebSocket server
            async with websockets.connect(self.url) as ws:
                # Gửi yêu cầu bắt đầu
                start_request = {
                    "task": "tts",
                    "signal": "start"
                }
                await ws.send(json.dumps(start_request))

                # Nhận phản hồi bắt đầu và trích xuất session_id
                start_response = await ws.recv()
                start_response = json.loads(start_response)  # Phân tích phản hồi JSON
                if start_response.get("status") != 0:
                    raise Exception(f"Kết nối thất bại: {start_response.get('signal')}")

                session_id = start_response.get("session")

                # Gửi dữ liệu văn bản cần tổng hợp
                data_request = {
                    "text": text,
                    "spk_id": self.spk_id,
                }
                await ws.send(json.dumps(data_request))

                audio_chunks = b""
                timeout_seconds = 60  # Thiết lập timeout
                try:
                    while True:
                        response = await asyncio.wait_for(ws.recv(), timeout=timeout_seconds)
                        response = json.loads(response)  # Phân tích phản hồi JSON
                        status = response.get("status")

                        if status == 2:  # Gói dữ liệu cuối cùng
                            break
                        else:
                            # Nối dữ liệu audio (dữ liệu PCM được mã hóa base64)
                            audio_chunks += base64.b64decode(response.get("audio"))
                except asyncio.TimeoutError:
                    raise Exception(f"WebSocket timeout: chờ dữ liệu audio vượt quá {timeout_seconds} giây")

                # Chuyển đổi dữ liệu PCM đã nối sang định dạng WAV
                wav_data = await self.pcm_to_wav(audio_chunks)

                # Yêu cầu kết thúc
                end_request = {
                    "task": "tts",
                    "signal": "end",
                    "session": session_id  # ID phiên phải khớp với yêu cầu bắt đầu
                }
                await ws.send(json.dumps(end_request))

                # Nhận phản hồi kết thúc để tránh service ném ngoại lệ
                await ws.recv()

                # Quyết định có lưu file hay không dựa trên cấu hình
                if not self.delete_audio_file and self.save_path:
                    with open(self.save_path, "wb") as f:
                        f.write(wav_data)
                    logger.bind(tag=TAG).info(f"File audio đã được lưu tại: {self.save_path}")
                
                # Trả về hoặc lưu dữ liệu audio
                if output_file:
                    with open(output_file, "wb") as file_to_save:
                        file_to_save.write(wav_data)
                else:
                    return wav_data

        except Exception as e:
            raise Exception(f"Error during TTS WebSocket request: {e} while processing text: {text}")