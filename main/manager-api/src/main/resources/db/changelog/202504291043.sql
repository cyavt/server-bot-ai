-- Thêm nhà cung cấp và cấu hình mô hình nhận dạng giọng nói dịch vụ FunASR
DELETE FROM `ai_model_provider` WHERE `id` = 'SYSTEM_ASR_FunASRServer';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_FunASRServer', 'ASR', 'fun_server', 'Nhận dạng giọng nói dịch vụ FunASR', '[{"key":"host","label":"Địa chỉ dịch vụ","type":"string"},{"key":"port","label":"Số cổng","type":"number"}]', 4, 1, NOW(), 1, NOW());

DELETE FROM `ai_model_config` WHERE `id` = 'ASR_FunASRServer';
INSERT INTO `ai_model_config` VALUES ('ASR_FunASRServer', 'ASR', 'FunASRServer', 'Nhận dạng giọng nói dịch vụ FunASR', 0, 1, '{\"type\": \"fun_server\", \"host\": \"127.0.0.1\", \"port\": 10096}', NULL, NULL, 5, NULL, NULL, NULL, NULL);

-- Sửa đổi kiểu trường remark của bảng ai_model_config thành TEXT
ALTER TABLE `ai_model_config` MODIFY COLUMN `remark` TEXT COMMENT 'Ghi chú'; 

-- Cập nhật tài liệu hướng dẫn cấu hình mô hình ASR
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md',
`remark` = 'Triển khai FunASR độc lập, sử dụng dịch vụ API của FunASR, chỉ cần năm câu lệnh
Câu thứ nhất: mkdir -p ./funasr-runtime-resources/models
Câu thứ hai: sudo docker run -d -p 10096:10095 --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
Sau khi thực hiện câu lệnh trên sẽ vào container, tiếp tục câu thứ ba: cd FunASR/runtime
Không thoát container, tiếp tục thực hiện câu thứ tư trong container: nohup bash run_server_2pass.sh --download-model-dir /workspace/models --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst --itn-dir thuduj12/fst_itn_zh --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
Sau khi thực hiện câu lệnh trên sẽ vào container, tiếp tục câu thứ năm: tail -f log.txt
Sau khi thực hiện xong câu lệnh thứ năm, bạn sẽ thấy nhật ký tải xuống mô hình, sau khi tải xuống xong là có thể kết nối và sử dụng
Trên đây là sử dụng suy luận CPU, nếu có GPU, tham khảo chi tiết: https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md' WHERE `id` = 'ASR_FunASRServer';

-- Cập nhật hướng dẫn cấu hình mô hình FunASR cục bộ
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/modelscope/FunASR',
`remark` = 'Hướng dẫn cấu hình mô hình FunASR cục bộ:
1. Cần tải xuống file mô hình vào thư mục xiaozhi-server/models/SenseVoiceSmall
2. Hỗ trợ nhận dạng giọng nói tiếng Trung, Nhật, Hàn, Quảng Đông
3. Suy luận cục bộ, không cần kết nối mạng
4. File cần nhận dạng được lưu trong thư mục tmp/' WHERE `id` = 'ASR_FunASR';

-- Cập nhật hướng dẫn cấu hình SherpaASR
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/k2-fsa/sherpa-onnx',
`remark` = 'Hướng dẫn cấu hình SherpaASR:
1. Tự động tải xuống file mô hình vào thư mục models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17 khi chạy
2. Hỗ trợ nhiều ngôn ngữ như tiếng Trung, tiếng Anh, tiếng Nhật, tiếng Hàn, tiếng Quảng Đông
3. Suy luận cục bộ, không cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/' WHERE `id` = 'ASR_SherpaASR';

-- Cập nhật hướng dẫn cấu hình ASR Đậu Bao
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = 'Hướng dẫn cấu hình ASR Đậu Bao:
1. Cần tạo ứng dụng trên bảng điều khiển Huoshan Engine và lấy appid và access_token
2. Hỗ trợ nhận dạng giọng nói tiếng Trung
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://console.volcengine.com/speech/app
2. Tạo ứng dụng mới
3. Lấy appid và access_token
4. Điền vào file cấu hình' WHERE `id` = 'ASR_DoubaoASR';

