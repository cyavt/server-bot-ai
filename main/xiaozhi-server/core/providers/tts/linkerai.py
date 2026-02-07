import os
import time
import queue
import aiohttp
import asyncio
import requests
import traceback
from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.providers.tts.base import TTSProviderBase
from core.utils import opus_encoder_utils, textUtils
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.interface_type = InterfaceType.SINGLE_STREAM
        self.access_token = config.get("access_token")
        self.voice = config.get("voice")
        self.api_url = config.get("api_url")
        self.audio_format = "pcm"
        self.before_stop_play_files = []

        # Buffer PCM
        self.pcm_buffer = bytearray()

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
        await self._tts_request(text, is_last)

    async def close(self):
        """Dọn dẹp tài nguyên"""
        await super().close()
        if hasattr(self, "opus_encoder"):
            self.opus_encoder.close()

    async def _tts_request(self, text: str, is_last: bool) -> None:
        params = {
            "tts_text": text,
            "spk_id": self.voice,
            "frame_durition": 60,
            "stream": "true",
            "target_sr": self.conn.sample_rate,
            "audio_format": "pcm",
            "instruct_text": "Vui lòng tạo một đoạn giọng nói tự nhiên và mượt mà",
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # Số byte cần cho một frame PCM: 60 ms × sample_rate × 1 ch × 2 B
        frame_bytes = int(
            self.opus_encoder.sample_rate
            * self.opus_encoder.channels  # 1
            * self.opus_encoder.frame_size_ms
            / 1000
            * 2
        )  # 16-bit = 2 bytes

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url, params=params, headers=headers, timeout=10
                ) as resp:

                    if resp.status != 200:
                        logger.bind(tag=TAG).error(
                            f"Yêu cầu TTS thất bại: {resp.status}, {await resp.text()}"
                        )
                        self.tts_audio_queue.put((SentenceType.LAST, [], None))
                        return

                    self.pcm_buffer.clear()
                    self.tts_audio_queue.put((SentenceType.FIRST, [], text))

                    # Tương thích iter_chunked / iter_chunks / iter_any
                    async for chunk in resp.content.iter_any():
                        data = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
                        if not data:
                            continue

                        # Nối vào buffer
                        self.pcm_buffer.extend(data)

                        # Đủ một frame thì mã hóa
                        while len(self.pcm_buffer) >= frame_bytes:
                            frame = bytes(self.pcm_buffer[:frame_bytes])
                            del self.pcm_buffer[:frame_bytes]

                            self.opus_encoder.encode_pcm_to_opus_stream(
                                frame,
                                end_of_stream=False,
                                callback=self.handle_opus
                            )

                    # Xả dữ liệu còn lại không đủ một frame
                    if self.pcm_buffer:
                        self.opus_encoder.encode_pcm_to_opus_stream(
                            bytes(self.pcm_buffer),
                            end_of_stream=True,
                            callback=self.handle_opus
                        )
                        self.pcm_buffer.clear()

                    # Nếu là đoạn cuối, việc lấy audio đầu ra đã hoàn tất
                    if is_last:
                        self._process_before_stop_play_files()

        except Exception as e:
            logger.bind(tag=TAG).error(f"Yêu cầu TTS bất thường: {e}")
            self.tts_audio_queue.put((SentenceType.LAST, [], None))

    def to_tts(self, text: str) -> list:
        """Xử lý TTS không streaming, dùng cho test và lưu file audio
        Args:
            text: Văn bản cần chuyển đổi
        Returns:
            list: Trả về danh sách dữ liệu audio đã mã hóa opus
        """
        start_time = time.time()
        text = MarkdownCleaner.clean_markdown(text)

        params = {
            "tts_text": text,
            "spk_id": self.voice,
            "frame_duration": 60,
            "stream": False,
            "target_sr": self.conn.sample_rate,
            "audio_format": self.audio_format,
            "instruct_text": "Vui lòng tạo một đoạn giọng nói tự nhiên và mượt mà",
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            with requests.get(
                self.api_url, params=params, headers=headers, timeout=5
            ) as response:
                if response.status_code != 200:
                    logger.bind(tag=TAG).error(
                        f"Yêu cầu TTS thất bại: {response.status_code}, {response.text}"
                    )
                    return []

                logger.info(f"Yêu cầu TTS thành công: {text}, thời gian: {time.time() - start_time} giây")

                # Sử dụng bộ mã hóa opus để xử lý dữ liệu PCM
                opus_datas = []
                pcm_data = response.content

                # Tính số byte mỗi frame
                frame_bytes = int(
                    self.opus_encoder.sample_rate
                    * self.opus_encoder.channels
                    * self.opus_encoder.frame_size_ms
                    / 1000
                    * 2
                )

                # Xử lý phân frame dữ liệu PCM
                for i in range(0, len(pcm_data), frame_bytes):
                    frame = pcm_data[i : i + frame_bytes]
                    if len(frame) < frame_bytes:
                        # Frame cuối có thể không đủ, dùng 0 để lấp đầy
                        frame = frame + b"\x00" * (frame_bytes - len(frame))

                    self.opus_encoder.encode_pcm_to_opus_stream(
                        frame,
                        end_of_stream=(i + frame_bytes >= len(pcm_data)),
                        callback=lambda opus: opus_datas.append(opus)
                    )

                return opus_datas

        except Exception as e:
            logger.bind(tag=TAG).error(f"Yêu cầu TTS bất thường: {e}")
            return []