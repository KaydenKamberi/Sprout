// Sprout network test program: checkpoint A2, gate G2 (spec 3.5, 7.4, 7.8, 7.9, 14).
//
// NOT the stake firmware. It lives in its own PlatformIO environment (env:net_test) and
// only proves the board can reach the internet over the real networks:
//   G2 passes when the board has an IP within 10 s AND a real HTTPS POST gets a 2xx reply.
// Connect, DNS, TLS and POST times are recorded for the power budget.
//
// Every 60 s, forever:
//   1. WiFiMulti connects to whichever network from secrets.h is visible (give up after 20 s).
//   2. DNS lookup of the test URL's host.
//   3. TLS connection, checking the server's certificate against the root bundle.
//   4. HTTPS POST of a JSON report; timed until the response arrives.
//   5. Summary and "G2 PASS" or "G2 FAIL: <reason>" on the serial monitor (115200 baud).
//   6. WiFi off until the next attempt.
//
// Setup and use: firmware/README.md.

#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WiFiMulti.h>
#include <lwip/dns.h>
#include <lwip/tcpip.h>

#if __has_include("secrets.h")
#include "secrets.h"
#else
#error "firmware/include/secrets.h is missing. Copy include/secrets.example.h to include/secrets.h and fill it in (see firmware/README.md)."
#endif

// Unused network slots may be left out of secrets.h.
#ifndef WIFI_2_SSID
#define WIFI_2_SSID ""
#define WIFI_2_PASSWORD ""
#endif
#ifndef WIFI_3_SSID
#define WIFI_3_SSID ""
#define WIFI_3_PASSWORD ""
#endif

// ---------- constants (spec 14 G2, 16.1) ----------
static const uint32_t ATTEMPT_PERIOD_MS = 60000;  // one attempt every 60 s, start to start
static const uint32_t WIFI_TIMEOUT_MS = 20000;    // WIFI_TIMEOUT_S, placeholder 20 s
static const uint32_t IP_PASS_MS = 10000;         // G2: IP within 10 s
static const uint32_t HTTP_TIMEOUT_MS = 15000;    // HTTP_TIMEOUT_S, placeholder 15 s
static const uint32_t FIRST_ATTEMPT_DELAY_MS = 5000;  // time to open the serial monitor
static const size_t REPLY_PRINT_MAX = 300;        // characters of the server reply to show

// Root certificate bundle (Mozilla roots), embedded by board_build.embed_files in
// platformio.ini. Built by certs/make_bundle.py.
extern const uint8_t ROOT_BUNDLE_START[] asm("_binary_certs_x509_crt_bundle_start");
extern const uint8_t ROOT_BUNDLE_END[] asm("_binary_certs_x509_crt_bundle_end");

struct Network {
    const char *ssid;
    const char *password;
};

static const Network NETWORKS[] = {
    {WIFI_1_SSID, WIFI_1_PASSWORD},
    {WIFI_2_SSID, WIFI_2_PASSWORD},
    {WIFI_3_SSID, WIFI_3_PASSWORD},
};
static const size_t NETWORK_SLOTS = sizeof(NETWORKS) / sizeof(NETWORKS[0]);

static WiFiMulti wifiMulti;
static String setupError;  // empty = secrets.h looks usable
static String testHost;
static uint16_t testPort = 443;
static uint32_t attempt = 0;
static uint32_t nextAttemptAt = 0;
static long previousPostMs = -1;  // post_ms of the previous attempt; -1 = not known

// ---------- helpers ----------

static const char *wifiStatusName(wl_status_t s) {
    switch (s) {
        case WL_IDLE_STATUS: return "idle";
        case WL_NO_SSID_AVAIL: return "no listed network visible";
        case WL_SCAN_COMPLETED: return "scan completed";
        case WL_CONNECTED: return "connected";
        case WL_CONNECT_FAILED: return "connect failed (wrong password?)";
        case WL_CONNECTION_LOST: return "connection lost";
        case WL_DISCONNECTED: return "disconnected";
        default: return "unknown";
    }
}

