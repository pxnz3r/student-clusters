# student-clusters

AI Lab coursework: grouping students by attendance, study activity and assignment completion with hierarchical clustering and K-Means.

## Layout

- `student_clusters/` this project's code: `data.py` (inputs), `groups.py` (group names and advice), `report.py` (which outputs make up the results)
- `pxlab/` vendored copy of the shared engine (see `pxlab/VERSION`). Don't edit it here; it is replaced on the next sync.
- `prepared/students.csv` one row per student, committed; `scripts/build_students.py` rebuilds it from the OULAD download in `data/` (ignored)
- `main.py` runs the full study and rewrites `docs/results.md`; `app.py` is the Streamlit demo; `app_overview.md` the demo's Overview text
- `outputs/` figures and CSV tables, `models/` the K-Means pipeline and group names (both committed for the hosted app)
- `docs/` methodology, results, deploy

## Commands

- Full study: `uv run python main.py`
- Rebuild the student table: `uv run python scripts/build_students.py`
- Demo: `uv run streamlit run app.py`
- Lint: `uv run ruff check . && uv run ruff format --check .`

## Conventions

- Beginner-student style on purpose: plain functions, docstrings on every function, comments explaining the AI concepts.
- Seed 42 everywhere.
- After changing the study, re-run `main.py` and refresh the README results and `app_overview.md`.
