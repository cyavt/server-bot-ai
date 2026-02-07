import time
import numpy as np
import torch
import opuslib_next
from config.logger import setup_logging
from core.providers.vad.base import VADProviderBase

TAG = __name__
logger = setup_logging()


class VADProvider(VADProviderBase):
    def __init__(self, config):
        logger.bind(tag=TAG).info("SileroVAD", config)
        self.model, _ = torch.hub.load(
            repo_or_dir=config["model_dir"],
            source="local",
            model="silero_vad",
            force_reload=False,
        )

        self.decoder = opuslib_next.Decoder(16000, 1)

        # Xử lý trường hợp chuỗi rỗng
        threshold = config.get("threshold", "0.5")
        threshold_low = config.get("threshold_low", "0.2")
        min_silence_duration_ms = config.get("min_silence_duration_ms", "1000")

        self.vad_threshold = float(threshold) if threshold else 0.5
        self.vad_threshold_low = float(threshold_low) if threshold_low else 0.2

        self.silence_threshold_ms = (
            int(min_silence_duration_ms) if min_silence_duration_ms else 1000
        )

        # Cần ít nhất bao nhiêu frame mới được tính là có giọng nói
        self.frame_window_threshold = 3

    def __del__(self):
        if hasattr(self, 'decoder') and self.decoder is not None:
            try:
                del self.decoder
            except Exception:
                pass

    def is_vad(self, conn, opus_packet):
        # Chế độ thủ công: trả về True trực tiếp, không thực hiện phát hiện VAD thời gian thực, tất cả audio đều được cache
        if conn.client_listen_mode == "manual":
            return True
            
        try:
            pcm_frame = self.decoder.decode(opus_packet, 960)
            conn.client_audio_buffer.extend(pcm_frame)  # Thêm dữ liệu mới vào buffer

            # Xử lý các frame hoàn chỉnh trong buffer (mỗi lần xử lý 512 điểm mẫu)
            client_have_voice = False
            while len(conn.client_audio_buffer) >= 512 * 2:
                # Trích xuất 512 điểm mẫu đầu tiên (1024 byte)
                chunk = conn.client_audio_buffer[: 512 * 2]
                conn.client_audio_buffer = conn.client_audio_buffer[512 * 2 :]

                # Chuyển đổi sang định dạng tensor mà model cần
                audio_int16 = np.frombuffer(chunk, dtype=np.int16)
                audio_float32 = audio_int16.astype(np.float32) / 32768.0
                audio_tensor = torch.from_numpy(audio_float32)

                # Phát hiện hoạt động giọng nói
                with torch.no_grad():
                    speech_prob = self.model(audio_tensor, 16000).item()

                # Phán đoán ngưỡng kép
                if speech_prob >= self.vad_threshold:
                    is_voice = True
                elif speech_prob <= self.vad_threshold_low:
                    is_voice = False
                else:
                    is_voice = conn.last_is_voice

                # Nếu âm thanh không thấp hơn giá trị tối thiểu thì tiếp tục trạng thái trước, phán đoán là có giọng nói
                conn.last_is_voice = is_voice

                # Cập nhật cửa sổ trượt
                conn.client_voice_window.append(is_voice)
                client_have_voice = (
                    conn.client_voice_window.count(True) >= self.frame_window_threshold
                )

                # Nếu trước đó có giọng nói, nhưng lần này không có giọng nói, và khoảng thời gian từ lần có giọng nói cuối cùng đã vượt quá ngưỡng im lặng, thì cho rằng đã nói xong một câu
                if conn.client_have_voice and not client_have_voice:
                    stop_duration = time.time() * 1000 - conn.last_activity_time
                    if stop_duration >= self.silence_threshold_ms:
                        conn.client_voice_stop = True
                if client_have_voice:
                    conn.client_have_voice = True
                    conn.last_activity_time = time.time() * 1000

            return client_have_voice
        except opuslib_next.OpusError as e:
            logger.bind(tag=TAG).info(f"Lỗi giải mã: {e}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error processing audio packet: {e}")
