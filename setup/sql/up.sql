-- When a package was first installed, used for displaying packages in release date order
CREATE TABLE first_installs (
    package                  varchar(200) NOT NULL PRIMARY KEY,
    first_install            timestamp    NOT NULL
);


-- A tally of installs for website display purposes
CREATE TABLE install_counts (
    package                  varchar(200) NOT NULL PRIMARY KEY,
    unique_installs          integer      NOT NULL DEFAULT 0,
    installs                 integer      NOT NULL DEFAULT 0,
    osx_unique_installs      integer      NOT NULL DEFAULT 0,
    osx_installs             integer      NOT NULL DEFAULT 0,
    windows_unique_installs  integer      NOT NULL DEFAULT 0,
    windows_installs         integer      NOT NULL DEFAULT 0,
    linux_unique_installs    integer      NOT NULL DEFAULT 0,
    linux_installs           integer      NOT NULL DEFAULT 0
);


CREATE TABLE daily_install_counts (
    date                     date         NOT NULL,
    package                  varchar(200) NOT NULL,
    installs                 integer      NOT NULL DEFAULT 0,
    osx_installs             integer      NOT NULL DEFAULT 0,
    windows_installs         integer      NOT NULL DEFAULT 0,
    linux_installs           integer      NOT NULL DEFAULT 0,
    PRIMARY KEY(date, package)
);


-- A list of all of the unique IP/platform combos ever seen
CREATE TABLE ips (
    ip                       varchar(15) NOT NULL,
    sublime_platform         varchar(10) NOT NULL,
    PRIMARY KEY(ip, sublime_platform)
);


-- All of the unique IP/package/platform combos ever seen
CREATE TABLE unique_package_installs (
    ip                       varchar(15)  NOT NULL,
    package                  varchar(200) NOT NULL,
    sublime_platform         varchar(10)  NOT NULL,
    PRIMARY KEY(ip, package, sublime_platform)
);


-- A record of every install, update and removal of a package
CREATE TABLE usage (
    usage_id                 serial       NOT NULL PRIMARY KEY,
    ip                       varchar(15)  NOT NULL,
    user_agent               varchar(500) NOT NULL,
    package                  varchar(200) NOT NULL,
    operation                varchar(20)  NOT NULL,
    date_time                timestamp    NOT NULL,
    version                  varchar(100) NOT NULL,
    old_version              varchar(100),
    package_control_version  varchar(100) NOT NULL,
    sublime_platform         varchar(10)  NOT NULL,
    sublime_version          varchar(100) NOT NULL
);
CREATE INDEX usage_date_time ON usage USING btree (date_time);


-- The main package info
CREATE TABLE packages (
    name                     varchar(500)  NOT NULL PRIMARY KEY,
    description              varchar       NOT NULL DEFAULT '',
    authors                  varchar[],
    homepage                 varchar       NOT NULL DEFAULT '',
    previous_names           varchar[],
    labels                   varchar[],
    platforms                varchar[],
    st_versions              integer[],
    last_modified            timestamp     NOT NULL,
    last_seen                timestamp     NOT NULL,
    sources                  varchar[]     NOT NULL,
    readme                   varchar,
    issues                   varchar,
    donate                   varchar,
    buy                      varchar
);


CREATE TABLE dependencies (
    name                     varchar(500)  NOT NULL PRIMARY KEY,
    load_order               varchar(2)    NOT NULL,
    description              varchar       NOT NULL DEFAULT '',
    authors                  varchar[],
    issues                   varchar       NOT NULL DEFAULT '',
    last_seen                timestamp     NOT NULL,
    sources                  varchar[]     NOT NULL,
    is_missing               boolean       NOT NULL DEFAULT FALSE,
    missing_error            varchar       NOT NULL DEFAULT '',
    removed                  boolean       NOT NULL DEFAULT FALSE,
    needs_review             boolean       NOT NULL DEFAULT FALSE
);


CREATE TABLE dependency_releases (
    dependency               varchar(500)  NOT NULL REFERENCES dependencies(name) ON DELETE CASCADE ON UPDATE CASCADE,
    platforms                varchar[]     NOT NULL,
    sublime_text             varchar       NOT NULL,
    version                  varchar       NOT NULL,
    url                      varchar       NOT NULL,
    sha256                   varchar,
    PRIMARY KEY(dependency, platforms, sublime_text, version)
);


-- Each package can have more than one release at a time, and for different platforms
CREATE TABLE releases (
    package                  varchar(500)  NOT NULL REFERENCES packages(name) ON DELETE CASCADE ON UPDATE CASCADE,
    platforms                varchar[]     NOT NULL,
    sublime_text             varchar       NOT NULL,
    version                  varchar       NOT NULL,
    url                      varchar       NOT NULL,
    date                     timestamp     NOT NULL,
    dependencies             varchar[],
    PRIMARY KEY(package, platforms, sublime_text, version)
);


CREATE TABLE readmes (
    package                  varchar(500)  NOT NULL REFERENCES packages(name) ON DELETE CASCADE ON UPDATE CASCADE PRIMARY KEY,
    filename                 varchar       NOT NULL,
    format                   varchar       NOT NULL CHECK(format IN ('markdown', 'textile', 'creole', 'rst', 'txt')),
    source                   text          NOT NULL,
    rendered_html            text          NOT NULL
);


