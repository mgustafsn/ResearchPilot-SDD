# Known issues

## BUG-PRJ-001 — Invalid publication-year input becomes unbounded

- **Reported**: 2026-10-12, by the user during project-management review.
- **Requirements**: FR-PRJ-004, FR-PRJ-007, AC-PRJ-004.
- **Status**: Open; fix deferred to a future MVP iteration at the user's request.
- **Observed by user**: Publication-year controls permit nonnumeric characters;
  saving then displays "Any – Any" instead of a validation error.
- **Impact**: An invalid intended year restriction can silently become unbounded.
- **Expected**: Intentionally blank years remain optional. Invalid nonblank input
  must produce a readable error and preserve form input/stored project data.
- **Inspection finding (not reproduced)**: `frontend/app.js` converts an empty
  number-control value to null. Browser number controls can expose an invalid
  entry as an empty value; treating that as deliberately blank is a possible cause.
  Browser/version and exact keystrokes were not supplied; do not claim independent
  reproduction or a confirmed root cause.
- **Future fix/verification**: Distinguish invalid input from deliberate omission;
  add real-browser typing/pasting regressions for both year bounds, create/edit,
  unchanged persisted values, and genuinely blank unbounded years. Verify the
  user's browser behavior before selecting the fix.

Existing green backend and browser tests did not establish this input behavior.
The user accepted feature 001 with this known limitation on 2026-10-12 (reply:
"Yesw", interpreted as yes to the explicit acceptance question). The issue remains
open; acceptance/deferral is not a claim of full requirement compliance or a fix.