-- Cập nhật hướng dẫn cấu hình ASR Tencent
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.cloud.tencent.com/cam/capi',
`remark` = 'Hướng dẫn cấu hình ASR Tencent:
1. Cần tạo ứng dụng trên bảng điều khiển Tencent Cloud và lấy appid, secret_id và secret_key
2. Hỗ trợ nhận dạng giọng nói tiếng Trung
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://console.cloud.tencent.com/cam/capi để lấy khóa
2. Truy cập https://console.cloud.tencent.com/asr/resourcebundle để nhận tài nguyên miễn phí
3. Lấy appid, secret_id và secret_key
4. Điền vào file cấu hình' WHERE `id` = 'ASR_TencentASR';

-- Cập nhật hướng dẫn cấu hình mô hình TTS
-- Hướng dẫn cấu hình EdgeTTS
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/rany2/edge-tts',
`remark` = 'Hướng dẫn cấu hình EdgeTTS:
1. Sử dụng dịch vụ Edge TTS của Microsoft
2. Hỗ trợ nhiều ngôn ngữ và giọng nói
3. Miễn phí sử dụng, không cần đăng ký
4. Cần kết nối mạng
5. File đầu ra được lưu trong thư mục tmp/' WHERE `id` = 'TTS_EdgeTTS';

-- Hướng dẫn cấu hình TTS Đậu Bao
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/service/8',
`remark` = 'Hướng dẫn cấu hình TTS Đậu Bao:
1. Truy cập https://console.volcengine.com/speech/service/8
2. Cần tạo ứng dụng trên bảng điều khiển Huoshan Engine và lấy appid và access_token
3. Dịch vụ giọng nói Huoshan Engine nhất định phải mua trả phí, giá khởi điểm 30 nhân dân tệ, có 100 đồng thời. Nếu dùng miễn phí chỉ có 2 đồng thời, sẽ thường xuyên báo lỗi tts
4. Sau khi mua dịch vụ, mua giọng miễn phí, có thể phải đợi khoảng nửa giờ mới có thể sử dụng.
5. Điền vào file cấu hình' WHERE `id` = 'TTS_DoubaoTTS';

-- Hướng dẫn cấu hình TTS Siliconflow
UPDATE `ai_model_config` SET 
`doc_link` = 'https://cloud.siliconflow.cn/account/ak',
`remark` = 'Hướng dẫn cấu hình TTS Siliconflow:
1. Truy cập https://cloud.siliconflow.cn/account/ak
2. Đăng ký và lấy khóa API
3. Điền vào file cấu hình' WHERE `id` = 'TTS_CosyVoiceSiliconflow';

-- Hướng dẫn cấu hình TTS Coze tiếng Trung
UPDATE `ai_model_config` SET 
`doc_link` = 'https://www.coze.cn/open/oauth/pats',
`remark` = 'Hướng dẫn cấu hình TTS Coze tiếng Trung:
1. Truy cập https://www.coze.cn/open/oauth/pats
2. Lấy mã thông báo cá nhân
3. Điền vào file cấu hình' WHERE `id` = 'TTS_CozeCnTTS';

-- Hướng dẫn cấu hình FishSpeech
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/fishaudio/fish-speech',
`remark` = 'Hướng dẫn cấu hình FishSpeech:
1. Cần triển khai dịch vụ FishSpeech cục bộ
2. Hỗ trợ giọng nói tùy chỉnh
3. Suy luận cục bộ, không cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
5. Lệnh ví dụ chạy dịch vụ: python -m tools.api_server --listen 0.0.0.0:8080 --llama-checkpoint-path "checkpoints/fish-speech-1.5" --decoder-checkpoint-path "checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth" --decoder-config-name firefly_gan_vq --compile' WHERE `id` = 'TTS_FishSpeech';

-- Hướng dẫn cấu hình GPT-SoVITS V2
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/RVC-Boss/GPT-SoVITS',
`remark` = 'Hướng dẫn cấu hình GPT-SoVITS V2:
1. Cần triển khai dịch vụ GPT-SoVITS cục bộ
2. Hỗ trợ sao chép giọng nói tùy chỉnh
3. Suy luận cục bộ, không cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước triển khai:
1. Lệnh ví dụ chạy dịch vụ: python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/demo.yaml' WHERE `id` = 'TTS_GPT_SOVITS_V2';

