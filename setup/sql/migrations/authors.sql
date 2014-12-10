ALTER TABLE packages ADD authors varchar[];
UPDATE packages SET authors = string_to_array(author, ', ');
ALTER TABLE packages DROP COLUMN author;

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

DROP INDEX package_search_idx;
DROP TRIGGER search_vector_update ON packages;
DROP FUNCTION package_search_trigger();

ALTER TABLE package_search_entries ADD authors varchar[];
ALTER TABLE package_search_entries DROP COLUMN author;

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

CREATE TRIGGER search_vector_update AFTER INSERT OR UPDATE
    ON packages FOR EACH ROW EXECUTE PROCEDURE package_search_trigger();

CREATE INDEX package_search_idx ON package_search_entries USING gin(search_vector);

-- Trigger reindex
UPDATE packages SET name = name;
