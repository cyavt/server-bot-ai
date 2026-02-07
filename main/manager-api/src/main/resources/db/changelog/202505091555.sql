-- Cập nhật bảng provider mô hình
UPDATE `ai_model_provider` SET fields = '[{"key": "host", "type": "string", "label": "Địa chỉ dịch vụ"}, {"key": "port", "type": "number", "label": "Số cổng"}, {"key": "type", "type": "string", "label": "Loại dịch vụ"}, {"key": "is_ssl", "type": "boolean", "label": "Có sử dụng SSL không"}, {"key": "api_key", "type": "string", "label": "Khóa API"}, {"key": "output_dir", "type": "string", "label": "Thư mục đầu ra"}]' WHERE id = 'SYSTEM_ASR_FunASRServer';

-- Cập nhật bảng cấu hình mô hình
UPDATE `ai_model_config` SET 
config_json = '{"host": "127.0.0.1", "port": 10096, "type": "fun_server", "is_ssl": true, "api_key": "none", "output_dir": "tmp/"}',
`doc_link` = 'https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md',
`remark` = 'Triển khai FunASR độc lập, sử dụng dịch vụ API của FunASR, chỉ cần năm câu lệnh
Câu thứ nhất：mkdir -p ./funasr-runtime-resources/models
Câu thứ hai：sudo docker run -p 10096:10095 -it --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
Sau khi thực hiện câu lệnh trên sẽ vào container, tiếp tục câu thứ ba：cd FunASR/runtime
Không thoát container, tiếp tục thực hiện câu thứ tư trong container：nohup bash run_server_2pass.sh --download-model-dir /workspace/models --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst --itn-dir thuduj12/fst_itn_zh --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
Sau khi thực hiện câu lệnh trên sẽ vào container, tiếp tục câu thứ năm：tail -f log.txt
Sau khi thực hiện xong câu lệnh thứ năm, bạn sẽ thấy nhật ký tải xuống mô hình, sau khi tải xuống xong là có thể kết nối và sử dụng
Trên đây là sử dụng suy luận CPU, nếu có GPU, tham khảo chi tiết：https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md' WHERE `id` = 'ASR_FunASRServer';

-- Hướng dẫn cấu hình FishSpeech
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/fish-speech-integration.md',
`remark` = 'Hướng dẫn cấu hình FishSpeech：
1. Cần triển khai dịch vụ FishSpeech local
2. Hỗ trợ giọng tùy chỉnh
3. Suy luận local, không cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
5. Có thể tham khảo hướng dẫn https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/fish-speech-integration.md' WHERE `id` = 'TTS_FishSpeech';
