---
applyTo: "services/assets-svc/**/*.cs"
description: This file describes instructions for the .NET 8 assets service code style and engineering practices for the project.
---

- Follow standard C# naming conventions — Use PascalCase for types, methods, and properties, camelCase for locals and parameters, UPPER_SNAKE_CASE only for constants when needed, and keep file names aligned to the primary type they define.
- Use file-scoped namespaces that match the `Contoso.Assets` root namespace (for example, `namespace Contoso.Assets.Endpoints;`) and keep related types in the appropriate `Data/`, `Endpoints/`, or `Models/` folder.
- Honor nullable reference types everywhere — Mark optional reference values with `?`, initialize non-null properties explicitly, and do not use the null-forgiving operator (`!`) unless there is no better option and the reason is documented in a comment.
- Keep minimal API wiring in endpoint extension classes — Add related routes through `public static` extension methods on `IEndpointRouteBuilder`, organize them with `MapGroup(...)`, and keep request handlers as private static methods that return `IResult`.
- Return HTTP results intentionally — Use `Results.Ok(...)`, `Results.Created(...)`, `Results.NotFound()`, and `Results.NoContent()` as appropriate, and prefer explicit not-found and no-content responses over letting endpoint exceptions escape.
- Use Dapper with parameterized SQL only — Pass values through anonymous objects or `DynamicParameters`, use `@param` placeholders, and never concatenate user-controlled input into SQL statements.
- Open SQLite connections through `AssetsDb` with `using var conn = db.Open();` so every handler gets a fresh `SqliteConnection` and disposes it promptly.
- Keep persistence concerns in `AssetsDb` and endpoint/query code — Use `AssetsDb` for connection management and initialization, and preserve the existing Dapper + `Microsoft.Data.Sqlite` approach instead of introducing Entity Framework or other ORM abstractions.
- Keep read models and write/input models separate — Place models under `Models/`, use dedicated input types like `AssetCreate` for request bodies, and keep optional request fields as nullable `string?` values when the API accepts missing data.
- Preserve course-exercise gaps unless the task explicitly changes them — `AssetCreate` intentionally allows incomplete or invalid input today, so do not add blanket rules or generated code that assume validation is always required.
- Register dependencies with `builder.Services` and resolve them from DI — Prefer singleton registration for stateless infrastructure such as `AssetsDb`, and do not instantiate shared dependencies directly inside handlers when DI can provide them.
- Read runtime configuration from `Environment.GetEnvironmentVariable(...)` with sensible fallback defaults, including `ASSETS_DB_PATH` for the SQLite file location, and avoid hard-coded environment-specific paths or service URLs.
- Keep `Program.cs` compatible with the existing host/test setup — Preserve Swagger registration, keep startup focused on wiring and initialization, and retain `public partial class Program { }` at the bottom so `WebApplicationFactory`-based tests continue to work.
- Keep changes incremental and dependency-light — Make focused updates that fit the minimal API structure already in place, avoid adding new NuGet packages unless the task requires them, and validate changes with `dotnet test services/assets-svc/Tests/AssetsService.Tests.csproj` when behavior is affected.
