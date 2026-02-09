import os
import uuid
import requests
from config.logger import setup_logging
from datetime import datetime
from core.providers.tts.base import TTSProviderBase

TAG = __name__
logger = setup_logging()

class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        # Lấy trực tiếp các key từ DB config
        self.api_key = config.get("api_key")
        self.voice_id = config.get("voice_id")
        self.model = config.get("model", "ssfm-v30")
        self.url = config.get("url", "https://api.typecast.ai/v1/text-to-speech") 
        self.audio_file_type = config.get("format", "wav")
        self.output_file = config.get("output_dir", "tmp/")

    def generate_filename(self):
        return os.path.join(self.output_file, f"tts-{datetime.now().date()}@{uuid.uuid4().hex}.{self.audio_file_type}")

    async def text_to_speak(self, text, output_file):
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key
        }
        
        payload = {
            "text": text,
            "model": self.model,
            "voice_id": self.voice_id
        }

        try:
            logger.bind(tag=TAG).info(f"Typecast Request: {self.url} | Voice: {self.voice_id} | Model: {self.model}")
            resp = requests.post(self.url, json=payload, headers=headers)
            
            if resp.status_code == 200:
                content = resp.content
                if output_file:
                    with open(output_file, "wb") as file:
                        file.write(content)
                else:
                    return content
            else:
                error_msg = f"Typecast TTS Request Failed: {resp.status_code} - {resp.text}"
                logger.bind(tag=TAG).error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.bind(tag=TAG).error(f"Typecast TTS Error: {e}")
            raise e