-- Hướng dẫn cấu hình GPT-SoVITS V3
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/RVC-Boss/GPT-SoVITS',
`remark` = 'Hướng dẫn cấu hình GPT-SoVITS V3:
1. Cần triển khai dịch vụ GPT-SoVITS V3 cục bộ
2. Hỗ trợ sao chép giọng nói tùy chỉnh
3. Suy luận cục bộ, không cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/' WHERE `id` = 'TTS_GPT_SOVITS_V3';

-- Hướng dẫn cấu hình TTS MiniMax
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.minimaxi.com/',
`remark` = 'Hướng dẫn cấu hình TTS MiniMax:
1. Cần tạo tài khoản trên nền tảng MiniMax và nạp tiền
2. Hỗ trợ nhiều giọng nói, cấu hình hiện tại sử dụng female-shaonv
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://platform.minimaxi.com/ để đăng ký tài khoản
2. Truy cập https://platform.minimaxi.com/user-center/payment/balance để nạp tiền
3. Truy cập https://platform.minimaxi.com/user-center/basic-information để lấy group_id
4. Truy cập https://platform.minimaxi.com/user-center/basic-information/interface-key để lấy api_key
5. Điền vào file cấu hình' WHERE `id` = 'TTS_MinimaxTTS';

-- Hướng dẫn cấu hình TTS Alibaba Cloud
UPDATE `ai_model_config` SET 
`doc_link` = 'https://nls-portal.console.aliyun.com/',
`remark` = 'Hướng dẫn cấu hình TTS Alibaba Cloud:
1. Cần kích hoạt dịch vụ tương tác giọng nói thông minh trên nền tảng Alibaba Cloud
2. Hỗ trợ nhiều giọng nói, cấu hình hiện tại sử dụng xiaoyun
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://nls-portal.console.aliyun.com/ để kích hoạt dịch vụ
2. Truy cập https://nls-portal.console.aliyun.com/applist để lấy appkey
3. Truy cập https://nls-portal.console.aliyun.com/overview để lấy token
4. Điền vào file cấu hình
Lưu ý: token là tạm thời, có hiệu lực 24 giờ, sử dụng lâu dài cần cấu hình access_key_id và access_key_secret' WHERE `id` = 'TTS_AliyunTTS';

-- Hướng dẫn cấu hình TTS Tencent
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.cloud.tencent.com/cam/capi',
`remark` = 'Hướng dẫn cấu hình TTS Tencent:
1. Cần kích hoạt dịch vụ tương tác giọng nói thông minh trên nền tảng Tencent Cloud
2. Hỗ trợ nhiều giọng nói, cấu hình hiện tại sử dụng 101001
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://console.cloud.tencent.com/cam/capi để lấy khóa
2. Truy cập https://console.cloud.tencent.com/tts/resourcebundle để nhận tài nguyên miễn phí
3. Tạo ứng dụng mới
4. Lấy appid, secret_id và secret_key
5. Điền vào file cấu hình' WHERE `id` = 'TTS_TencentTTS';

-- Hướng dẫn cấu hình TTS 302AI
UPDATE `ai_model_config` SET 
`doc_link` = 'https://dash.302.ai/',
`remark` = 'Hướng dẫn cấu hình TTS 302AI:
1. Cần tạo tài khoản trên nền tảng 302 và lấy khóa API
2. Hỗ trợ nhiều giọng nói, cấu hình hiện tại sử dụng giọng Tiểu Hà
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://dash.302.ai/ để đăng ký tài khoản
2. Truy cập https://dash.302.ai/apis/list để lấy khóa API
3. Điền vào file cấu hình
Giá: $35/triệu ký tự' WHERE `id` = 'TTS_TTS302AI';

-- Hướng dẫn cấu hình TTS Gizwits
UPDATE `ai_model_config` SET 
`doc_link` = 'https://agentrouter.gizwitsapi.com/panel/token',
`remark` = 'Hướng dẫn cấu hình TTS Gizwits:
1. Cần lấy khóa API trên nền tảng Gizwits
2. Hỗ trợ nhiều giọng nói, cấu hình hiện tại sử dụng giọng Tiểu Hà
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://agentrouter.gizwitsapi.com/panel/token để lấy khóa API
2. Điền vào file cấu hình
Lưu ý: Mười nghìn người dùng đăng ký đầu tiên sẽ được tặng 5 nhân dân tệ để trải nghiệm' WHERE `id` = 'TTS_GizwitsTTS';

