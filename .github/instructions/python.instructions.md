---
applyTo: "services/**/*.py"
description: This file describes instructions for Python 3.12 FastAPI services in reporting-svc and notifications-svc.
---

- Use Python 3.12 type hints on every function signature, including return types; prefer `dict[str, Any]` for open-ended JSON, `list[T]` for typed collections, and `str | None` for optional strings.
- Add a short module docstring that explains the service or module purpose, and keep public route/helper names descriptive and domain-focused.
- For services with multiple concerns, keep `app/main.py` thin (app creation, config constants, router inclusion, health check only) and put domain routes under `app/routers/` with one `APIRouter(prefix="/...", tags=["..."])` per concern.
- Before changing anything that looks like a bug or gap, check `exercises.md` — many rough edges (`app/legacy/format_helpers.py`, the CSV import error handling, missing validation) are deliberate course exercises. Change them only when the current task is the exercise that targets them.
- Read service URLs, database paths, and other runtime configuration with `os.getenv("VAR", "default")`; never hard-code hostnames or filesystem paths and never use `os.environ["VAR"]` for required config.
- For outbound calls, use `httpx.AsyncClient` inside an `async with` block, set an explicit timeout, and keep each request/response flow small and readable.
- When an upstream HTTP call fails, catch the specific `httpx.HTTPError` around the failing operation and re-raise `HTTPException(status_code=502, detail=...) from e` so FastAPI returns a clear gateway-style error with the original exception chain preserved.
- Raise `HTTPException` with appropriate status codes from route handlers, and keep `try`/`except` blocks tight so unrelated code is not accidentally masked.
- In SQLite-backed code, use `pathlib.Path` for DB paths, initialize schema in the existing startup pattern, open connections with `with sqlite3.connect(...) as conn`, and keep SQL operations local and explicit.
- Always use parameterized SQLite queries with `?` placeholders; never build SQL with f-strings, `%` formatting, or string concatenation.
- Use the standard `logging` module with `logging.basicConfig(...)`, keep a module logger, and emit operational messages with `log.info(...)`, `log.warning(...)`, or `log.error(...)` instead of `print(...)`.
- Prefer modern Python idioms: f-strings, comprehensions where they improve clarity, `with` blocks for files and network resources, and dataclasses or Pydantic models for structured data instead of ad-hoc dict juggling when the schema is stable.
- Avoid older or less safe patterns such as `%`-style string formatting, `os.path.join`, bare `open()` without a context manager, and broad exception handling that hides the failing line.
- Keep health checks and existing startup hooks intact: each service should continue to expose `@app.get("/health")`, and notifications-style services should preserve the `_init_db()` initialization flow unless the task explicitly changes startup behavior.
- Use pytest and pytest-asyncio for tests, run `pytest` from the service directory for Python service changes, and run `ruff check .` before submitting updates; if you add or change dependencies, update the relevant `pyproject.toml` in the same change.
- Make incremental, reviewable updates that match the existing FastAPI style, preserve current API behavior unless requirements change, and prefer existing standard-library/framework features over adding new packages.