// Splits "https://host[:port]/path" into host and port. Only https is accepted.
static bool parseHttpsUrl(const char *url, String &host, uint16_t &port) {
    const char *prefix = "https://";
    if (strncmp(url, prefix, strlen(prefix)) != 0) return false;
    const char *p = url + strlen(prefix);
    const char *end = p;
    while (*end && *end != '/' && *end != ':' && *end != '?' && *end != '#') end++;
    if (end == p) return false;
    host = String(p).substring(0, end - p);
    port = 443;
    if (*end == ':') {
        long n = strtol(end + 1, nullptr, 10);
        if (n <= 0 || n > 65535) return false;
        port = (uint16_t)n;
    }
    return true;
}

// Empties lwIP's DNS cache so every attempt does a real lookup, like a stake waking from
// deep sleep. Runs on the lwIP thread; it finishes long before the DNS step.
static void clearDnsCache() {
    tcpip_callback([](void *) { dns_clear_cache(); }, nullptr);
}

static void printVisibleNetworks() {
    Serial.println("  Scanning to show what the board can see (2.4 GHz only)...");
    int n = WiFi.scanNetworks();
    if (n <= 0) {
        Serial.println("  No networks visible at all.");
        return;
    }
    Serial.printf("  %d network(s) visible:\n", n);
    for (int i = 0; i < n; i++) {
        bool listed = false;
        for (size_t k = 0; k < NETWORK_SLOTS; k++) {
            if (NETWORKS[k].ssid[0] && WiFi.SSID(i) == NETWORKS[k].ssid) listed = true;
        }
        Serial.printf("    %s\"%s\"  %d dBm  channel %ld\n", listed ? "* " : "  ",
                      WiFi.SSID(i).c_str(), (int)WiFi.RSSI(i), (long)WiFi.channel(i));
    }
    Serial.println("  (* = in secrets.h)");
    WiFi.scanDelete();
}

static void wifiOff() {
    WiFi.disconnect(true, false);
    WiFi.mode(WIFI_OFF);
}

static void printSummary(const String &network, int rssi, long connectMs, bool ipWithin10s,
                         long dnsMs, long tlsMs, long postMs, int httpStatus) {
    auto ms = [](long v) { return v < 0 ? String("-") : String(v); };
    Serial.printf("\n---- attempt %lu summary ----\n", (unsigned long)attempt);
    Serial.printf("  network       : %s\n", network.length() ? network.c_str() : "-");
    Serial.printf("  rssi_dbm      : %s\n", network.length() ? String(rssi).c_str() : "-");
    Serial.printf("  connect_ms    : %s\n", ms(connectMs).c_str());
    Serial.printf("  ip_within_10s : %s\n", ipWithin10s ? "true" : "false");
    Serial.printf("  dns_ms        : %s\n", ms(dnsMs).c_str());
    Serial.printf("  tls_ms        : %s\n", ms(tlsMs).c_str());
    Serial.printf("  post_ms       : %s  (sent in the next attempt's body)\n", ms(postMs).c_str());
    Serial.printf("  http_status   : %s\n", httpStatus > 0 ? String(httpStatus).c_str() : "-");
    Serial.printf("  uptime_s      : %lu\n", (unsigned long)(millis() / 1000));
}

// ---------- one attempt ----------

