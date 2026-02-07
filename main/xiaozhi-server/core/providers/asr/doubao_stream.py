import json
import gzip
import uuid
import asyncio
import websockets
import opuslib_next
from core.providers.asr.base import ASRProviderBase
from config.logger import setup_logging
from core.providers.asr.dto.dto import InterfaceType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()


class ASRProvider(ASRProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__()
        self.interface_type = InterfaceType.STREAM
        self.config = config
        self.text = ""
        self.decoder = opuslib_next.Decoder(16000, 1)
        self.asr_ws = None
        self.forward_task = None
        self.is_processing = False  # Thêm cờ trạng thái xử lý

        # Tham số cấu hình
        self.appid = str(config.get("appid"))
        self.cluster = config.get("cluster")
        self.access_token = config.get("access_token")
        self.boosting_table_name = config.get("boosting_table_name", "")
        self.correct_table_name = config.get("correct_table_name", "")
        self.output_dir = config.get("output_dir", "tmp/")
        self.delete_audio_file = delete_audio_file

        # Cấu hình ASR Volcano Engine
        enable_multilingual = config.get("enable_multilingual", False)
        self.enable_multilingual = (
            False if str(enable_multilingual).lower() == "false" else True
        )
        if self.enable_multilingual:
            self.ws_url = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream"
        else:
            self.ws_url = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
        self.uid = config.get("uid", "streaming_asr_service")
        self.workflow = config.get(
            "workflow", "audio_in,resample,partition,vad,fe,decode,itn,nlu_punctuate"
        )
        self.result_type = config.get("result_type", "single")
        self.format = config.get("format", "pcm")
        self.codec = config.get("codec", "pcm")
        self.rate = config.get("sample_rate", 16000)
        # Tham số language chỉ có hiệu lực trong chế độ đa ngôn ngữ (bigmodel_nostream)
        self.language = config.get("language") if self.enable_multilingual else None
        self.bits = config.get("bits", 16)
        self.channel = config.get("channel", 1)
        self.auth_method = config.get("auth_method", "token")
        self.secret = config.get("secret", "access_secret")
        end_window_size = config.get("end_window_size")
        self.end_window_size = int(end_window_size) if end_window_size else 200

    async def open_audio_channels(self, conn):
        await super().open_audio_channels(conn)

    async def receive_audio(self, conn: "ConnectionHandler", audio, audio_have_voice):
        # Gọi phương thức lớp cha để xử lý logic cơ bản trước
        await super().receive_audio(conn, audio, audio_have_voice)
        
        # Nếu lần này có âm thanh, và trước đó chưa thiết lập kết nối
        if audio_have_voice and self.asr_ws is None and not self.is_processing:
            try:
                self.is_processing = True
                # Thiết lập kết nối WebSocket mới
                headers = self.token_auth() if self.auth_method == "token" else None
                logger.bind(tag=TAG).info(f"Đang kết nối dịch vụ ASR, headers: {headers}")

                self.asr_ws = await websockets.connect(
                    self.ws_url,
                    additional_headers=headers,
                    max_size=1000000000,
                    ping_interval=None,
                    ping_timeout=None,
                    close_timeout=10,
                )

                # Gửi yêu cầu khởi tạo
                request_params = self.construct_request(str(uuid.uuid4()))
                try:
                    payload_bytes = str.encode(json.dumps(request_params))
                    payload_bytes = gzip.compress(payload_bytes)
                    full_client_request = self.generate_header()
                    full_client_request.extend((len(payload_bytes)).to_bytes(4, "big"))
                    full_client_request.extend(payload_bytes)

                    logger.bind(tag=TAG).info(f"Gửi yêu cầu khởi tạo: {request_params}")
                    await self.asr_ws.send(full_client_request)

                    # Chờ phản hồi khởi tạo
                    init_res = await self.asr_ws.recv()
                    result = self.parse_response(init_res)
                    logger.bind(tag=TAG).info(f"Nhận phản hồi khởi tạo: {result}")

                    # Kiểm tra phản hồi khởi tạo
                    if "code" in result and result["code"] != 1000:
                        error_msg = f"Khởi tạo dịch vụ ASR thất bại: {result.get('payload_msg', {}).get('error', 'Lỗi không xác định')}"
                        logger.bind(tag=TAG).error(error_msg)
                        raise Exception(error_msg)

                except Exception as e:
                    logger.bind(tag=TAG).error(f"Gửi yêu cầu khởi tạo thất bại: {str(e)}")
                    if hasattr(e, "__cause__") and e.__cause__:
                        logger.bind(tag=TAG).error(f"Nguyên nhân lỗi: {str(e.__cause__)}")
                    raise e

                # Khởi động tác vụ bất đồng bộ nhận kết quả ASR
                self.forward_task = asyncio.create_task(self._forward_asr_results(conn))

                # Gửi dữ liệu audio đã cache
                if conn.asr_audio and len(conn.asr_audio) > 0:
                    for cached_audio in conn.asr_audio[-10:]:
                        try:
                            pcm_frame = self.decoder.decode(cached_audio, 960)
                            payload = gzip.compress(pcm_frame)
                            audio_request = bytearray(
                                self.generate_audio_default_header()
                            )
                            audio_request.extend(len(payload).to_bytes(4, "big"))
                            audio_request.extend(payload)
                            await self.asr_ws.send(audio_request)
                        except Exception as e:
                            logger.bind(tag=TAG).info(
                                f"Lỗi khi gửi dữ liệu audio đã cache: {e}"
                            )

            except Exception as e:
                logger.bind(tag=TAG).error(f"Thiết lập kết nối ASR thất bại: {str(e)}")
                if hasattr(e, "__cause__") and e.__cause__:
                    logger.bind(tag=TAG).error(f"Nguyên nhân lỗi: {str(e.__cause__)}")
                if self.asr_ws:
                    await self.asr_ws.close()
                    self.asr_ws = None
                self.is_processing = False
                return

        # Gửi dữ liệu audio hiện tại
        if self.asr_ws and self.is_processing:
            try:
                pcm_frame = self.decoder.decode(audio, 960)
                payload = gzip.compress(pcm_frame)
                audio_request = bytearray(self.generate_audio_default_header())
                audio_request.extend(len(payload).to_bytes(4, "big"))
                audio_request.extend(payload)
                await self.asr_ws.send(audio_request)
            except Exception as e:
                logger.bind(tag=TAG).info(f"Lỗi khi gửi dữ liệu audio: {e}")

    async def _forward_asr_results(self, conn: "ConnectionHandler"):
        try:
            while self.asr_ws and not conn.stop_event.is_set():
                # Lấy dữ liệu audio của kết nối hiện tại
                audio_data = conn.asr_audio
                try:
                    response = await self.asr_ws.recv()
                    result = self.parse_response(response)
                    logger.bind(tag=TAG).debug(f"Nhận kết quả ASR: {result}")

                    if "payload_msg" in result:
                        payload = result["payload_msg"]
                        # Kiểm tra có phải mã lỗi 1013 (không có giọng nói hợp lệ) không
                        if "code" in payload and payload["code"] == 1013:
                            # Xử lý im lặng, không ghi log lỗi
                            continue

                        if "result" in payload:
                            utterances = payload["result"].get("utterances", [])
                            # Kiểm tra trường hợp duration và văn bản rỗng
                            if (
                                not self.enable_multilingual  # Lưu ý: chế độ đa ngôn ngữ không trả về kết quả trung gian, cần chờ kết quả cuối cùng
                                and payload.get("audio_info", {}).get("duration", 0)
                                > 2000
                                and not utterances
                                and not payload["result"].get("text")
                                and conn.client_listen_mode != "manual"
                            ):
                                logger.bind(tag=TAG).error(f"Văn bản nhận dạng: rỗng")
                                self.text = ""
                                if len(audio_data) > 15:  # Đảm bảo có đủ dữ liệu audio
                                    await self.handle_voice_stop(conn, audio_data)
                                break

                            # Xử lý đặc biệt kết quả nhận dạng không có văn bản (trong chế độ thủ công có thể đã nhận dạng xong nhưng chưa thả phím)
                            elif not payload["result"].get("text") and not utterances:
                                # Chế độ đa ngôn ngữ sẽ tiếp tục trả về văn bản rỗng cho đến khi trả về kết quả hoàn chỉnh cuối cùng, nên cần loại trừ
                                if self.enable_multilingual:
                                    continue

                                if conn.client_listen_mode == "manual" and conn.client_voice_stop and len(audio_data) > 15:
                                    logger.bind(tag=TAG).debug("Kết thúc tin nhắn nhận tín hiệu dừng, kích hoạt xử lý")
                                    await self.handle_voice_stop(conn, audio_data)
                                    break

                            for utterance in utterances:
                                if utterance.get("definite", False):
                                    current_text = utterance["text"]
                                    logger.bind(tag=TAG).info(
                                        f"Nhận dạng được văn bản: {current_text}"
                                    )

                                    # Trong chế độ thủ công, tích lũy kết quả nhận dạng
                                    if conn.client_listen_mode == "manual":
                                        if self.text:
                                            self.text += current_text
                                        else:
                                            self.text = current_text

                                        # Nhận tín hiệu dừng khi đang nhận tin nhắn giữa chừng
                                        if conn.client_voice_stop and len(audio_data) > 0:
                                            logger.bind(tag=TAG).debug("Giữa chừng tin nhắn nhận tín hiệu dừng, kích hoạt xử lý")
                                            await self.handle_voice_stop(conn, audio_data)
                                        break
                                    else:
                                        # Trong chế độ tự động, ghi đè trực tiếp
                                        self.text = current_text
                                        if len(audio_data) > 15:  # Đảm bảo có đủ dữ liệu audio
                                            await self.handle_voice_stop(
                                                conn, audio_data
                                            )
                                    break
                        elif "error" in payload:
                            error_msg = payload.get("error", "Lỗi không xác định")
                            logger.bind(tag=TAG).error(f"Dịch vụ ASR trả về lỗi: {error_msg}")
                            break

                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).info("Kết nối dịch vụ ASR đã đóng")
                    self.is_processing = False
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(f"Lỗi khi xử lý kết quả ASR: {str(e)}")
                    if hasattr(e, "__cause__") and e.__cause__:
                        logger.bind(tag=TAG).error(f"Nguyên nhân lỗi: {str(e.__cause__)}")
                    self.is_processing = False
                    break

        except Exception as e:
            logger.bind(tag=TAG).error(f"Tác vụ chuyển tiếp kết quả ASR xảy ra lỗi: {str(e)}")
            if hasattr(e, "__cause__") and e.__cause__:
                logger.bind(tag=TAG).error(f"Nguyên nhân lỗi: {str(e.__cause__)}")
        finally:
            if self.asr_ws:
                await self.asr_ws.close()
                self.asr_ws = None
            self.is_processing = False
            # Đặt lại tất cả trạng thái liên quan đến audio
            conn.reset_audio_states()

    def stop_ws_connection(self):
        if self.asr_ws:
            asyncio.create_task(self.asr_ws.close())
            self.asr_ws = None
        self.is_processing = False

    async def _send_stop_request(self):
        """Gửi frame audio cuối cùng để thông báo server kết thúc"""
        if self.asr_ws:
            try:
                # Gửi frame audio có đánh dấu kết thúc (dữ liệu rỗng được nén gzip)
                empty_payload = gzip.compress(b"")
                last_audio_request = bytearray(
                    self.generate_last_audio_default_header()
                )
                last_audio_request.extend(len(empty_payload).to_bytes(4, "big"))
                last_audio_request.extend(empty_payload)
                await self.asr_ws.send(last_audio_request)
                logger.bind(tag=TAG).debug("Đã gửi frame audio kết thúc")
            except Exception as e:
                logger.bind(tag=TAG).debug(f"Lỗi khi gửi frame audio kết thúc: {e}")

    def construct_request(self, reqid):
        req = {
            "app": {
                "appid": self.appid,
                "cluster": self.cluster,
                "token": self.access_token,
            },
            "user": {"uid": self.uid},
            "request": {
                "reqid": reqid,
                "workflow": self.workflow,
                "show_utterances": True,
                "result_type": self.result_type,
                "sequence": 1,
                "boosting_table_name": self.boosting_table_name,
                "correct_table_name": self.correct_table_name,
                "end_window_size": self.end_window_size,
            },
            "audio": {
                "format": self.format,
                "codec": self.codec,
                "rate": self.rate,
                "bits": self.bits,
                "channel": self.channel,
                "sample_rate": self.rate,
            },
        }

        # Tham số language chỉ được thêm trong chế độ đa ngôn ngữ
        if self.enable_multilingual and self.language:
            req["audio"]["language"] = self.language

        logger.bind(tag=TAG).debug(
            f"Xây dựng tham số yêu cầu: {json.dumps(req, ensure_ascii=False)}"
        )
        return req

    def token_auth(self):
        return {
            "X-Api-App-Key": self.appid,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
            "X-Api-Connect-Id": str(uuid.uuid4()),
        }

    def generate_header(
        self,
        version=0x01,
        message_type=0x01,
        message_type_specific_flags=0x00,
        serial_method=0x01,
        compression_type=0x01,
        reserved_data=0x00,
        extension_header: bytes = b"",
    ):
        header = bytearray()
        header_size = int(len(extension_header) / 4) + 1
        header.append((version << 4) | header_size)
        header.append((message_type << 4) | message_type_specific_flags)
        header.append((serial_method << 4) | compression_type)
        header.append(reserved_data)
        header.extend(extension_header)
        return header

    def generate_audio_default_header(self):
        return self.generate_header(
            version=0x01,
            message_type=0x02,
            message_type_specific_flags=0x00,
            serial_method=0x01,
            compression_type=0x01,
        )

    def generate_last_audio_default_header(self):
        return self.generate_header(
            version=0x01,
            message_type=0x02,
            message_type_specific_flags=0x02,
            serial_method=0x01,
            compression_type=0x01,
        )

    def parse_response(self, res: bytes) -> dict:
        try:
            # Kiểm tra độ dài phản hồi
            if len(res) < 4:
                logger.bind(tag=TAG).error(f"Độ dài dữ liệu phản hồi không đủ: {len(res)}")
                return {"error": "Độ dài dữ liệu phản hồi không đủ"}

            # Lấy header tin nhắn
            header = res[:4]
            message_type = header[1] >> 4

            # Nếu là phản hồi lỗi
            if message_type == 0x0F:  # SERVER_ERROR_RESPONSE
                code = int.from_bytes(res[4:8], "big", signed=False)
                msg_length = int.from_bytes(res[8:12], "big", signed=False)
                error_msg = json.loads(res[12:].decode("utf-8"))
                return {
                    "code": code,
                    "msg_length": msg_length,
                    "payload_msg": error_msg,
                }

            # Lấy dữ liệu JSON (bỏ qua 12 byte header)
            try:
                json_data = res[12:].decode("utf-8")
                result = json.loads(json_data)
                logger.bind(tag=TAG).debug(f"Phân tích JSON phản hồi thành công: {result}")
                return {"payload_msg": result}
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.bind(tag=TAG).error(f"Phân tích JSON thất bại: {str(e)}")
                logger.bind(tag=TAG).error(f"Dữ liệu gốc: {res}")
                raise

        except Exception as e:
            logger.bind(tag=TAG).error(f"Phân tích phản hồi thất bại: {str(e)}")
            logger.bind(tag=TAG).error(f"Dữ liệu phản hồi gốc: {res.hex()}")
            raise

    async def speech_to_text(self, opus_data, session_id, audio_format, artifacts=None):
        result = self.text
        self.text = ""  # Xóa text
        return result, None

    async def close(self):
        """Phương thức dọn dẹp tài nguyên"""
        if self.asr_ws:
            await self.asr_ws.close()
            self.asr_ws = None
        if self.forward_task:
            self.forward_task.cancel()
            try:
                await self.forward_task
            except asyncio.CancelledError:
                pass
            self.forward_task = None
        self.is_processing = False

        # Giải phóng tài nguyên decoder một cách rõ ràng
        if hasattr(self, "decoder") and self.decoder is not None:
            try:
                del self.decoder
                self.decoder = None
                logger.bind(tag=TAG).debug("Doubao decoder resources released")
            except Exception as e:
                logger.bind(tag=TAG).debug(f"Lỗi khi giải phóng tài nguyên decoder Doubao: {e}")
