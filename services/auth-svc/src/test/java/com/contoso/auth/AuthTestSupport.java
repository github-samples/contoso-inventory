package com.contoso.auth;

import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import java.nio.file.Path;

/** Points the service at an isolated temp SQLite DB so tests never touch /data/auth.db. */
abstract class AuthTestSupport {
    static final Path DB = tempDb();

    private static Path tempDb() {
        try {
            Path dir = java.nio.file.Files.createTempDirectory("auth-test");
            return dir.resolve("auth.db");
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry registry) {
        registry.add("AUTH_DB_PATH", DB::toString);
    }
}
