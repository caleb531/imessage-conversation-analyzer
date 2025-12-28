-- To maximize flexibility, we'd query for contacts with an email address but no
-- phone number (which is a very valid use case because a person's iMessage may
-- not be configured to send/receive from a phone number). Accomplishing this
-- requires an effective FULL OUTER JOIN however sqlite3 has only recently added
-- support for FULL OUTER JOIN, and attempting to upgrade Python's version of
-- sqlite3 has proven challenging and is fraught with its own risks. Therefore,
-- we opt for using a UNION ALL of a LEFT JOIN and RIGHT JOIN instead; we can
-- also avoid duplicating the subquery for each WHERE clause by utilizing a
-- Common Table Expression (CTE)
WITH "contact_search" AS (
    SELECT
        "Z_PK"
    FROM "ZABCDRECORD"
    WHERE (
        lower(
            trim(
                ifnull("ZFIRSTNAME", '')
                ||
                ' '
                ||
                ifnull("ZLASTNAME", '')
            )
        ) = lower(
            trim(:contact_identifier)
        )
    )
    UNION
    SELECT
        "ZOWNER"
    FROM "ZABCDEMAILADDRESS"
    WHERE lower(trim("ZADDRESS")) = lower(trim(:contact_identifier))
    UNION
    SELECT
        "ZOWNER"
    FROM "ZABCDPHONENUMBER"
    WHERE (
        -- The macOS contacts database stores the phone number as the user
        -- entered it (without normalization), so we must normalize each phone
        -- number ourselves during comparison by stripping out common formatting
        -- characters
        replace(
            replace(
                replace(
                    replace(
                        replace("ZFULLNUMBER", ' ', ''),
                        '-',
                        ''
                    ),
                    '(',
                    ''
                ),
                ')',
                ''
            ),
            '+',
            ''
        ) LIKE '%' || replace(
            replace(
                replace(
                    replace(
                        replace(:contact_identifier, ' ', ''),
                        '-',
                        ''
                    ),
                    '(',
                    ''
                ),
                ')',
                ''
            ),
            '+',
            ''
        )
    )
)

SELECT
    "ZABCDRECORD"."Z_PK" AS "contact_id",
    "ZABCDRECORD"."ZFIRSTNAME",
    "ZABCDRECORD"."ZLASTNAME",
    "ZABCDPHONENUMBER"."ZFULLNUMBER",
    "ZABCDEMAILADDRESS"."ZADDRESS"
FROM "ZABCDRECORD"
LEFT JOIN "ZABCDPHONENUMBER" ON "ZABCDRECORD"."Z_PK" = "ZABCDPHONENUMBER"."ZOWNER"
LEFT JOIN "ZABCDEMAILADDRESS" ON "ZABCDRECORD"."Z_PK" = "ZABCDEMAILADDRESS"."ZOWNER"
WHERE "ZABCDRECORD"."Z_PK" IN (SELECT * FROM "contact_search")

