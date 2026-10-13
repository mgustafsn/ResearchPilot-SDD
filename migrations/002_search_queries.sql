ALTER TABLE projects
    ADD COLUMN mutation_revision BIGINT NOT NULL DEFAULT 0 CHECK (mutation_revision >= 0),
    ADD COLUMN query_context_revision BIGINT NOT NULL DEFAULT 0 CHECK (query_context_revision >= 0),
    ADD COLUMN generated_context_revision BIGINT,
    ADD CONSTRAINT generated_context_bounds CHECK (
        generated_context_revision IS NULL OR
        (generated_context_revision >= 0 AND generated_context_revision <= query_context_revision)
    );

CREATE TABLE search_queries (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    text TEXT NOT NULL CHECK (char_length(text) BETWEEN 1 AND 160),
    normalized_key TEXT COLLATE "C" NOT NULL CHECK (char_length(normalized_key) > 0),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    origin TEXT NOT NULL CHECK (origin IN ('manual', 'generated')),
    user_owned BOOLEAN NOT NULL,
    slot SMALLINT NOT NULL CHECK (slot BETWEEN 1 AND 20),
    CHECK (origin != 'manual' OR user_owned),
    UNIQUE (project_id, normalized_key),
    UNIQUE (project_id, slot)
);
