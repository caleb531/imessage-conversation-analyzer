SELECT
    "attachment"."ROWID",
    "mime_type",
    "filename",
    "message_id",
    "date",
    "is_from_me"
FROM "attachment"
INNER JOIN "message_attachment_join"
    ON "attachment"."ROWID" = "attachment_id"
INNER JOIN "message"
    ON "message"."ROWID" = "message_id"
WHERE
    "message_id" IN (
        -- Get all messages tied to chat
        SELECT "message_id"
        FROM "chat_message_join"
        WHERE "chat_id" IN (
            -- Get all chats with the specified phone number
            SELECT "chat"."ROWID"
            FROM "chat"
            WHERE CAST(chat_identifier AS VARCHAR) IN (SELECT unnest(string_split(?, '|')))
        )
    )
ORDER BY "date" ASC