-- Hướng dẫn cấu hình TTS ACGN
UPDATE `ai_model_config` SET 
`doc_link` = 'https://acgn.ttson.cn/',
`remark` = 'Hướng dẫn cấu hình TTS ACGN:
1. Cần mua token trên nền tảng ttson
2. Hỗ trợ nhiều giọng nói nhân vật, cấu hình hiện tại sử dụng ID nhân vật: 1695
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://acgn.ttson.cn/ để xem danh sách nhân vật
2. Truy cập www.ttson.cn để mua token
3. Điền vào file cấu hình
Câu hỏi liên quan đến phát triển vui lòng gửi đến qq trên trang web' WHERE `id` = 'TTS_ACGNTTS';

-- Hướng dẫn cấu hình TTS OpenAI
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.openai.com/api-keys',
`remark` = 'Hướng dẫn cấu hình TTS OpenAI:
1. Cần lấy khóa API trên nền tảng OpenAI
2. Hỗ trợ nhiều giọng nói, cấu hình hiện tại sử dụng onyx
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Các bước đăng ký:
1. Truy cập https://platform.openai.com/api-keys để lấy khóa API
2. Điền vào file cấu hình
Lưu ý: Trong nước cần sử dụng proxy để truy cập' WHERE `id` = 'TTS_OpenAITTS';

-- Hướng dẫn cấu hình TTS tùy chỉnh
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Hướng dẫn cấu hình TTS tùy chỉnh:
1. Hỗ trợ dịch vụ giao diện TTS tùy chỉnh
2. Sử dụng phương thức GET để yêu cầu
3. Cần kết nối mạng
4. File đầu ra được lưu trong thư mục tmp/
Hướng dẫn cấu hình:
1. Cấu hình tham số yêu cầu trong params
2. Cấu hình tiêu đề yêu cầu trong headers
3. Đặt định dạng âm thanh trả về' WHERE `id` = 'TTS_CustomTTS';

-- Hướng dẫn cấu hình TTS cổng mô hình lớn biên Huoshan Engine
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/vei/aigateway/',
`remark` = 'Hướng dẫn cấu hình TTS cổng mô hình lớn biên Huoshan Engine:
1. Truy cập https://console.volcengine.com/vei/aigateway/
2. Tạo khóa truy cập cổng, tìm kiếm và chọn Doubao-语音合成
3. Nếu cần sử dụng LLM, đồng thời chọn Doubao-pro-32k-functioncall
4. Truy cập https://console.volcengine.com/vei/aigateway/tokens-list để lấy khóa
5. Điền vào file cấu hình
Tham khảo danh sách giọng nói: https://www.volcengine.com/docs/6561/1257544' WHERE `id` = 'TTS_VolcesAiGatewayTTS';

-- Cập nhật hướng dẫn cấu hình mô hình LLM
-- Hướng dẫn cấu hình ChatGLM
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys',
`remark` = 'Hướng dẫn cấu hình ChatGLM:
1. Truy cập https://bigmodel.cn/usercenter/proj-mgmt/apikeys
2. Đăng ký và lấy khóa API
3. Điền vào file cấu hình' WHERE `id` = 'LLM_ChatGLMLLM';

-- Hướng dẫn cấu hình Ollama
UPDATE `ai_model_config` SET 
`doc_link` = 'https://ollama.com/',
`remark` = 'Hướng dẫn cấu hình Ollama:
1. Cài đặt dịch vụ Ollama
2. Chạy lệnh: ollama pull qwen2.5
3. Đảm bảo dịch vụ chạy trên http://localhost:11434' WHERE `id` = 'LLM_OllamaLLM';

-- Hướng dẫn cấu hình Tongyi Qianwen
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
`remark` = 'Hướng dẫn cấu hình Tongyi Qianwen:
1. Truy cập https://bailian.console.aliyun.com/?apiKey=1#/api-key
2. Lấy khóa API
3. Điền vào file cấu hình, cấu hình hiện tại sử dụng mô hình qwen-turbo
4. Hỗ trợ tham số tùy chỉnh: temperature=0.7, max_tokens=500, top_p=1, top_k=50' WHERE `id` = 'LLM_AliLLM';

