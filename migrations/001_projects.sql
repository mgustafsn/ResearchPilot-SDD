CREATE TABLE projects (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL CHECK (char_length(btrim(title)) BETWEEN 1 AND 200),
    research_question TEXT NOT NULL CHECK (char_length(btrim(research_question)) BETWEEN 1 AND 5000),
    keywords JSON NOT NULL,
    year_from INTEGER CHECK (year_from BETWEEN 1 AND 9999),
    year_to INTEGER CHECK (year_to BETWEEN 1 AND 9999),
    max_paper_count INTEGER NOT NULL CHECK (max_paper_count BETWEEN 1 AND 250),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CHECK (year_from IS NULL OR year_to IS NULL OR year_from <= year_to)
);
