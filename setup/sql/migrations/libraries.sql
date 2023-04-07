ALTER TABLE releases ADD COLUMN python_versions varchar[];
ALTER TABLE releases RENAME dependencies TO libraries;

ALTER TABLE dependencies RENAME TO libraries;
ALTER TABLE libraries DROP COLUMN load_order;

ALTER TABLE dependency_releases RENAME TO library_releases;
ALTER TABLE library_releases RENAME dependency TO library;

ALTER TABLE library_releases ADD COLUMN python_versions varchar[];
UPDATE library_releases SET python_versions = '{3.3}';
ALTER TABLE library_releases ALTER python_versions SET NOT NULL;
