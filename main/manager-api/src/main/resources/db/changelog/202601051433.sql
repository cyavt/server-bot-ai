-- Thay đổi mô hình trong tài liệu hướng dẫn FunASRServer thành SenseVoiceSmall
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md',
`remark` = 'Triển khai độc lập FunASR, sử dụng dịch vụ API của FunASR, chỉ cần năm câu lệnh
Câu lệnh đầu tiên: mkdir -p ./funasr-runtime-resources/models
Câu lệnh thứ hai: sudo docker run -d -p 10096:10095 --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
Sau khi câu lệnh trên thực thi sẽ vào container, tiếp tục câu lệnh thứ ba: cd FunASR/runtime
Không thoát container, tiếp tục thực thi câu lệnh thứ tư trong container: nohup bash run_server_2pass.sh --download-model-dir /workspace/models --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx --model-dir iic/SenseVoiceSmall-onnx  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst --itn-dir thuduj12/fst_itn_zh --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
Sau khi câu lệnh trên thực thi sẽ vào container, tiếp tục câu lệnh thứ năm: tail -f log.txt
Sau khi câu lệnh thứ năm thực thi xong, sẽ thấy nhật ký tải mô hình, sau khi tải xong có thể kết nối sử dụng
Trên đây là sử dụng CPU để suy luận, nếu có GPU, tham khảo chi tiết: https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md' WHERE `id` = 'ASR_FunASRServer';