-- Hướng dẫn cấu hình Tongyi Bailian
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
`remark` = 'Hướng dẫn cấu hình Tongyi Bailian:
1. Truy cập https://bailian.console.aliyun.com/?apiKey=1#/api-key
2. Lấy app_id và api_key
3. Điền vào file cấu hình' WHERE `id` = 'LLM_AliAppLLM';

-- Hướng dẫn cấu hình mô hình lớn Đậu Bao
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement',
`remark` = 'Hướng dẫn cấu hình mô hình lớn Đậu Bao:
1. Truy cập https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement
2. Kích hoạt dịch vụ Doubao-1.5-pro
3. Truy cập https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey để lấy khóa API
4. Điền vào file cấu hình
5. Hiện tại khuyến nghị sử dụng doubao-1-5-pro-32k-250115
Lưu ý: Có hạn mức miễn phí 500000 token' WHERE `id` = 'LLM_DoubaoLLM';

-- Hướng dẫn cấu hình DeepSeek
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.deepseek.com/',
`remark` = 'Hướng dẫn cấu hình DeepSeek:
1. Truy cập https://platform.deepseek.com/
2. Đăng ký và lấy khóa API
3. Điền vào file cấu hình' WHERE `id` = 'LLM_DeepSeekLLM';

-- Hướng dẫn cấu hình Dify
UPDATE `ai_model_config` SET 
`doc_link` = 'https://cloud.dify.ai/',
`remark` = 'Hướng dẫn cấu hình Dify:
1. Truy cập https://cloud.dify.ai/
2. Đăng ký và lấy khóa API
3. Điền vào file cấu hình
4. Hỗ trợ nhiều chế độ đối thoại: workflows/run, chat-messages, completion-messages
5. Định nghĩa vai trò được đặt trên nền tảng sẽ không có hiệu lực, cần đặt trong bảng điều khiển Dify
Lưu ý: Khuyến nghị sử dụng giao diện Dify triển khai cục bộ, một số khu vực trong nước truy cập giao diện đám mây công cộng có thể bị hạn chế' WHERE `id` = 'LLM_DifyLLM';

-- Hướng dẫn cấu hình Gemini
UPDATE `ai_model_config` SET 
`doc_link` = 'https://aistudio.google.com/apikey',
`remark` = 'Hướng dẫn cấu hình Gemini:
1. Sử dụng dịch vụ API Gemini của Google
2. Cấu hình hiện tại sử dụng mô hình gemini-2.0-flash
3. Cần kết nối mạng
4. Hỗ trợ cấu hình proxy
Các bước đăng ký:
1. Truy cập https://aistudio.google.com/apikey
2. Tạo khóa API
3. Điền vào file cấu hình
Lưu ý: Nếu sử dụng trong lãnh thổ Trung Quốc, vui lòng tuân thủ "Biện pháp quản lý tạm thời dịch vụ trí tuệ nhân tạo tạo sinh"' WHERE `id` = 'LLM_GeminiLLM';

-- Hướng dẫn cấu hình Coze
UPDATE `ai_model_config` SET 
`doc_link` = 'https://www.coze.cn/open/oauth/pats',
`remark` = 'Hướng dẫn cấu hình Coze:
1. Sử dụng dịch vụ nền tảng Coze
2. Cần bot_id, user_id và mã thông báo cá nhân
3. Cần kết nối mạng
Các bước đăng ký:
1. Truy cập https://www.coze.cn/open/oauth/pats
2. Lấy mã thông báo cá nhân
3. Tính toán thủ công bot_id và user_id
4. Điền vào file cấu hình' WHERE `id` = 'LLM_CozeLLM';

