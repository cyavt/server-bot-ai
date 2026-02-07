import os
import json
import time
import queue
import asyncio
import aiohttp
import requests
import traceback
from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.utils.util import parse_string_to_list
from core.providers.tts.base import TTSProviderBase
from core.utils import opus_encoder_utils, textUtils
from core.providers.tts.dto.dto import SentenceType, ContentType

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.group_id = config.get("group_id")
        self.api_key = config.get("api_key")
        self.model = config.get("model")
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("voice_id")

        default_voice_setting = {
            "voice_id": "female-shaonv",
            "speed": 1,
            "vol": 1,
            "pitch": 0,
            "emotion": "happy",
        }
        default_pronunciation_dict = {"tone": ["处理/(chu3)(li3)", "危险/dangerous"]}
        defult_audio_setting = {
            "sample_rate": 24000,
            "bitrate": 128000,
            "format": "pcm",
            "channel": 1,
        }
        self.voice_setting = {
            **default_voice_setting,
            **config.get("voice_setting", {}),
        }
        self.pronunciation_dict = {
            **default_pronunciation_dict,
            **config.get("pronunciation_dict", {}),
        }
        self.audio_setting = {**defult_audio_setting, **config.get("audio_setting", {})}
        self.timber_weights = parse_string_to_list(config.get("timber_weights"))

        if self.voice:
            self.voice_setting["voice_id"] = self.voice

        self.host = "api.minimaxi.com"  # Địa chỉ dự phòng: api-bj.minimaxi.com
        self.api_url = f"https://{self.host}/v1/t2a_v2?GroupId={self.group_id}"
        self.header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.audio_file_type = defult_audio_setting.get("format", "pcm")

        # Buffer PCM
        self.pcm_buffer = bytearray()

    async def open_audio_channels(self, conn):
        """Khởi tạo kênh audio và cập nhật cấu hình theo conn.sample_rate"""
        # Gọi phương thức của lớp cha
        await super().open_audio_channels(conn)

        # Cập nhật tần số lấy mẫu trong audio_setting thành conn.sample_rate thực tế
        self.audio_setting["sample_rate"] = conn.sample_rate

    def tts_text_priority_thread(self):
        """Luồng xử lý văn bản streaming"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                if message.sentence_type == SentenceType.FIRST:
                    # Khởi tạo tham số
                    self.tts_stop_request = False
                    self.processed_chars = 0
                    self.tts_text_buff = []
                    self.before_stop_play_files.clear()
                elif ContentType.TEXT == message.content_type:
                    self.tts_text_buff.append(message.content_detail)
                    segment_text = self._get_segment_text()
                    if segment_text:
                        self.to_tts_single_stream(segment_text)

                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"Thêm file audio vào danh sách chờ phát: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        # Xử lý dữ liệu audio của file trước
                        self._process_audio_file_stream(message.content_file, callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail))
                if message.sentence_type == SentenceType.LAST:
                    # Xử lý văn bản còn lại
                    self._process_remaining_text_stream(True)

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"Xử lý văn bản TTS thất bại: {str(e)}, loại: {type(e).__name__}, stack: {traceback.format_exc()}"
                )

    def _process_remaining_text_stream(self, is_last=False):
        """Xử lý văn bản còn lại và tạo giọng nói
        Returns:
            bool: Có xử lý thành công văn bản không
        """
        full_text = "".join(self.tts_text_buff)
        remaining_text = full_text[self.processed_chars :]
        if remaining_text:
            segment_text = textUtils.get_string_no_punctuation_or_emoji(remaining_text)
            if segment_text:
                self.to_tts_single_stream(segment_text, is_last)
                self.processed_chars += len(full_text)
            else:
                self._process_before_stop_play_files()
        else:
            self._process_before_stop_play_files()

    def to_tts_single_stream(self, text, is_last=False):
        try:
            max_repeat_time = 5
            text = MarkdownCleaner.clean_markdown(text)
            try:
                asyncio.run(self.text_to_speak(text, is_last))
            except Exception as e:
                logger.bind(tag=TAG).warning(
                    f"Tạo giọng nói thất bại lần {5 - max_repeat_time + 1}: {text}, lỗi: {e}"
                )
                max_repeat_time -= 1

            if max_repeat_time > 0:
                logger.bind(tag=TAG).info(
                    f"Tạo giọng nói thành công: {text}, thử lại {5 - max_repeat_time} lần"
                )
            else:
                logger.bind(tag=TAG).error(
                    f"Tạo giọng nói thất bại: {text}, vui lòng kiểm tra mạng hoặc dịch vụ có bình thường không"
                )
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to generate TTS file: {e}")
        finally:
            return None

    async def text_to_speak(self, text, is_last):
        """Xử lý audio TTS streaming, mỗi câu chỉ đẩy một lần danh sách audio"""
        payload = {
            "model": self.model,
            "text": text,
            "stream": True,
            "voice_setting": self.voice_setting,
            "pronunciation_dict": self.pronunciation_dict,
            "audio_setting": self.audio_setting,
        }

        if type(self.timber_weights) is list and len(self.timber_weights) > 0:
            payload["timber_weights"] = self.timber_weights
            payload["voice_setting"]["voice_id"] = ""

        frame_bytes = int(
            self.opus_encoder.sample_rate
            * self.opus_encoder.channels  # 1
            * self.opus_encoder.frame_size_ms
            / 1000
            * 2
        )  # 16-bit = 2 bytes
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=self.header,
                    data=json.dumps(payload),
                    timeout=10,
                ) as resp:

                    if resp.status != 200:
                        logger.bind(tag=TAG).error(
                            f"Yêu cầu TTS thất bại: {resp.status}, {await resp.text()}"
                        )
                        self.tts_audio_queue.put((SentenceType.LAST, [], None))
                        return

                    self.pcm_buffer.clear()
                    self.tts_audio_queue.put((SentenceType.FIRST, [], text))

                    # Xử lý dữ liệu luồng audio
                    buffer = b""
                    async for chunk in resp.content.iter_any():
                        if not chunk:
                            continue

                        buffer += chunk
                        while True:
                            # Tìm ký tự phân cách khối dữ liệu
                            header_pos = buffer.find(b"data: ")
                            if header_pos == -1:
                                break

                            end_pos = buffer.find(b"\n\n", header_pos)
                            if end_pos == -1:
                                break

                            # Trích xuất khối JSON hoàn chỉnh đơn lẻ
                            json_str = buffer[header_pos + 6 : end_pos].decode("utf-8")
                            buffer = buffer[end_pos + 2 :]

                            try:
                                data = json.loads(json_str)

                                # Kiểm tra lỗi tầng nghiệp vụ
                                base_resp = data.get("base_resp", {})
                                status_code = base_resp.get("status_code", 0)
                                if status_code != 0:
                                    status_msg = base_resp.get("status_msg", "Lỗi không xác định")
                                    logger.bind(tag=TAG).error(
                                        f"Yêu cầu TTS thất bại, mã lỗi:{status_code}, thông báo lỗi:{status_msg}"
                                    )
                                    self.tts_audio_queue.put((SentenceType.LAST, [], None))
                                    return

                                status = data.get("data", {}).get("status", 1)
                                audio_hex = data.get("data", {}).get("audio")

                                # Chỉ xử lý khối audio hợp lệ status=1, bỏ qua khối tổng kết kết thúc status=2
                                if status == 1 and audio_hex:
                                    pcm_data = bytes.fromhex(audio_hex)
                                    self.pcm_buffer.extend(pcm_data)

                            except json.JSONDecodeError as e:
                                logger.bind(tag=TAG).error(f"Phân tích JSON thất bại: {e}")
                                continue

                        while len(self.pcm_buffer) >= frame_bytes:
                            frame = bytes(self.pcm_buffer[:frame_bytes])
                            del self.pcm_buffer[:frame_bytes]

                            self.opus_encoder.encode_pcm_to_opus_stream(
                                frame, end_of_stream=False, callback=self.handle_opus
                            )

                    # Xả dữ liệu còn lại không đủ một frame
                    if self.pcm_buffer:
                        self.opus_encoder.encode_pcm_to_opus_stream(
                            bytes(self.pcm_buffer),
                            end_of_stream=True,
                            callback=self.handle_opus,
                        )
                        self.pcm_buffer.clear()

                    # Nếu là đoạn cuối, việc lấy audio đầu ra đã hoàn tất
                    if is_last:
                        self._process_before_stop_play_files()

        except Exception as e:
            logger.bind(tag=TAG).error(f"Yêu cầu TTS bất thường: {e}")
            self.tts_audio_queue.put((SentenceType.LAST, [], None))

    async def close(self):
        """Dọn dẹp tài nguyên"""
        await super().close()
        if hasattr(self, "opus_encoder"):
            self.opus_encoder.close()

    def to_tts(self, text: str) -> list:
        """Xử lý TTS không streaming, dùng cho test và lưu file audio
        Args:
            text: Văn bản cần chuyển đổi
        Returns:
            list: Trả về danh sách dữ liệu audio đã mã hóa opus
        """
        start_time = time.time()
        text = MarkdownCleaner.clean_markdown(text)

        payload = {
            "model": self.model,
            "text": text,
            "stream": True,
            "voice_setting": self.voice_setting,
            "pronunciation_dict": self.pronunciation_dict,
            "audio_setting": self.audio_setting,
        }

        if type(self.timber_weights) is list and len(self.timber_weights) > 0:
            payload["timber_weights"] = self.timber_weights
            payload["voice_setting"]["voice_id"] = ""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            with requests.post(
                self.api_url, data=json.dumps(payload), headers=headers, timeout=5
            ) as response:
                if response.status_code != 200:
                    logger.bind(tag=TAG).error(
                        f"Yêu cầu TTS thất bại: {response.status_code}, {response.text}"
                    )
                    return []

                logger.info(f"Yêu cầu TTS thành công: {text}, thời gian: {time.time() - start_time} giây")

                # Sử dụng bộ mã hóa opus để xử lý dữ liệu PCM
                opus_datas = []
                full_content = response.content.decode('utf-8')
                pcm_data = bytearray()
                for data_block in full_content.split('\n\n'):
                    if not data_block.startswith('data: '):
                        continue

                    try:
                        json_str = data_block[6:]  # Loại bỏ tiền tố 'data: '
                        data = json.loads(json_str)
                        if data.get('data', {}).get('status') == 1:
                            audio_hex = data['data']['audio']
                            pcm_data.extend(bytes.fromhex(audio_hex))
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.bind(tag=TAG).warning(f"Khối dữ liệu không hợp lệ: {e}")
                        continue

                # Tính số byte mỗi frame
                frame_bytes = int(
                    self.opus_encoder.sample_rate
                    * self.opus_encoder.channels
                    * self.opus_encoder.frame_size_ms
                    / 1000
                    * 2
                )

                # Xử lý phân frame dữ liệu PCM đã hợp nhất
                for i in range(0, len(pcm_data), frame_bytes):
                    frame = bytes(pcm_data[i:i+frame_bytes])
                    if len(frame) < frame_bytes:
                        frame += b"\x00" * (frame_bytes - len(frame))
 
                    self.opus_encoder.encode_pcm_to_opus_stream(
                        frame,
                        end_of_stream=(i + frame_bytes >= len(pcm_data)),
                        callback=lambda opus: opus_datas.append(opus)
                    )

                return opus_datas

        except Exception as e:
            logger.bind(tag=TAG).error(f"Yêu cầu TTS bất thường: {e}")
            return []
