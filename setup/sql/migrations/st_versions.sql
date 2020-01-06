UPDATE packages SET st_versions = ARRAY[2, 3, 4]::int[] WHERE st_versions = ARRAY[2, 3]::int[];
UPDATE packages SET st_versions = ARRAY[3, 4]::int[] WHERE st_versions = ARRAY[3]::int[];
