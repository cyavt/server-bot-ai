import os
import uuid
import edge_tts
from datetime import datetime
from core.providers.tts.base import TTSProviderBase


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("voice")
        self.audio_file_type = config.get("format", "mp3")

    def generate_filename(self, extension=".mp3"):
        return os.path.join(
            self.output_file,
            f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}",
        )

    async def text_to_speak(self, text, output_file):
        try:
            # Kiểm tra voice có hợp lệ không
            if not self.voice:
                raise ValueError("Voice không được chỉ định trong cấu hình EdgeTTS")
            
            # Kiểm tra text có rỗng không
            if not text or not text.strip():
                raise ValueError("Văn bản đầu vào rỗng")
            
            communicate = edge_tts.Communicate(text, voice=self.voice)
            
            audio_received = False
            if output_file:
                # Đảm bảo thư mục tồn tại và tạo tệp trống
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, "wb") as f:
                    pass

                # Ghi dữ liệu âm thanh theo luồng
                with open(output_file, "ab") as f:  # Đổi sang chế độ nối thêm để tránh ghi đè
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":  # Chỉ xử lý khối dữ liệu âm thanh
                            f.write(chunk["data"])
                            audio_received = True
            else:
                # Trả về dữ liệu nhị phân âm thanh
                audio_bytes = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_bytes += chunk["data"]
                        audio_received = True
                if not audio_received:
                    raise ValueError("Không nhận được dữ liệu âm thanh từ EdgeTTS")
                return audio_bytes
            
            # Kiểm tra xem có nhận được audio không
            if not audio_received:
                raise ValueError(f"Không nhận được dữ liệu âm thanh. Voice: {self.voice}, Text length: {len(text)}")
                
        except Exception as e:
            error_msg = f"Yêu cầu Edge TTS thất bại: {e}"
            # Xử lý exception message an toàn với Unicode
            try:
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                else:
                    error_msg = str(error_msg).encode('utf-8', errors='replace').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                error_msg = repr(e)
            raise Exception(error_msg)  # Ném ngoại lệ để bên gọi bắt