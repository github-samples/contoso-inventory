package com.contoso.audit;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class AuditControllerTest extends AuditTestSupport {

    @LocalServerPort
    int port;

    private RestClient rest() {
        return RestClient.create("http://localhost:" + port);
    }

    @Test
    void health_returnsOk() {
        ResponseEntity<Map> res = rest().get().uri("/health").retrieve().toEntity(Map.class);
        assertThat(res.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(res.getBody()).containsEntry("status", "ok").containsEntry("service", "audit-svc");
    }

    @Test
    void postThenGetEvents_roundTrips() {
        Map<String, String> body = Map.of(
                "actor", "tester", "action", "create", "entityType", "asset",
                "entityId", "CON-TST-001", "details", "created in test");
        ResponseEntity<Map> post = rest().post().uri("/events").body(body).retrieve().toEntity(Map.class);
        assertThat(post.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(((Number) post.getBody().get("id")).longValue()).isPositive();

        ResponseEntity<List> list = rest().get().uri("/events").retrieve().toEntity(List.class);
        assertThat(list.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(list.getBody()).isNotEmpty();
    }
}
