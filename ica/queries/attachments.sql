SELECT "mime_type",
       "filename",
       "message_id"
FROM "attachment"
INNER JOIN "message_attachment_join"
    ON "attachment"."ROWID" = "attachment_id"
WHERE
    "message_id" IN (
        -- Get all messages tied to chat
        SELECT "message_id"
        FROM "chat_message_join"
        WHERE "chat_id" IN (
            -- Get all chats with the specified phone number
            SELECT "chat"."ROWID"
            FROM "chat"
            WHERE :chat_identifiers LIKE (
                '%'
                ||
                :chat_identifier_delimiter
                ||
                "chat_identifier"
                ||
                :chat_identifier_delimiter
                ||
                '%'
            )
        )
    )
