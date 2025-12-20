SELECT
    "ROWID",
    "text",
    "attributedBody",
    "message"."date" + 978307200000000000 as "datetime",
    "is_from_me"
FROM "message"
WHERE "message"."ROWID" IN (
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
) ORDER BY "datetime"
