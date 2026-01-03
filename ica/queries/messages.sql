SELECT
    "message"."ROWID",
    "text",
    "handle_id",
    "handle"."id" AS "sender_name",
    "attributedBody",
    datetime("message"."date" / 1000000000 + strftime("%s", "2001-01-01") ,"unixepoch") as "datetime",
    "is_from_me"
FROM "message"
LEFT JOIN "handle" ON "message"."handle_id" = "handle"."ROWID"
WHERE "message"."ROWID" IN (
    -- Get all messages tied to chat
    SELECT "message_id"
    FROM "chat_message_join"
    WHERE "chat_id" IN ({chat_ids_placeholder})
) ORDER BY "datetime"
