# Migration plan: `audit-svc` from Spring Boot 3.5.16 / Java 17 to Spring Boot 4.1.0 / Java 21

## 1. Executive summary

`audit-svc` is a small, append-only audit-log microservice currently on Spring Boot `3.5.16` / Java `17` — CVE-clean, but a Spring Boot generation and an LTS behind the team's current target. Its sibling `workforce-svc` runs the modern Boot 3.5 / Java 21 baseline, and the goal here is to bring `audit-svc` (and then `auth-svc`) fully current on **Spring Boot 4.1.0 / Java 21**. `audit-svc` uses only `spring-boot-starter-web`, `spring-boot-starter-jdbc`, raw `JdbcTemplate`, and `sqlite-jdbc` — no JPA, no Hibernate, and no direct Jackson use — so its migration surface is unusually narrow. The plan isolates the work into sequential phases — baseline safety net, toolchain alignment, framework bump, and dependency reconciliation — so each phase can be verified and rolled back independently.

## 2. Target stack (pinned, CVE-clean today)

| Coordinate | Before | After |
| --- | --- | --- |
| `spring-boot-starter-parent` | `3.5.16` | `4.1.0` |
| `java.version` | `17` | `21` |
| Jackson | 2.x (managed) | **Jackson 3** (`tools.jackson`), pinned `jackson-bom.version` = `3.1.6` |
| Log4j2 API | `2.25.5` | `2.25.5` (pin retained: Boot 4.1.0 manages `2.25.4`, which is vulnerable) |
| Dockerfile base | `eclipse-temurin-17` | `eclipse-temurin-21` |

Boot 4.1.0 natively resolves Jackson 3 `3.1.4` and Log4j2 `2.25.4`, both of which carry a known CVE today; the two pins hold them at CVE-clean `3.1.6` / `2.25.5`. Spring Framework `7.0.8`, Tomcat `11.0.22`, snakeyaml, and HikariCP resolve clean at Boot 4.1.0 with no pin.

## 3. Jackson 3 reconciliation

Spring Boot 4 makes **Jackson 3** (package `tools.jackson`, immutable `JsonMapper`) the default and no longer manages Jackson 2. `audit-svc` returns `Map`/`List` from its `@RestController` methods and imports no Jackson types, so Spring MVC serializes them under Jackson 3 with **zero source changes**. (The coupling that does matter — a library carrying its own Jackson 2 — shows up in `auth-svc`, whose `jjwt-jackson` is swapped for `jjwt-gson`; see the playbook.)

## 4. Phases

- **Phase 0 — safety net.** Add `spring-boot-starter-test` (`test` scope) and characterization tests on the current 3.5.16 / 17 stack: a `@SpringBootTest` context-load test and `@LocalServerPort` + `RestClient` endpoint tests, pointed at an isolated temp SQLite DB. Confirm green before touching the runtime.
- **Phase 1 — Java 17 → 21.** Bump `<java.version>` to `21` and the Dockerfile bases `temurin-17` → `temurin-21`. Re-run the Phase 0 tests.
- **Phase 2 — Boot 3.5.16 → 4.1.0.** Bump the parent, add `<jackson-bom.version>3.1.6</jackson-bom.version>` and keep `<log4j2.version>2.25.5</log4j2.version>`. Note the Boot 4 test-API relocation (`TestRestTemplate`/`LocalServerPort` moved) — the Phase 0 tests already use `RestClient` to avoid it.
- **Phase 3 — validate.** `mvn verify` green; confirm the resolved tree is OSV-clean; run the Playwright e2e suite as the cross-system gate.

## 5. Risks

| Risk | Mitigation |
| --- | --- |
| Boot 4.1.0 ships a vulnerable Jackson 3 (`3.1.4`) / Log4j2 (`2.25.4`) | Explicit `jackson-bom.version` / `log4j2.version` pins; re-scan the resolved tree with OSV. |
| Boot 4 test-API relocation breaks characterization tests | Use `@LocalServerPort` + `RestClient` instead of the moved `TestRestTemplate`. |
| Behavior drift across the major bump | Characterization tests written and green on 3.5.16 / 17 first, held constant across the bump. |

## 6. Out of scope

Introducing Spring Data JPA / Hibernate; fixing the intentional SQL-injection course-exercise code; SQLite pool hardening beyond test isolation. Each is tracked separately.
