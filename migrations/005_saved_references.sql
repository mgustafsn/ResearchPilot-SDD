CREATE TABLE saved_references (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider = 'openalex'),
    provider_id TEXT NOT NULL CHECK (char_length(btrim(provider_id)) BETWEEN 1 AND 255),
    paper_snapshot JSONB NOT NULL CHECK (jsonb_typeof(paper_snapshot) = 'object'),
    title_sort_key TEXT NOT NULL,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, provider, provider_id),
    CHECK (paper_snapshot->>'provider' IS NOT NULL AND paper_snapshot->>'provider' = provider),
    CHECK (paper_snapshot->>'provider_id' IS NOT NULL AND paper_snapshot->>'provider_id' = provider_id),
    CHECK (paper_snapshot->>'title' IS NOT NULL AND char_length(btrim(paper_snapshot->>'title')) > 0),
    CHECK (paper_snapshot->>'source_url' IS NOT NULL AND char_length(btrim(paper_snapshot->>'source_url')) > 0),
    CHECK (char_length(btrim(title_sort_key)) > 0)
);

CREATE INDEX saved_references_project_order_idx
    ON saved_references (project_id, title_sort_key, provider, provider_id);
