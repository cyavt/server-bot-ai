-- Cập nhật cấu hình plugin get_news_from_newsnow hiện có
UPDATE ai_model_provider 
SET fields = JSON_ARRAY(
    JSON_OBJECT(
        'key', 'url',
        'type', 'string',
        'label', 'Địa chỉ giao diện',
        'default', 'https://newsnow.busiyi.world/api/s?id='
    ),
    JSON_OBJECT(
        'key', 'news_sources',
        'type', 'string',
        'label', 'Cấu hình nguồn tin tức',
        'default', '澎湃新闻;百度热搜;财联社'
    )
)
WHERE provider_code = 'get_news_from_newsnow' 
AND model_type = 'Plugin'; 