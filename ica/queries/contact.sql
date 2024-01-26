SELECT
    "ZFULLNUMBER",
    "ZADDRESS"
FROM "ZABCDPHONENUMBER"
-- Using a FULL OUTER JOIN would be preferable here, however sqlite3 has only
-- recently added support for FULL OUTER JOIN, and attempting to upgrade
-- Python's version of sqlite3 has proven challenging and is fraught with its
-- own risks; therefore, we opt for simply using a LEFT JOIN instead
LEFT JOIN "ZABCDEMAILADDRESS"
    ON "ZABCDPHONENUMBER"."ZOWNER" = "ZABCDEMAILADDRESS"."ZOWNER"
WHERE "ZABCDPHONENUMBER"."ZOWNER" = (
    SELECT "Z_PK"
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
);
