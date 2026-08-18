package com.contoso.auth;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

/** Verifies the context loads (including @PostConstruct RSA key init). */
@SpringBootTest
class AuthApplicationTests extends AuthTestSupport {
    @Test
    void contextLoads() {
    }
}
