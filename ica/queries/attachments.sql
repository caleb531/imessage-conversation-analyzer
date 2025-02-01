SELECT "mime_type",
       "filename",
       "message_id",
        datetime("message"."date" / 1000000000 + strftime("%s", "2001-01-01") ,"unixepoch") as "datetime",
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