static void runAttempt() {
    attempt++;
    long connectMs = -1, dnsMs = -1, tlsMs = -1, postMs = -1;
    int httpStatus = 0;
    bool ipWithin10s = false;
    String network;
    int rssi = 0;
    String failure;  // empty = pass

    Serial.printf("\n========== G2 attempt %lu  (uptime %lu s) ==========\n",
                  (unsigned long)attempt, (unsigned long)(millis() / 1000));

    // 1. WiFi
    Serial.printf("[1/4] WiFi: looking for");
    for (size_t k = 0; k < NETWORK_SLOTS; k++) {
        if (NETWORKS[k].ssid[0]) Serial.printf(" \"%s\"", NETWORKS[k].ssid);
    }
    Serial.printf(" (give up after %lu s)\n", (unsigned long)(WIFI_TIMEOUT_MS / 1000));

    WiFi.mode(WIFI_STA);
    clearDnsCache();
    uint32_t start = millis();
    wl_status_t status = WL_DISCONNECTED;
    while (millis() - start < WIFI_TIMEOUT_MS) {
        uint32_t left = WIFI_TIMEOUT_MS - (millis() - start);
        status = (wl_status_t)wifiMulti.run(left);
        if (status == WL_CONNECTED) break;  // WL_CONNECTED means the board has an IP
        delay(50);
    }
    if (status != WL_CONNECTED) {
        Serial.printf("  No connection after %lu ms (last WiFi status: %s)\n",
                      (unsigned long)(millis() - start), wifiStatusName(status));
        printVisibleNetworks();
        failure = "no listed network connected within 20 s (" + String(wifiStatusName(status)) + ")";
    } else {
        connectMs = millis() - start;
        ipWithin10s = connectMs <= (long)IP_PASS_MS;
        network = WiFi.SSID();
        rssi = WiFi.RSSI();
        Serial.printf("  Connected to \"%s\" in %ld ms. IP %s, signal %d dBm, channel %ld\n",
                      network.c_str(), connectMs, WiFi.localIP().toString().c_str(), rssi,
                      (long)WiFi.channel());
        Serial.printf("  IP within 10 s: %s\n", ipWithin10s ? "yes" : "NO");
    }

    // 2. DNS
    IPAddress serverIp;
    if (failure.isEmpty()) {
        Serial.printf("[2/4] DNS: looking up %s\n", testHost.c_str());
        uint32_t t = millis();
        int ok = WiFi.hostByName(testHost.c_str(), serverIp);
        dnsMs = millis() - t;
        if (ok != 1 || serverIp == IPAddress()) {
            Serial.printf("  Lookup failed after %ld ms\n", dnsMs);
            failure = "DNS lookup of " + testHost + " failed";
        } else {
            Serial.printf("  %s -> %s in %ld ms\n", testHost.c_str(), serverIp.toString().c_str(), dnsMs);
        }
    }

    // 3. TLS (certificate checked against the root bundle; never insecure)
    WiFiClientSecure client;
    client.setCACertBundle(ROOT_BUNDLE_START, ROOT_BUNDLE_END - ROOT_BUNDLE_START);
    client.setConnectionTimeout(HTTP_TIMEOUT_MS);
    client.setHandshakeTimeout(HTTP_TIMEOUT_MS / 1000);
    if (failure.isEmpty()) {
        Serial.printf("[3/4] TLS: connecting to %s:%u and checking its certificate\n", testHost.c_str(), testPort);
        uint32_t t = millis();
        // Connect by the IP we just looked up, giving the host name for SNI and the
        // certificate name check, so tls_ms does not include a second DNS lookup.
        int ok = client.connect(serverIp, testPort, testHost.c_str(), nullptr, nullptr, nullptr);
        tlsMs = millis() - t;
        if (!ok) {
            char err[120] = "";
            client.lastError(err, sizeof(err));
            Serial.printf("  TLS failed after %ld ms: %s\n", tlsMs, err);
            failure = "TLS connection failed (" + String(err) + ")";
        } else {
            Serial.printf("  Secure connection up, certificate valid, in %ld ms\n", tlsMs);
        }
    }

    // 4. HTTPS POST
    if (failure.isEmpty()) {
        JsonDocument doc;
        doc["test"] = "G2";
        doc["network"] = network;  // the network's name only, never its password
        doc["rssi_dbm"] = rssi;
        doc["connect_ms"] = connectMs;
        doc["dns_ms"] = dnsMs;
        doc["tls_ms"] = tlsMs;
        if (previousPostMs >= 0) {
            doc["post_ms"] = previousPostMs;  // the previous attempt's POST time
        } else {
            doc["post_ms"] = nullptr;  // first attempt, or the previous POST got no reply
        }
        doc["ip_within_10s"] = ipWithin10s;
        doc["uptime_s"] = millis() / 1000;
        doc["attempt"] = attempt;
        String body;
        serializeJson(doc, body);

        Serial.println("[4/4] POST: sending");
        Serial.printf("  %s\n", body.c_str());

        HTTPClient https;
        https.setReuse(false);
        https.setConnectTimeout(HTTP_TIMEOUT_MS);
        https.setTimeout(HTTP_TIMEOUT_MS);
        if (!https.begin(client, TEST_URL)) {  // reuses the TLS connection from step 3
            failure = "could not start the HTTPS request (check TEST_URL)";
        } else {
            https.addHeader("Content-Type", "application/json");
            uint32_t t = millis();
            httpStatus = https.POST(body);
            uint32_t elapsed = millis() - t;
            if (httpStatus <= 0) {
                Serial.printf("  No reply after %lu ms: %s\n", (unsigned long)elapsed,
                              HTTPClient::errorToString(httpStatus).c_str());
                failure = "POST got no reply (" + HTTPClient::errorToString(httpStatus) + ")";
            } else {
                postMs = elapsed;
                String reply = https.getString();
                Serial.printf("  HTTP %d in %ld ms\n", httpStatus, postMs);
                if (reply.length() > REPLY_PRINT_MAX) reply = reply.substring(0, REPLY_PRINT_MAX) + "...";
                if (reply.length()) Serial.printf("  Reply: %s\n", reply.c_str());
                if (httpStatus < 200 || httpStatus > 299) {
                    failure = "server replied HTTP " + String(httpStatus) + " (needs 2xx)";
                }
            }
            https.end();
        }
    }
    client.stop();
    previousPostMs = postMs;

    // A slow connection fails G2 even when the POST worked.
    if (failure.isEmpty() && !ipWithin10s) {
        failure = "IP took " + String(connectMs) + " ms (limit 10000 ms)";
    } else if (!failure.isEmpty() && connectMs >= 0 && !ipWithin10s) {
        failure += "; IP also took " + String(connectMs) + " ms (limit 10000 ms)";
    }

    printSummary(network, rssi, connectMs, ipWithin10s, dnsMs, tlsMs, postMs, httpStatus);
    if (failure.isEmpty()) {
        Serial.println("G2 PASS");
    } else {
        Serial.printf("G2 FAIL: %s\n", failure.c_str());
    }

    // 6. WiFi off between attempts
    wifiOff();
}

