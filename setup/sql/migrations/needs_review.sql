ALTER TABLE package_stats ADD needs_review boolean NOT NULL DEFAULT FALSE;
ALTER TABLE dependencies ADD needs_review boolean NOT NULL DEFAULT FALSE;

UPDATE package_stats SET needs_review = TRUE WHERE is_missing = TRUE OR removed = TRUE;
UPDATE dependencies SET needs_review = TRUE WHERE is_missing = TRUE OR removed = TRUE;
