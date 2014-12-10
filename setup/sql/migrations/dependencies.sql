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
    removed                  boolean       NOT NULL DEFAULT FALSE
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

ALTER TABLE releases ADD dependencies varchar[];
