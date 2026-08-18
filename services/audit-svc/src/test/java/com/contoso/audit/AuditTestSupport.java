package com.contoso.audit;

import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import java.nio.file.Path;

/** Points the service at an isolated temp SQLite DB so tests never touch /data/audit.db. */
abstract class AuditTestSupport {
    static final Path DB = tempDb();

    private static Path tempDb() {
        try {
            Path dir = java.nio.file.Files.createTempDirectory("audit-test");
            return dir.resolve("audit.db");
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry registry) {
        registry.add("AUDIT_DB_PATH", DB::toString);
    }
}