// ---------- Arduino entry points ----------

void setup() {
    Serial.begin(115200);
    uint32_t waitStart = millis();
    while (!Serial && millis() - waitStart < 3000) delay(10);  // USB serial needs a moment

    Serial.println("\n\nSprout network test (checkpoint A2 / gate G2)");
    Serial.println("G2 passes when: IP within 10 s AND the HTTPS POST gets a 2xx reply.");

    size_t listed = 0;
    for (size_t k = 0; k < NETWORK_SLOTS; k++) {
        if (!NETWORKS[k].ssid[0]) continue;
        size_t len = strlen(NETWORKS[k].password);
        Serial.printf("  Network %u: \"%s\"%s\n", (unsigned)(k + 1), NETWORKS[k].ssid,
                      (len < 8 || len > 63) ? "  (WARNING: WPA2 passwords are 8 to 63 characters)" : "");
        wifiMulti.addAP(NETWORKS[k].ssid, NETWORKS[k].password);
        listed++;
    }

    bool urlOk = parseHttpsUrl(TEST_URL, testHost, testPort);
    if (urlOk) {
        Serial.printf("  Test URL host: %s, port %u\n", testHost.c_str(), testPort);
    }
    if (listed == 0) {
        setupError = "no networks in secrets.h (WIFI_1_SSID is empty)";
    } else if (!urlOk) {
        setupError = "TEST_URL in secrets.h must start with https:// and include a host name";
    }

    WiFi.persistent(false);  // never write network settings to flash
    WiFi.mode(WIFI_OFF);
    nextAttemptAt = millis() + FIRST_ATTEMPT_DELAY_MS;
    if (setupError.isEmpty()) {
        Serial.printf("First attempt in %lu s, then every %lu s.\n",
                      (unsigned long)(FIRST_ATTEMPT_DELAY_MS / 1000), (unsigned long)(ATTEMPT_PERIOD_MS / 1000));
    }
}

void loop() {
    if ((int32_t)(millis() - nextAttemptAt) < 0) {
        delay(100);
        return;
    }
    nextAttemptAt += ATTEMPT_PERIOD_MS;

    if (!setupError.isEmpty()) {  // repeated every 60 s in case the monitor was opened late
        Serial.printf("G2 FAIL: setup error: %s (see firmware/README.md)\n", setupError.c_str());
        return;
    }

    runAttempt();

    // If an attempt ran past the next start time, start the next one straight away.
    if ((int32_t)(millis() - nextAttemptAt) > 0) nextAttemptAt = millis();
    Serial.printf("WiFi off. Next attempt in %lu s.\n",
                  (unsigned long)((nextAttemptAt - millis()) / 1000));
}
