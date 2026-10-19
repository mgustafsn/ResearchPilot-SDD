CREATE TABLE papers (
    id UUID PRIMARY KEY,
    provider TEXT NOT NULL CHECK (provider = 'openalex'),
    provider_id TEXT NOT NULL CHECK (char_length(provider_id) BETWEEN 1 AND 255),
    doi TEXT,
    title TEXT NOT NULL CHECK (char_length(btrim(title)) > 0),
    abstract TEXT,
    authors JSONB NOT NULL DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(authors) = 'array' AND jsonb_array_length(authors) <= 100),
    publication_year INTEGER CHECK (publication_year BETWEEN 1 AND 9999),
    publication_date DATE,
    venue TEXT,
    citation_count BIGINT CHECK (citation_count >= 0),
    source_url TEXT NOT NULL,
    publication_url TEXT,
    full_text_url TEXT,
    is_open_access BOOLEAN,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider, provider_id)
);

CREATE INDEX papers_doi_idx ON papers (doi) WHERE doi IS NOT NULL;

CREATE TABLE search_runs (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    input_snapshot JSONB NOT NULL CHECK (jsonb_typeof(input_snapshot) = 'object'),
    status TEXT NOT NULL CHECK (status IN ('pending', 'succeeded', 'failed')),
    ownership_token UUID NOT NULL UNIQUE,
    lease_expires_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    raw_fetched_count BIGINT NOT NULL DEFAULT 0 CHECK (raw_fetched_count >= 0),
    skipped_count BIGINT NOT NULL DEFAULT 0 CHECK (skipped_count >= 0),
    duplicate_count BIGINT NOT NULL DEFAULT 0 CHECK (duplicate_count >= 0),
    queries_used JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(queries_used) = 'array'),
    queries_unused JSONB NOT NULL DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(queries_unused) = 'array'),
    error_code TEXT,
    UNIQUE (project_id, id),
    CHECK (
        (status = 'pending' AND finished_at IS NULL AND error_code IS NULL)
        OR (status = 'succeeded' AND finished_at IS NOT NULL AND error_code IS NULL)
        OR (status = 'failed' AND finished_at IS NOT NULL AND error_code IS NOT NULL)
    )
);

CREATE UNIQUE INDEX search_runs_one_pending_per_project
    ON search_runs (project_id) WHERE status = 'pending';
CREATE INDEX search_runs_project_started_idx ON search_runs (project_id, started_at DESC);

CREATE TABLE project_papers (
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE RESTRICT,
    search_run_id UUID NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    FOREIGN KEY (project_id, search_run_id)
        REFERENCES search_runs(project_id, id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, paper_id),
    UNIQUE (project_id, ordinal)
);
