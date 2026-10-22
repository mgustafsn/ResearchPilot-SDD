ALTER TABLE project_papers
    ADD COLUMN embedding_score NUMERIC(7,6),
    ADD COLUMN ranking_provenance JSONB,
    ADD CONSTRAINT project_papers_embedding_score_range
        CHECK (embedding_score BETWEEN 0 AND 1),
    ADD CONSTRAINT project_papers_ranking_pair
        CHECK ((embedding_score IS NULL) = (ranking_provenance IS NULL)),
    ADD CONSTRAINT project_papers_ranking_object
        CHECK (ranking_provenance IS NULL OR jsonb_typeof(ranking_provenance) = 'object');

ALTER TABLE search_runs
    ADD COLUMN ranking_provenance JSONB,
    ADD CONSTRAINT search_runs_ranking_object
        CHECK (ranking_provenance IS NULL OR jsonb_typeof(ranking_provenance) = 'object');
