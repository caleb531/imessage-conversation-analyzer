-- Get all attachments (GIFs, images, links, etc.)
SELECT "mime_type" FROM "attachment" INNER JOIN "message_attachment_join" ON "attachment"."ROWID" = "attachment_id" WHERE "message_id" IN (
    -- Get all handles tied to chat
    SELECT "message_id" FROM "chat_message_join" WHERE "chat_id" IN (
        -- Get all chats with the specified phone number
        SELECT "chat"."ROWID" FROM "chat" WHERE "chat_identifier" LIKE ('%' || :phone_number)
    )
)
