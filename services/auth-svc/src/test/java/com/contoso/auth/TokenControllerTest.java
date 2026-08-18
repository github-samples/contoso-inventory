package com.contoso.auth;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestClient;

import java.util.Base64;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class TokenControllerTest extends AuthTestSupport {

    @LocalServerPort
    int port;

    private RestClient rest() {
        return RestClient.create("http://localhost:" + port);
    }

    @Test
    void token_issuesJwt_viaGsonSerializer() {
        ResponseEntity<Map> res = rest().post().uri("/token")
                .body(Map.of("username", "admin", "password", "password"))
                .retrieve().toEntity(Map.class);
        assertThat(res.getStatusCode()).isEqualTo(HttpStatus.OK);
        String jwt = (String) res.getBody().get("access_token");
        assertThat(jwt).isNotBlank();

        // A signed JWT is header.payload.signature; decode the payload to prove the
        // jjwt-gson serializer emitted the claims (the Jackson-2-free path under Boot 4).
        String[] parts = jwt.split("\\.");
        assertThat(parts).hasSize(3);
        String payload = new String(Base64.getUrlDecoder().decode(parts[1]));
        assertThat(payload).contains("\"sub\":\"admin\"").contains("\"role\":\"admin\"");
    }

    @Test
    void badCredentials_returns401() {
        HttpStatusCode status = rest().post().uri("/token")
                .body(Map.of("username", "admin", "password", "wrong"))
                .exchange((req, res) -> res.getStatusCode());
        assertThat(status).isEqualTo(HttpStatus.UNAUTHORIZED);
    }

    @Test
    void jwks_exposesKey() {
        ResponseEntity<Map> res = rest().get().uri("/.well-known/jwks").retrieve().toEntity(Map.class);
        assertThat(res.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(res.getBody()).containsKey("keys");
    }
}
