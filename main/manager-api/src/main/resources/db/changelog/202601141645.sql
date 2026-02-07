-- Dọn dẹp hàng loạt định nghĩa trường sample_rate trong ai_model_provider
UPDATE `ai_model_provider` ap
JOIN (
    SELECT 
        id,
        JSON_ARRAYAGG(
            JSON_OBJECT('key', jt.k, 'label', jt.l, 'type', jt.t)
        ) AS new_fields
    FROM `ai_model_provider`,
         JSON_TABLE(`fields`, '$[*]' COLUMNS (
             k VARCHAR(50) PATH '$.key',
             l VARCHAR(100) PATH '$.label',
             t VARCHAR(20) PATH '$.type'
         )) AS jt
    WHERE `model_type` = 'TTS' 
      AND jt.k != 'sample_rate'
    GROUP BY id
) filtered ON ap.id = filtered.id
SET ap.fields = filtered.new_fields;

-- Dọn dẹp sample_rate ở cấp cao nhất của config_json
UPDATE `ai_model_config`
SET `config_json` = JSON_REMOVE(`config_json`, '$.sample_rate')
WHERE `model_type` = 'TTS'
  AND JSON_EXTRACT(`config_json`, '$.sample_rate') IS NOT NULL;

-- Dọn dẹp tham số sample_rate của Minimax streaming TTS (nằm trong audio_setting)
UPDATE `ai_model_config` SET 
`config_json` = JSON_SET(`config_json`, '$.audio_setting', JSON_REMOVE(JSON_EXTRACT(`config_json`, '$.audio_setting'), '$.sample_rate'))
WHERE `id` = 'TTS_MinimaxStreamTTS'
AND JSON_EXTRACT(`config_json`, '$.audio_setting.sample_rate') IS NOT NULL;