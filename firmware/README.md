# Sprout firmware

This folder holds the code for the Seeed XIAO ESP32-C3 board. It has three PlatformIO
environments (spec 7.9):

| Environment | What it is |
| --- | --- |
| `seeed_xiao_esp32c3` | The real stake firmware (`src/main.cpp`, `src/logic/`). The default. |
| `net_test` | The checkpoint A2 / gate G2 network test (`src/net_test/net_test.cpp`). A separate program. |
| `native` | Laptop tests for `src/logic/`. GitHub runs them on every pull request. |

## Running the G2 network test (Windows, VS Code + PlatformIO, no terminal)

The test connects to your WiFi, makes a real HTTPS POST every 60 seconds and prints how long
each step took (spec 14, G2). **G2 PASS** means the board had an IP address within 10 s and
the server replied with a 2xx status.

### 1. Open the firmware folder

In VS Code choose **File > Open Folder…** and pick the **`firmware`** folder inside Sprout
(not the whole Sprout folder). PlatformIO only finds the project when `platformio.ini` sits at
the top of the opened folder.

### 2. Make your secrets.h

WiFi names, passwords and the test address live in `include/secrets.h`. That file is never put
on GitHub (it's listed in `.gitignore`), so you make your own copy from the example:

1. In the Explorer panel on the left, open the `include` folder.
2. Right-click `secrets.example.h` and choose **Copy**.
3. Right-click the `include` folder and choose **Paste**. You get `secrets.example copy.h`.
4. Right-click the copy, choose **Rename**, and name it exactly `secrets.h`.
5. Open `secrets.h` and fill in, between the double quotes:
   - `WIFI_1_SSID` / `WIFI_1_PASSWORD`: your phone hotspot's name and password.
   - `WIFI_2_SSID` / `WIFI_2_PASSWORD`: your home WiFi.
   - `WIFI_3_SSID` / `WIFI_3_PASSWORD`: a spare network, or leave both as `""`.
   - `TEST_URL`: where the board sends its report. Easiest: open https://webhook.site in a
     browser, copy **Your unique URL**, and paste it here. Every report then shows up in
     that browser tab.
6. Save with **Ctrl+S**.

Never put real passwords in `secrets.example.h`: that file is on GitHub.

### 3. Pick the net_test environment

In the blue bar along the bottom of VS Code, click the environment name (it says
**Default (firmware)** at first) and choose **env:net_test** from the list at the top.

### 4. Upload

1. Plug the board in with a USB-C cable that carries data (some charging-only cables don't).
2. Click **Upload**: the right-pointing arrow (→) in the bottom bar. The first time, PlatformIO
   downloads its tools, which can take several minutes.
3. Wait for **SUCCESS** in the panel that opens.
4. Press the board's reset button (the tiny button marked **R**).

### 5. Open the Serial Monitor

Click the plug icon in the bottom bar (**Serial Monitor**). The speed (115200 baud) is set
for you. Within a minute you'll see something like:

```
========== G2 attempt 1  (uptime 5 s) ==========
[1/4] WiFi: looking for "My Hotspot" "Home WiFi" (give up after 20 s)
  Connected to "My Hotspot" in 3412 ms. IP 172.20.10.3, signal -52 dBm, channel 6
...
---- attempt 1 summary ----
  connect_ms    : 3412
  ...
G2 PASS
```

Each attempt ends with **G2 PASS** or **G2 FAIL:** and the reason. The `post_ms` of one
attempt goes into the next attempt's report, because the POST time is only known once its
reply has arrived. To run the test somewhere else, just unplug and replug the board there. It
keeps going every 60 seconds until it loses power.

For the G2 record (spec 14), run it on the hotspot in the classroom and on home WiFi, and copy
the summary lines into the shared log.

### If something goes wrong

- **The board only uses 2.4 GHz WiFi.** It can't see 5 GHz networks. On an **iPhone hotspot**,
  go to Settings > Personal Hotspot and turn on **Maximize Compatibility**. When it can't
  connect, the test lists every network the board *can* see, and marks yours with a `*`.
- **School logins and sign-in web pages don't work.** Only networks with a plain WiFi
  password (WPA2-Personal) work.
- **Windows shows "Device Descriptor Request Failed"** (or no port appears): unplug the board,
  hold down the **BOOT** button (marked **B**), plug it back in while still holding it, then let go.
  Click **Upload** again, and press the reset button (**R**) after the upload finishes.
- **The build fails with "secrets.h is missing":** step 2 wasn't finished. The file must be
  named exactly `secrets.h` and sit in the `include` folder.
- **"G2 FAIL: TLS connection failed":** the board couldn't check the server's certificate, or the
  network blocks HTTPS. Try another network or another `TEST_URL`.
- **Upload says the port is busy:** close the Serial Monitor (the bin icon on its panel) and upload again.

## For maintainers: the certificate bundle

`certs/x509_crt_bundle` holds Mozilla's root certificates in the format ESP-IDF 5.5 reads.
`net_test` embeds it so WiFiClientSecure can check any public HTTPS server's certificate
(certificate checking is never turned off). `certs/make_bundle.py` explains how to rebuild it
when the pinned platform moves to a new ESP-IDF version.
