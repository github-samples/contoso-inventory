package com.contoso.audit;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

/** Verifies the Spring application context loads without errors. */
@SpringBootTest
class AuditApplicationTests extends AuditTestSupport {
    @Test
    void contextLoads() {
    }
}
