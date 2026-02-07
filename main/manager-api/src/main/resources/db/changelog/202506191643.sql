-- Hướng dẫn cấu hình nhận dạng ý định LLM
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Hướng dẫn cấu hình nhận dạng ý định LLM：
1. Sử dụng LLM độc lập để nhận dạng ý định
2. Mặc định sử dụng mô hình selected_module.LLM
3. Có thể cấu hình sử dụng LLM độc lập (như ChatGLMLLM miễn phí)
4. Tính phổ biến cao, nhưng sẽ tăng thời gian xử lý
Hướng dẫn cấu hình：
1. Chỉ định mô hình LLM sử dụng trong trường llm
2. Nếu không chỉ định, sẽ sử dụng mô hình selected_module.LLM' WHERE `id` = 'Intent_intent_llm';

-- Hướng dẫn cấu hình nhận dạng ý định gọi hàm
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Hướng dẫn cấu hình nhận dạng ý định gọi hàm：
1. Sử dụng chức năng function_call của LLM để nhận dạng ý định
2. Cần LLM được chọn hỗ trợ function_call
3. Gọi công cụ theo nhu cầu, tốc độ xử lý nhanh' WHERE `id` = 'Intent_function_call';