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
            trim(:contact_name)
        )
    )
)

SELECT
    "ZFULLNUMBER",
    "ZADDRESS"
FROM "ZABCDPHONENUMBER"
LEFT JOIN "ZABCDEMAILADDRESS"
  ON "ZABCDPHONENUMBER"."ZOWNER" = "ZABCDEMAILADDRESS"."ZOWNER"
WHERE "ZABCDPHONENUMBER"."ZOWNER" IN (SELECT * FROM "contact_search")
-- Combine the results of the LEFT JOIN queries into a single
-- result set
UNION ALL
SELECT
    "ZFULLNUMBER",
    "ZADDRESS"
FROM "ZABCDEMAILADDRESS"
-- RIGHT JOIN has roughly the same sqlite3 version compatibility as FULL OUTER
-- JOIN, so we cannot use it here either; fortunately, we can simulate a RIGHT
-- JOIN pretty easily by swapping the FROM and JOIN table names
LEFT JOIN "ZABCDPHONENUMBER"
  ON "ZABCDEMAILADDRESS"."ZOWNER" = "ZABCDPHONENUMBER"."ZOWNER"
WHERE "ZABCDEMAILADDRESS"."ZOWNER" IN (SELECT * FROM "contact_search");
