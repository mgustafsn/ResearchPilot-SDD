# Reduced MVP scope — feature boundaries approved; product decisions draft

The user approved the five included delivery slices and listed exclusions on
2026-10-12 (option A: keep all five features, build and approve one at a time).
This scope-boundary approval does not approve individual specifications, plans,
tasks, or implementation. Feature 001's specification and the paper-count decision
were separately approved on 2026-10-12; other product proposals below remain draft.

## Objective and stakeholders

Help an individual student or researcher discover real papers and retain a short
project reading list. The researcher is the primary user; student developers maintain
the system; course assessors examine traceability and evidence. Scholarly and AI
providers are external systems whose limits constrain the design, not end users.

## Included delivery slices

| Slice | User value | Prerequisite |
|---|---|---|
| 001 Projects | Persist a research question and search constraints | None |
| 002 Queries | Review and control what is searched | 001 |
| 003 Retrieval | Discover real, normalized, deduplicated papers | 001, 002 |
| 004 Ranking | Prioritize retrieved papers by semantic relevance | 003 |
| 005 References | Keep selected papers beyond later searches | 003; 004 for final demo |

Each slice is independently verifiable once its stated prerequisites exist; later
slices are not independent of project persistence or retrieval.

## Excluded

Clustering and subtopics; categorization explanations; manual paper organization;
Scopus and multi-provider retrieval; manual citations; reference notes, reading
status, citation numbering; authentication and public deployment; collaboration;
exports/Zotero; institutional access; PDF ingestion; embedding caches.

## Decisions proposed for approval

| Decision | Proposal | Relationship to baseline |
|---|---|---|
| Deployment | Local, single user, same-origin web application | Retain |
| Stack | Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL; vanilla JS | Retain to limit stack confounding |
| Paper limit (approved 2026-10-12) | Required integer 1–250; UI default 100 | Narrow baseline API limit 1–1000 |
| Query generation failure | Keep current list unchanged, show error; permit manual queries | Simplify baseline keyword/name fallback |
| Retrieval failure | Any enabled-query failure fails the attempt; retain old results | Simplify partial-success behavior |
| Ranking | Retain calibrated embedding score; show all retrieved papers | Drop baseline automatic 40% filtering |
| References | Provider-derived snapshots saved from search results only | Exclude baseline manual citations and editable metadata |
| Search progress | Visible pending/success/failure; no staged history polling initially | Simplify baseline UI |
| Ranking failure | Preserve previous result set; no silent lexical fallback | Explicit atomicity proposal |
| Interrupted work | Expiring search ownership token, stale writes rejected | Retain baseline safety intent |

Except for the separately approved paper limit, these are proposals, not facts
about the original or ratified decisions. Approve or change them before implementation.
Model names, timeouts, performance environment,
and request budgets require clarification before their respective plans.

## Final acceptance journey

Create project → review/edit/select suggestions → search OpenAlex → view unique,
ranked papers and source links → save a reference → search again → restart application
→ reopen project and find the saved reference unchanged.

Inject retrieval and embedding failures and verify old results and references remain.
Use identical frozen inputs to compare overlapping baseline and rebuild behavior.
Do not claim full feature parity or infer ranking accuracy from unit tests alone.
