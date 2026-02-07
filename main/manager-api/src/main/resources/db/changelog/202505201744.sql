-- Cập nhật trường fields của ai_model_provider, đổi type là dict thành string
update ai_model_provider set fields = replace(fields, '"type": "dict"', '"type": "string"') where id not in ('SYSTEM_LLM_fastgpt', 'SYSTEM_TTS_custom');
update ai_model_provider set fields = replace(fields, '"type":"dict"', '"type": "string"') where id not in ('SYSTEM_LLM_fastgpt', 'SYSTEM_TTS_custom');