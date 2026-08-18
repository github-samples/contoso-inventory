# Java modernization playbook

> A reusable recipe for bringing an AssetTrack Java service current — from Spring Boot 3.5 / Java 17 to Spring Boot 4.1 / Java 21. Distilled from modernizing `audit-svc` and `auth-svc`. Use it with the `Java migrator` agent.

## The loop

Assess → Plan → Protect → Migrate → Validate → Document. An agent changes the speed of each step, not the need for it.

## Recipe

1. **Assess.** Confirm the current stack (`pom.xml` parent + `java.version`), the dependency surface, and how the service touches JSON. Boot 4 makes **Jackson 3** (`tools.jackson`) the default and no longer manages Jackson 2, so any library that carries its own Jackson 2 (e.g. `jjwt-jackson`) needs attention. Use the LSP (`.github/lsp.json` → `jdtls`) for precise caller/symbol lookups rather than text search.
2. **Plan.** Target the current supported baseline (`spring-boot-starter-parent` `4.1.0`, `java.version` `21`) rather than a generic "4.x". Pin the BOM-managed libraries that ship a still-vulnerable patch to a CVE-clean one (`jackson-bom.version` → Jackson 3 `3.1.6`; `log4j2.version` → `2.25.5`). Keep the plan phased so each step is independently verifiable and revertible.
3. **Protect — build the safety net first.** Add `spring-boot-starter-test` (`test` scope) and characterization tests *before* touching the framework: a `@SpringBootTest` context-load test, endpoint contract tests, and (for `auth-svc`) a token round-trip. Point them at an **isolated temporary SQLite database** (never `/data/*.db`). Note the Boot 4 test-API relocation: `TestRestTemplate` / `LocalServerPort` moved, so prefer `@LocalServerPort` + `RestClient`. Confirm green on the *old* (3.5 / 17) stack first.
4. **Migrate in order.**
   - Phase 1 — toolchain: `java.version` `17` → `21`; bump the Dockerfile base images `temurin-17` → `temurin-21`.
   - Phase 2 — framework: `spring-boot-starter-parent` `3.5.16` → `4.1.0`; add the Jackson 3 / Log4j2 currency pins.
   - Phase 3 — reconcile dependencies. Jackson 3 serializes the controllers' `Map`/`List` responses with **no** source change. For `jjwt`, bump `0.11.5` → `0.12.7` (the fluent builder API: `.issuer()/.subject()/.signWith(key, Jwts.SIG.RS256)`) and swap the serializer `jjwt-jackson` → `jjwt-gson` so JWT (de)serialization stays off Jackson 2, which Boot 4 no longer manages.
5. **Validate after every phase.** `mvn verify` from the service directory; the same test count must stay green. Run the Playwright e2e suite as the final cross-system gate. Wire the service into `.github/hooks/scripts/test-router.sh` so edits trigger its tests.
6. **Document.** Update this playbook and the `Java migrator` agent with anything the upgrade taught you, so the next service is a repeat rather than a fresh start.

## Lessons from the two services

- **`audit-svc`** was the clean case: raw `JdbcTemplate`, no direct Jackson use, three dependencies. Two `pom.xml` edits (parent + `java.version`) plus the currency pins and the test starter, and a Dockerfile bump. Jackson 3 handled its `Map`/`List` JSON with zero source changes. Tests green on 4.1.0 / 21.
- **`auth-svc`** is where the second-service value showed up: it issues JWTs with `jjwt`. Boot 4 stops managing Jackson 2, so `jjwt-jackson` would drag in an old, vulnerable `jackson-databind`. The fix is two concrete moves — migrate `JwtIssuer` to the jjwt `0.12.x` fluent API, and swap `jjwt-jackson` → `jjwt-gson` to drop Jackson 2 entirely. A red test after the bump is the safety net doing its job. Tests green on 4.1.0 / 21.

## Explicitly out of scope for a framework bump

- Introducing Spring Data JPA / Hibernate (separate project, own branch).
- Fixing the intentional SQL-injection course-exercise code in the repositories (track separately).
- Hardening SQLite pool behavior beyond test isolation (evaluate under load, separately).