-- Hướng dẫn cấu hình LM Studio
UPDATE `ai_model_config` SET 
`doc_link` = 'https://lmstudio.ai/',
`remark` = 'Hướng dẫn cấu hình LM Studio:
1. Sử dụng dịch vụ LM Studio triển khai cục bộ
2. Cấu hình hiện tại sử dụng mô hình deepseek-r1-distill-llama-8b@q4_k_m
3. Suy luận cục bộ, không cần kết nối mạng
4. Cần tải xuống mô hình trước
Các bước triển khai:
1. Cài đặt LM Studio
2. Tải xuống mô hình từ cộng đồng
3. Đảm bảo dịch vụ chạy trên http://localhost:1234/v1' WHERE `id` = 'LLM_LMStudioLLM';

-- Hướng dẫn cấu hình FastGPT
UPDATE `ai_model_config` SET 
`doc_link` = 'https://cloud.tryfastgpt.ai/account/apikey',
`remark` = 'Hướng dẫn cấu hình FastGPT:
1. Sử dụng dịch vụ nền tảng FastGPT
2. Cần kết nối mạng
3. prompt trong file cấu hình không có hiệu lực, cần đặt trong bảng điều khiển FastGPT
4. Hỗ trợ biến tùy chỉnh
Các bước đăng ký:
1. Truy cập https://cloud.tryfastgpt.ai/account/apikey
2. Lấy khóa API
3. Điền vào file cấu hình' WHERE `id` = 'LLM_FastgptLLM';

-- Hướng dẫn cấu hình Xinference
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xorbitsai/inference',
`remark` = 'Hướng dẫn cấu hình Xinference:
1. Sử dụng dịch vụ Xinference triển khai cục bộ
2. Cấu hình hiện tại sử dụng mô hình qwen2.5:72b-AWQ
3. Suy luận cục bộ, không cần kết nối mạng
4. Cần khởi động mô hình tương ứng trước
Các bước triển khai:
1. Cài đặt Xinference
2. Khởi động dịch vụ và tải mô hình
3. Đảm bảo dịch vụ chạy trên http://localhost:9997' WHERE `id` = 'LLM_XinferenceLLM';

-- Hướng dẫn cấu hình mô hình nhỏ Xinference
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xorbitsai/inference',
`remark` = 'Hướng dẫn cấu hình mô hình nhỏ Xinference:
1. Sử dụng dịch vụ Xinference triển khai cục bộ
2. Cấu hình hiện tại sử dụng mô hình qwen2.5:3b-AWQ
3. Suy luận cục bộ, không cần kết nối mạng
4. Dùng cho nhận dạng ý định
Các bước triển khai:
1. Cài đặt Xinference
2. Khởi động dịch vụ và tải mô hình
3. Đảm bảo dịch vụ chạy trên http://localhost:9997' WHERE `id` = 'LLM_XinferenceSmallLLM';

-- Hướng dẫn cấu hình LLM cổng mô hình lớn biên Huoshan Engine
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/vei/aigateway/',
`remark` = 'Hướng dẫn cấu hình LLM cổng mô hình lớn biên Huoshan Engine:
1. Sử dụng dịch vụ cổng mô hình lớn biên Huoshan Engine
2. Cần khóa truy cập cổng
3. Cần kết nối mạng
4. Hỗ trợ chức năng function_call
Các bước đăng ký:
1. Truy cập https://console.volcengine.com/vei/aigateway/
2. Tạo khóa truy cập cổng, tìm kiếm và chọn Doubao-pro-32k-functioncall
3. Nếu cần sử dụng tổng hợp giọng nói, đồng thời chọn Doubao-语音合成
4. Truy cập https://console.volcengine.com/vei/aigateway/tokens-list để lấy khóa
5. Điền vào file cấu hình' WHERE `id` = 'LLM_VolcesAiGatewayLLM';

-- Cập nhật hướng dẫn cấu hình mô hình Memory
-- Hướng dẫn cấu hình không có bộ nhớ
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Hướng dẫn cấu hình không có bộ nhớ:
1. Không lưu lịch sử đối thoại
2. Mỗi cuộc đối thoại đều độc lập
3. Không cần cấu hình thêm
4. Phù hợp với các kịch bản yêu cầu quyền riêng tư cao' WHERE `id` = 'Memory_nomem';

