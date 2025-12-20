SELECT
    a."ROWID",
    a."mime_type",
    a."filename",
    maj."message_id",
    m."date",
    m."is_from_me"
FROM "chat" c
JOIN "chat_message_join" cmj ON c."ROWID" = cmj."chat_id"
JOIN "message" m ON cmj."message_id" = m."ROWID"
JOIN "message_attachment_join" maj ON m."ROWID" = maj."message_id"
JOIN "attachment" a ON maj."attachment_id" = a."ROWID"
WHERE CAST(c.chat_identifier AS VARCHAR) IN (SELECT unnest(string_split(?, '|')))
ORDER BY m."date" ASC
