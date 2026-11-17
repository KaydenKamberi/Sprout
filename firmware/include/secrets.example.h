// Template for secrets.h, used by the net_test program (checkpoint A2 / gate G2).
//
// 1. Copy this file into the same folder (firmware/include/) and name the copy secrets.h.
// 2. Put your real values in secrets.h, not here.
// 3. secrets.h is listed in .gitignore, so it never goes into the repository.
//    This example file IS in the repository: never put a real password in it.
//
// Every value goes between the double quotes. Names and passwords are case-sensitive.

#pragma once

// ---------- WiFi networks (up to 3) ----------
// The board tries whichever of these it can see (spec 7.8).
// - 2.4 GHz WPA2-Personal only. 5 GHz networks are invisible to the board, and school
//   logins or sign-in web pages (captive portals) do not work.
// - iPhone hotspot: Settings > Personal Hotspot > turn on "Maximize Compatibility".
// - Leave a slot as "" (empty) if you don't need it.

// Network 1: Kayden's phone hotspot (the classroom network)
#define WIFI_1_SSID     "Example-Hotspot"
#define WIFI_1_PASSWORD "example-password-1"

// Network 2: Kayden's home WiFi (used over school breaks)
#define WIFI_2_SSID     "Example-Home-WiFi"
#define WIFI_2_PASSWORD "example-password-2"

// Network 3: a spare network, or leave both empty
#define WIFI_3_SSID     ""
#define WIFI_3_PASSWORD ""

// ---------- Test endpoint ----------
// The full https:// address the board sends its test report (an HTTPS POST) to.
// It must accept a POST with a JSON body and reply with a 2xx status, for example:
// - a webhook.site address: open https://webhook.site in a browser, copy "Your unique URL",
//   and every report then appears in that browser tab;
// - https://httpbin.org/post, which simply echoes the report back.
// At A9a this becomes the live Sprout server.
#define TEST_URL "https://webhook.site/00000000-0000-0000-0000-000000000000"