-- Hướng dẫn cấu hình bộ nhớ ngắn hạn cục bộ
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Hướng dẫn cấu hình bộ nhớ ngắn hạn cục bộ:
1. Sử dụng lưu trữ cục bộ để lưu lịch sử đối thoại
2. Tóm tắt nội dung đối thoại thông qua llm của selected_module
3. Dữ liệu được lưu cục bộ, không tải lên máy chủ
4. Phù hợp với các kịch bản chú trọng quyền riêng tư
5. Không cần cấu hình thêm' WHERE `id` = 'Memory_mem_local_short';

-- Hướng dẫn cấu hình bộ nhớ Mem0AI
UPDATE `ai_model_config` SET 
`doc_link` = 'https://app.mem0.ai/dashboard/api-keys',
`remark` = 'Hướng dẫn cấu hình bộ nhớ Mem0AI:
1. Sử dụng dịch vụ Mem0AI để lưu lịch sử đối thoại
2. Cần khóa API
3. Cần kết nối mạng
4. Mỗi tháng có 1000 lần gọi miễn phí
Các bước đăng ký:
1. Truy cập https://app.mem0.ai/dashboard/api-keys
2. Lấy khóa API
3. Điền vào file cấu hình' WHERE `id` = 'Memory_mem0ai';

-- Cập nhật hướng dẫn cấu hình mô hình Intent
-- Hướng dẫn cấu hình không nhận dạng ý định
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Hướng dẫn cấu hình không nhận dạng ý định:
1. Không thực hiện nhận dạng ý định
2. Tất cả đối thoại đều được chuyển trực tiếp cho LLM xử lý
3. Không cần cấu hình thêm
4. Phù hợp với các kịch bản đối thoại đơn giản' WHERE `id` = 'Intent_nointent';

-- Hướng dẫn cấu hình nhận dạng ý định LLM
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Hướng dẫn cấu hình nhận dạng ý định LLM:
1. Sử dụng LLM độc lập để nhận dạng ý định
2. Mặc định sử dụng mô hình của selected_module.LLM
3. Có thể cấu hình sử dụng LLM độc lập (như ChatGLMLLM miễn phí)
4. Tính phổ biến cao, nhưng sẽ tăng thời gian xử lý
5. Không hỗ trợ các thao tác iot như điều khiển âm lượng
Hướng dẫn cấu hình:
1. Chỉ định mô hình LLM sử dụng trong trường llm
2. Nếu không chỉ định, sẽ sử dụng mô hình của selected_module.LLM' WHERE `id` = 'Intent_intent_llm';

-- Hướng dẫn cấu hình nhận dạng ý định gọi hàm
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Hướng dẫn cấu hình nhận dạng ý định gọi hàm:
1. Sử dụng chức năng function_call của LLM để nhận dạng ý định
2. Cần LLM đã chọn hỗ trợ function_call
3. Gọi công cụ theo nhu cầu, tốc độ xử lý nhanh
4. Hỗ trợ tất cả lệnh iot
5. Mặc định đã tải các chức năng sau:
   - handle_exit_intent (Thoát nhận dạng)
   - play_music (Phát nhạc)
   - change_role (Chuyển vai trò)
   - get_weather (Truy vấn thời tiết)
   - get_news (Truy vấn tin tức)
Hướng dẫn cấu hình:
1. Cấu hình mô-đun chức năng cần tải trong trường functions
2. Hệ thống mặc định đã tải chức năng cơ bản, không cần cấu hình lặp lại
3. Có thể thêm mô-đun chức năng tùy chỉnh' WHERE `id` = 'Intent_function_call';

-- Cập nhật hướng dẫn cấu hình mô hình VAD
-- Hướng dẫn cấu hình SileroVAD
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/snakers4/silero-vad',
`remark` = 'Hướng dẫn cấu hình SileroVAD:
1. Sử dụng mô hình SileroVAD để phát hiện hoạt động giọng nói
2. Suy luận cục bộ, không cần kết nối mạng
3. Cần tải xuống file mô hình vào thư mục models/snakers4_silero-vad
4. Tham số có thể cấu hình:
   - threshold: 0.5 (Ngưỡng phát hiện giọng nói)
   - min_silence_duration_ms: 700 (Thời lượng im lặng tối thiểu, đơn vị mili giây)
5. Nếu khoảng dừng khi nói tương đối dài, có thể tăng giá trị min_silence_duration_ms một cách thích hợp' WHERE `id` = 'VAD_SileroVAD';
