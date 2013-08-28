DROP INDEX package_search_idx;
DROP TRIGGER search_vector_update ON packages;
DROP FUNCTION package_search_trigger();
DROP FUNCTION split_package_name(varchar);

DROP TABLE package_search_entries;
DROP TABLE http_cache_entries;

DROP TRIGGER ensure_package_stats ON packages;
DROP FUNCTION create_package_stats();

DROP TABLE parsed_log_files;
DROP TABLE system_stats;
DROP TABLE package_stats;
DROP TABLE readmes;
DROP TABLE releases;
DROP TABLE packages;
DROP TABLE usage;
DROP TABLE unique_package_installs;
DROP TABLE ips;
DROP TABLE install_counts;
DROP TABLE first_installs;
