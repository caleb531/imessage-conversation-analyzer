-- Get messages
SELECT "text", "is_from_me" FROM "message" WHERE "message"."ROWID" IN (
    -- Get all messages tied to chat
    SELECT "message_id" FROM "chat_message_join" WHERE "chat_id" IN (
        -- Get all chats with the specified phone number
        SELECT "chat"."ROWID" FROM "chat" WHERE "chat_identifier" LIKE ('%' || :phone_number)
    )
) ORDER BY "date"
