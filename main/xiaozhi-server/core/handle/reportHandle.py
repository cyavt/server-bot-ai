"""
Chức năng báo cáo TTS đã được tích hợp vào lớp ConnectionHandler.

Chức năng báo cáo bao gồm:
1. Mỗi đối tượng kết nối có hàng đợi báo cáo và luồng xử lý riêng
2. Vòng đời luồng báo cáo được liên kết với đối tượng kết nối
3. Sử dụng phương thức ConnectionHandler.enqueue_tts_report để báo cáo

Vui lòng tham khảo mã liên quan trong core/connection.py để biết cách triển khai cụ thể.
"""

import time
import opuslib_next
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

from config.manage_api_client import report as manage_report

TAG = __name__


async def report(conn: "ConnectionHandler", type, text, opus_data, report_time):
    """Thực thi thao tác báo cáo lịch sử trò chuyện

    Args:
        conn: Đối tượng kết nối
        type: Loại báo cáo, 1 là người dùng, 2 là tác nhân thông minh
        text: Văn bản tổng hợp
        opus_data: Dữ liệu âm thanh opus
        report_time: Thời gian báo cáo
    """
    try:
        if opus_data:
            audio_data = opus_to_wav(conn, opus_data)
        else:
            audio_data = None
        # Thực thi báo cáo bất đồng bộ
        await manage_report(
            mac_address=conn.device_id,
            session_id=conn.session_id,
            chat_type=type,
            content=text,
            audio=audio_data,
            report_time=report_time,
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Báo cáo lịch sử trò chuyện thất bại: {e}")


def opus_to_wav(conn: "ConnectionHandler", opus_data):
    """Chuyển đổi dữ liệu Opus thành luồng byte định dạng WAV

    Args:
        output_dir: Thư mục đầu ra (giữ tham số để tương thích giao diện)
        opus_data: Dữ liệu âm thanh opus

    Returns:
        bytes: Dữ liệu âm thanh định dạng WAV
    """
    decoder = None
    try:
        decoder = opuslib_next.Decoder(16000, 1)  # 16kHz, đơn kênh
        pcm_data = []

        for opus_packet in opus_data:
            try:
                pcm_frame = decoder.decode(opus_packet, 960)  # 960 samples = 60ms
                pcm_data.append(pcm_frame)
            except opuslib_next.OpusError as e:
                conn.logger.bind(tag=TAG).error(f"Lỗi giải mã Opus: {e}", exc_info=True)

        if not pcm_data:
            raise ValueError("Không có dữ liệu PCM hợp lệ")

        # Tạo header tệp WAV
        pcm_data_bytes = b"".join(pcm_data)
        num_samples = len(pcm_data_bytes) // 2  # 16-bit samples

        # Header tệp WAV
        wav_header = bytearray()
        wav_header.extend(b"RIFF")  # ChunkID
        wav_header.extend((36 + len(pcm_data_bytes)).to_bytes(4, "little"))  # ChunkSize
        wav_header.extend(b"WAVE")  # Format
        wav_header.extend(b"fmt ")  # Subchunk1ID
        wav_header.extend((16).to_bytes(4, "little"))  # Subchunk1Size
        wav_header.extend((1).to_bytes(2, "little"))  # AudioFormat (PCM)
        wav_header.extend((1).to_bytes(2, "little"))  # NumChannels
        wav_header.extend((16000).to_bytes(4, "little"))  # SampleRate
        wav_header.extend((32000).to_bytes(4, "little"))  # ByteRate
        wav_header.extend((2).to_bytes(2, "little"))  # BlockAlign
        wav_header.extend((16).to_bytes(2, "little"))  # BitsPerSample
        wav_header.extend(b"data")  # Subchunk2ID
        wav_header.extend(len(pcm_data_bytes).to_bytes(4, "little"))  # Subchunk2Size

        # Trả về dữ liệu WAV đầy đủ
        return bytes(wav_header) + pcm_data_bytes
    finally:
        if decoder is not None:
            try:
                del decoder
            except Exception as e:
                conn.logger.bind(tag=TAG).debug(f"Lỗi khi giải phóng tài nguyên decoder: {e}")


def enqueue_tts_report(conn: "ConnectionHandler", text, opus_data):
    if not conn.read_config_from_api or conn.need_bind or not conn.report_tts_enable:
        return
    if conn.chat_history_conf == 0:
        return
    """Thêm dữ liệu TTS vào hàng đợi báo cáo

    Args:
        conn: Đối tượng kết nối
        text: Văn bản tổng hợp
        opus_data: Dữ liệu âm thanh opus
    """
    try:
        # Sử dụng hàng đợi của đối tượng kết nối, truyền văn bản và dữ liệu nhị phân thay vì đường dẫn tệp
        if conn.chat_history_conf == 2:
            conn.report_queue.put((2, text, opus_data, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"Dữ liệu TTS đã được thêm vào hàng đợi báo cáo: {conn.device_id}, kích thước âm thanh: {len(opus_data)} "
            )
        else:
            conn.report_queue.put((2, text, None, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"Dữ liệu TTS đã được thêm vào hàng đợi báo cáo: {conn.device_id}, không báo cáo âm thanh"
            )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Thêm vào hàng đợi báo cáo TTS thất bại: {text}, {e}")


def enqueue_asr_report(conn: "ConnectionHandler", text, opus_data):
    if not conn.read_config_from_api or conn.need_bind or not conn.report_asr_enable:
        return
    if conn.chat_history_conf == 0:
        return
    """Thêm dữ liệu ASR vào hàng đợi báo cáo

    Args:
        conn: Đối tượng kết nối
        text: Văn bản tổng hợp
        opus_data: Dữ liệu âm thanh opus
    """
    try:
        # Sử dụng hàng đợi của đối tượng kết nối, truyền văn bản và dữ liệu nhị phân thay vì đường dẫn tệp
        if conn.chat_history_conf == 2:
            conn.report_queue.put((1, text, opus_data, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"Dữ liệu ASR đã được thêm vào hàng đợi báo cáo: {conn.device_id}, kích thước âm thanh: {len(opus_data)} "
            )
        else:
            conn.report_queue.put((1, text, None, int(time.time())))
            conn.logger.bind(tag=TAG).debug(
                f"Dữ liệu ASR đã được thêm vào hàng đợi báo cáo: {conn.device_id}, không báo cáo âm thanh"
            )
    except Exception as e:
        conn.logger.bind(tag=TAG).debug(f"Thêm vào hàng đợi báo cáo ASR thất bại: {text}, {e}")
