-- Script để cập nhật checksum cho các changeset đã được dịch
-- Chạy script này trong database để Liquibase tính lại checksum

-- Xóa checksum cũ để Liquibase tính lại checksum mới
-- Sử dụng JOIN để tránh lỗi safe update mode
UPDATE DATABASECHANGELOG dcl
INNER JOIN (
    SELECT ID, AUTHOR, FILENAME
    FROM DATABASECHANGELOG
    WHERE ID IN (
        '202503141335',
        '202503141346',
        '202504082211',
        '202504092335',
        '202504112044',
        '202504112058',
        '202504151206',
        '202504181536',
        '202504221135',
        '202504221555',
        '202504251422',
        '202504291043',
        '202504301341',
        '202505022134',
        '202505081146',
        '202505091555',
        '202505111914',
        '202505122348',
        '202505142037',
        '202505182234',
        '202505201744',
        '202505151451',
        '202505271414',
        '202505292203',
        '202506010920',
        '202506031639'
    )
) AS temp ON dcl.ID = temp.ID 
    AND dcl.AUTHOR = temp.AUTHOR 
    AND dcl.FILENAME = temp.FILENAME
SET dcl.MD5SUM = NULL;
