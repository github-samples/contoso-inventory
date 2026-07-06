# AssetTrack architecture

AssetTrack is a teaching repo with seven services:

- `web` — Astro SSR UI and BFF
- `assets-svc` — .NET 8 asset CRUD/search API
- `workforce-svc` — Java 21 / Spring Boot 3 employee + assignment API
- `reporting-svc` — Python FastAPI reports + CSV import
- `notifications-svc` — Python FastAPI webhook receiver
- `audit-svc` — legacy Java 11 audit log
- `auth-svc` — legacy Java 11 JWT issuer

## Shared shape

- **Transport:** REST/JSON
- **Persistence:** mostly local SQLite per backend service
- **Frontend:** Astro SSR pages, server-side API calls, Bootstrap 5
- **Intent:** the repo includes deliberate gaps for modernization, validation, and security exercises

## `web`

- **Purpose:** dashboard, assets, employees, assignments, reports
- **Modules:** `src/pages/*`, `src/components/StatusBadge.astro`, `src/layouts/Layout.astro`, `src/lib/api/*`
- **Entry points:** `src/pages/index.astro`
- **Data layer:** no local DB; calls backend services through `src/lib/api/client.ts`
- **Templates:** Astro pages/components/layouts
- **Scripts:** `npm run dev`, `npm run build`, `npm run preview`, `npm run start`
- **Tech debt:** badge colors are wrong for `retired` and `lost`; new-asset form lacks validation; no assets-by-department page yet
- **Unenforced rules:** asset creation validation is intentionally missing end-to-end

## `assets-svc`

- **Purpose:** asset CRUD, search, stats
- **Modules:** `Program.cs`, `Data/AssetsDb.cs`, `Data/SeedData.cs`, `Endpoints/AssetEndpoints.cs`, `Models/Asset.cs`
- **Entry points:** `Program.cs`
- **Data layer:** SQLite + Dapper; schema and seed data are initialized at startup
- **Templates:** none
- **Scripts:** `dotnet run`, `dotnet test`
- **Tech debt:** `POST /assets` has no input validation; JWT validation is not wired here; seed data is intentionally messy
- **Unenforced rules:** required field and date validation are not enforced

## `workforce-svc`

- **Purpose:** employee and assignment management
- **Modules:** `employee/*`, `assignment/*`, `HealthController`, `HttpClientsConfig`, `WorkforceApplication`
- **Entry points:** `WorkforceApplication.main`
- **Data layer:** Spring Data JPA + Hibernate over SQLite; initial rows come from `src/main/resources/data.sql`
- **Templates:** none
- **Scripts:** `./mvnw spring-boot:run`, `mvn spring-boot:run`, `mvn test`
- **Tech debt:** no audit POST yet; notification webhook errors are swallowed; one outbound `RestClient` for audit exists but is unused
- **Unenforced rules:** inactive employees can still receive assets; `returnedDate` is not validated against `assignedDate`

## `reporting-svc`

- **Purpose:** warranty/utilization reports and CSV bulk import
- **Modules:** `app/main.py`, `app/routers/reports.py`, `app/routers/imports_.py`, `app/legacy/format_helpers.py`
- **Entry points:** `app/main.py`
- **Data layer:** no primary DB; reads live from `assets-svc` and `workforce-svc`
- **Templates:** none
- **Scripts:** `pip install -e ".[dev]"`, `uvicorn app.main:app --reload`
- **Tech debt:** legacy helper style remains on purpose; test suite is intentionally empty; import path lacks robust error handling
- **Unenforced rules:** malformed CSV rows crash the whole import

## `notifications-svc`

- **Purpose:** webhook receiver that stubs email/Slack delivery
- **Modules:** `app/main.py`
- **Entry points:** `app/main.py`
- **Data layer:** local SQLite `events` table via `sqlite3`
- **Templates:** none
- **Scripts:** `uvicorn app.main:app --reload`
- **Tech debt:** synchronous best-effort delivery only; no retry/queue/dead-letter mechanism
- **Unenforced rules:** webhook delivery resilience is intentionally absent

## `audit-svc`

- **Purpose:** append-only audit log
- **Modules:** `AuditApplication`, `AuditController`, `AuditRepository`, `DataInit`
- **Entry points:** `AuditApplication.main`
- **Data layer:** raw JDBC over SQLite; schema and seed events are created in `DataInit`
- **Templates:** none
- **Scripts:** `mvn spring-boot:run`
- **Tech debt:** SQL injection in search; no tests; legacy Spring Boot 2.7 / Java 11
- **Unenforced rules:** workforce is not yet posting events here

## `auth-svc`

- **Purpose:** JWT issuer and user lookup
- **Modules:** `AuthApplication`, `TokenController`, `JwtIssuer`, `UserRepository`, `DataInit`
- **Entry points:** `AuthApplication.main`
- **Data layer:** raw JDBC over SQLite; schema and seed users are created in `DataInit`
- **Templates:** none
- **Scripts:** `mvn spring-boot:run`
- **Tech debt:** SQL injection in username lookup; plain-text seeded passwords; no tests; legacy Spring Boot 2.7 / Java 11
- **Unenforced rules:** authentication data is intentionally insecure for course material
