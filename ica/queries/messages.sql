SELECT
    "ROWID",
    COALESCE(CAST("text" AS VARCHAR), decode_body(CAST("attributedBody" AS BLOB))) AS "text",
    "date",
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
        WHERE CAST(chat_identifier AS VARCHAR) IN (SELECT unnest(string_split(?, '|')))
    )
)
ORDER BY "date" ASC
