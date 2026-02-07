UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/infiniflow/ragflow/blob/main/README_zh.md',
`remark` = 'Tham khảo hướng dẫn triển khai chi tiết：https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/ragflow-integration.md
Sau khi triển khai thành công, đăng ký đăng nhập, nhấp vào avatar ở góc trên bên phải để lấy API KEY và địa chỉ máy chủ API của RAGFlow. Trước khi sử dụng RAGFlow, vui lòng thêm mô hình và thiết lập mô hình mặc định trong Model Provider。' WHERE `id` = 'RAG_RAGFlow';

update `ai_model_config` set `model_name` = 'Nhận dạng ý định mô hình lớn ngoài' where `id` = 'Intent_intent_llm';
update `ai_model_config` set `model_name` = 'Gọi hàm tự chủ mô hình lớn' where `id` = 'Intent_function_call';
update `ai_model_config` set `model_name` = 'Ứng dụng agent thông minh Bách Luyện' where `id` = 'LLM_AliAppLLM';

update `ai_model_provider` set `name` = 'Nhận dạng ý định mô hình lớn ngoài' , `fields` =  '[{"key":"llm","label":"Mô hình LLM được tham chiếu","type":"string"}]' where  id = 'SYSTEM_Intent_intent_llm';
update `ai_model_provider` set `name` = 'Gọi hàm tự chủ mô hình lớn' where  id = 'SYSTEM_Intent_function_call';

UPDATE ai_model_config set model_name = 'Linkerai (streaming)' where id = 'TTS_LinkeraiTTS';
UPDATE ai_model_config set model_name = 'Núi Lửa (streaming)' where id = 'TTS_HuoshanDoubleStreamTTS';
UPDATE ai_model_config set model_name = 'Alibaba Bách Luyện (streaming)' where id = 'TTS_AliBLStreamTTS';
UPDATE ai_model_config set model_name = 'Khoa Đại Tín Phi (streaming)' where id = 'TTS_XunFeiStreamTTS';
UPDATE ai_model_config set model_name = 'Minimax (streaming)' where id = 'TTS_MinimaxStreamTTS';
UPDATE ai_model_config set model_name = 'Alibaba Cloud (streaming)' where id = 'TTS_AliyunStreamTTS';
UPDATE ai_model_config set model_name = 'PaddleSpeech (streaming)' where id = 'TTS_PaddleSpeechTTS';
UPDATE ai_model_config set model_name = 'IndexTTS (streaming)' where id = 'TTS_IndexStreamTTS';

update ai_model_config SET sort = 2 where id = 'TTS_LinkeraiTTS';
update ai_model_config SET sort = 3 where id = 'TTS_HuoshanDoubleStreamTTS';
update ai_model_config SET sort = 4 where id = 'TTS_AliBLStreamTTS';
update ai_model_config SET sort = 5 where id = 'TTS_XunFeiStreamTTS';
update ai_model_config SET sort = 6 where id = 'TTS_MinimaxStreamTTS';
update ai_model_config SET sort = 7 where id = 'TTS_AliyunStreamTTS';
update ai_model_config SET sort = 8 where id = 'TTS_IndexStreamTTS';
update ai_model_config SET sort = 9 where id = 'TTS_PaddleSpeechTTS';
update ai_model_config SET sort = 10 where id = 'TTS_DoubaoTTS';
update ai_model_config SET sort = 11 where id = 'TTS_TencentTTS';
update ai_model_config SET sort = 12 where id = 'TTS_AliyunTTS';
update ai_model_config SET sort = 13 where id = 'TTS_OpenAITTS';
update ai_model_config SET sort = 14 where id = 'TTS_CosyVoiceSiliconflow';
update ai_model_config SET sort = 15 where id = 'TTS_CozeCnTTS';
update ai_model_config SET sort = 16 where id = 'TTS_FishSpeech';
update ai_model_config SET sort = 17 where id = 'TTS_GPT_SOVITS_V3';
update ai_model_config SET sort = 18 where id = 'TTS_GPT_SOVITS_V2';
update ai_model_config SET sort = 19 where id = 'TTS_TTS302AI';
update ai_model_config SET sort = 20 where id = 'TTS_GizwitsTTS';
update ai_model_config SET sort = 21 where id = 'TTS_VolcesAiGatewayTTS';
update ai_model_config SET sort = 22 where id = 'TTS_ACGNTTS';
update ai_model_config SET sort = 23 where id = 'TTS_CustomTTS';

UPDATE ai_model_config set model_name = 'Nhận dạng giọng nói Tín Phi (streaming)' where id = 'ASR_XunfeiStream';
UPDATE ai_model_config set model_name = 'Nhận dạng giọng nói Qwen3Flash' where id = 'ASR_Qwen3Flash';

update ai_model_config SET sort = 2 where id = 'ASR_FunASRServer';
update ai_model_config SET sort = 3 where id = 'ASR_XunfeiStream';
update ai_model_config SET sort = 4 where id = 'ASR_AliyunStreamASR';
update ai_model_config SET sort = 5 where id = 'ASR_DoubaoStreamASR';
update ai_model_config SET sort = 6 where id = 'ASR_TencentASR';
update ai_model_config SET sort = 7 where id = 'ASR_BaiduASR';
update ai_model_config SET sort = 8 where id = 'ASR_DoubaoASR';
update ai_model_config SET sort = 9 where id = 'ASR_AliyunASR';
update ai_model_config SET sort = 10 where id = 'ASR_SherpaASR';
update ai_model_config SET sort = 11 where id = 'ASR_OpenaiASR';
update ai_model_config SET sort = 12 where id = 'ASR_GroqASR';
update ai_model_config SET sort = 13 where id = 'ASR_VoskASR';
update ai_model_config SET sort = 14 where id = 'ASR_Qwen3Flash';

UPDATE ai_model_config SET config_json='{\"type\": \"openai\", \"base_url\": \"https://ark.cn-beijing.volces.com/api/v3\", \"model_name\": \"doubao-1-5-pro-32k-250115\", \"api_key\": \"你的api_key\"}' where id = 'LLM_DoubaoLLM' AND config_json LIKE '%你的api_key"%';