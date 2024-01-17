SELECT
    "ZFULLNUMBER",
    "ZADDRESS"
FROM "ZABCDPHONENUMBER"
FULL OUTER JOIN "ZABCDEMAILADDRESS"
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
