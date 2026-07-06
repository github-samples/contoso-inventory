# Copilot instructions for AssetTrack

## Big picture

AssetTrack is a teaching-oriented polyglot microservices app for internal asset and employee assignment tracking.

- `web` is an Astro SSR frontend and BFF; it calls backend services server-side only.
- Most backend services own a local SQLite database.
- `reporting-svc` reads live data from other services and does not own a primary DB.
- `auth-svc` and `audit-svc` are intentionally legacy Java 11 / Spring Boot 2.7 services.
- All service-to-service traffic is REST/JSON.

## Commands

### Root

```bash
npm run dev
npm run dev:verbose
npm run install:all
docker compose up --build
```

### `web`

```bash
npm --prefix services/web run dev
npm --prefix services/web run build
npm --prefix services/web run preview
npm --prefix services/web run start
```

### `assets-svc`

```bash
dotnet run
dotnet test services/assets-svc/Tests/AssetsService.Tests.csproj
dotnet test services/assets-svc/Tests/AssetsService.Tests.csproj --filter FullyQualifiedName~AssetsDbTests
```

### `workforce-svc`

```bash
mvn spring-boot:run
mvn test
mvn -Dtest=WorkforceApplicationTests test
```

### `reporting-svc`

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8080
ruff check .
```

### `notifications-svc`

```bash
pip install -e services/notifications-svc
uvicorn app.main:app --reload --port 8080
```

### `audit-svc` and `auth-svc`

```bash
mvn spring-boot:run
```

## Conventions

- Keep Astro data fetching on the server; use `services/web/src/lib/api/client.ts` and env vars rather than browser-side service calls.
- `web` resolves service URLs from `process.env`, not `import.meta.env`, so container runtime values work correctly.
- `assets-svc` is a .NET 8 minimal-API app; startup initializes the SQLite schema/seed data and exposes Swagger.
- Spring services use a thin controller/service/repository split; business rules live in services, not controllers.
- `workforce-svc` keeps the one-active-assignment-per-asset rule, but some other rules are intentionally left unenforced for exercises.
- Python services organize FastAPI routers under `app/routers/`; `reporting-svc` uses routers plus module-level service URLs.
- Legacy Java services use raw JDBC and seeded SQLite data in `DataInit`; their insecure patterns are intentional teaching targets.
- Several gaps are deliberate course exercises; check `README.md`, service READMEs, and `exercises.md` before "fixing" something that is meant to stay broken.
