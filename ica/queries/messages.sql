SELECT
    m."ROWID",
    CAST(m."text" AS VARCHAR) AS "text",
    CAST(m."attributedBody" AS BLOB) AS "attributedBody",
    m."date",
    m."is_from_me"
FROM "chat" c
JOIN "chat_message_join" cmj ON c."ROWID" = cmj."chat_id"
JOIN "message" m ON cmj."message_id" = m."ROWID"
WHERE CAST(c.chat_identifier AS VARCHAR) IN (SELECT unnest(string_split(?, '|')))
ORDER BY m."date" ASC, m."ROWID" ASC