-- This stores some periodically-computed stats for each package
CREATE TABLE package_stats (
    package                  varchar(500)  NOT NULL REFERENCES packages(name) ON DELETE CASCADE ON UPDATE CASCADE PRIMARY KEY,
    first_seen               timestamp     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_missing               boolean       NOT NULL DEFAULT FALSE,
    missing_error            varchar       NOT NULL DEFAULT '',
    removed                  boolean       NOT NULL DEFAULT FALSE,
    installs_rank            integer,
    trending_rank            integer,
    z_value                  float,
    needs_review             boolean       NOT NULL DEFAULT FALSE
);


-- Make sure every package has stats
CREATE FUNCTION create_package_stats() RETURNS trigger AS $$
BEGIN
    INSERT INTO package_stats (package) VALUES (NEW.name);
    return NEW;
END
$$ LANGUAGE plpgsql;


CREATE TRIGGER ensure_package_stats AFTER INSERT
    ON packages FOR EACH ROW EXECUTE PROCEDURE create_package_stats();


-- Statistics about the overall system
CREATE TABLE system_stats (
    name                     varchar(500)  NOT NULL,
    value                    decimal(20,3) NOT NULL DEFAULT 0.000,
    date                     date          NOT NULL,
    PRIMARY KEY(name, date)
);


-- A list of all log files that have been parsed
CREATE TABLE parsed_log_files (
    filename                 varchar(500)  NOT NULL PRIMARY KEY
);


-- Data store for cached HTTP content, as used by package_control code
CREATE TABLE http_cache_entries (
    key                      varchar(64) NOT NULL PRIMARY KEY,
    content                  bytea,
    last_modified            timestamp   NOT NULL
);


-- Keep the full text search stuff separate from the "clean" package data
CREATE TABLE package_search_entries (
    package                  varchar(500) PRIMARY KEY REFERENCES packages(name) ON UPDATE CASCADE ON DELETE CASCADE,
    search_vector            tsvector,
    -- Track the space-separated version of these fields for highlighting
    name                     varchar(500),
    description              varchar,
    authors                  varchar[],
    split_name               varchar(500),
    split_description        varchar
);


-- Split package names up for better full text indexing
CREATE FUNCTION split_package_name(name varchar) RETURNS varchar AS $$
BEGIN
    -- In the following we add three spaces so we can intelligently collapse it after highlighting
    -- Split camelCase
    name := regexp_replace(name, '([a-z])([A-Z])|([a-zA-Z])([0-9])|([0-9])([a-zA-Z])', '\1\3\5   \2\4\6', 'g');
    -- Replace - and . with spaces
    name := regexp_replace(name, '([a-zA-Z0-9])([.\\-])([a-zA-Z0-9])', '\1   \2   \3', 'g');
    -- Add a space after "sublime"
    name := regexp_replace(name, '(sublime)([a-zA-Z0-9])', '\1   \2', 'gi');

    RETURN name;
END
$$ LANGUAGE plpgsql IMMUTABLE;


-- Highlight a search result
CREATE FUNCTION highlight_result(value varchar, query tsquery, collapse_spaces boolean) RETURNS varchar AS $$
BEGIN
    value := ts_headline(value, query, E'HighlightAll=TRUE, StartSel="\002", StopSel="\003"');
    IF (collapse_spaces = TRUE) THEN
        value := replace(value, '   ', '');
    END IF;
    RETURN value;
END;
$$ LANGUAGE plpgsql STABLE;


-- Highlights an array of varchars from search results
CREATE FUNCTION highlight_result_array(vals varchar[], query tsquery, collapse_spaces boolean) RETURNS varchar[] AS $$
DECLARE
    output varchar[];
BEGIN
    FOR I IN array_lower(vals, 1)..array_upper(vals, 1) LOOP
        output[I] := highlight_result(vals[I], query, collapse_spaces);
    END LOOP;
    RETURN output;
END;
$$ LANGUAGE plpgsql STABLE;


-- Function to update the full text index for a package
CREATE FUNCTION package_search_trigger() RETURNS trigger AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        DELETE FROM package_search_entries WHERE package = OLD.name;
    END IF;

    INSERT INTO package_search_entries (
        package,
        search_vector,
        name,
        description,
        authors,
        split_name,
        split_description
    ) VALUES (
        NEW.name,
        -- The name gets weighted most heavily
        setweight(to_tsvector('english', split_package_name(NEW.name) || ' ' || NEW.name), 'A') ||
            -- The author is fairly important
            setweight(to_tsvector('english', array_to_string(NEW.authors, ', ')), 'B') ||
            -- The description is pretty low since they tend to include a lot of unhelpful text
            setweight(to_tsvector('english', split_package_name(coalesce(NEW.description, '')) || ' ' || coalesce(NEW.description, '')), 'D'),
        NEW.name,
        NEW.description,
        NEW.authors,
        split_package_name(NEW.name),
        split_package_name(NEW.description)
    );
    return NEW;
END
$$ LANGUAGE plpgsql;

CREATE FUNCTION array_unique(arr anyarray) RETURNS anyarray LANGUAGE sql AS $$
    SELECT array_agg(DISTINCT a)
    FROM (
        SELECT unnest(arr) a 
        ORDER BY a
    ) sq
$$;

CREATE TRIGGER search_vector_update AFTER INSERT OR UPDATE
    ON packages FOR EACH ROW EXECUTE PROCEDURE package_search_trigger();

CREATE INDEX package_search_idx ON package_search_entries USING gin(search_vector);
