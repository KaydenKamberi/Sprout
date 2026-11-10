# Sprout Master Specification v3

Nov 3, 2026 · @Kayden

## 0. How to read this document

This is the build specification for Sprout: everything gets built from this document. It merges two earlier specs, and as of 3 Nov 2026 the team has settled all 33 points where they disagreed; the last, DEC-33 (who owns which track), was settled on 5 Nov.

| Short name | Source | Author | Date | Role now |
| --- | --- | --- | --- | --- |
| v2 | Sprout Build Specification v2 | Kayden | 21 Oct 2026 | Kept as documentation only |
| Eli | Sprout Specification Rev. 117 | Eli | 26 Oct 2026 | Kept as documentation only |

Where either source disagrees with this document, this document wins (agreed 29 Oct).

### Labels used throughout

| Label | Meaning | What a builder or AI agent does |
| --- | --- | --- |
| **Decided (DEC-nn)** | The team chose this. Section 1 lists every decision | Build it exactly as written |
| **Placeholder** | A sensible value nobody has confirmed yet | Use it as written. Don't swap in a different value |
| **Measured (Gn)** | Only a bench test can produce the number | Use the stated stand-in until gate Gn records the real value |
| **Open Qn** | An unanswered question (section 17.2) | If its row in 17.2 names a placeholder, use that placeholder as written and flag it in the test log or pull request. If it names none, don't guess: stop and ask the question's owner |

### Numbering

- **Decisions:** DEC-01 to DEC-33, in section 1.
- **Open questions:** Q1–Q16 came from v2; Q17 onward were added during the merge. Numbers are never reused, and closed questions keep their number.
- **Checkpoints:** A (Device), B (Backend), C (Frontend), D (Design and QA), each with a due week, in section 3.
- **Test gates:** one list, G1 to G32, numbered so references stay stable (the Due column gives run order), in section 14.
- **Problems found and fixed during the merge:** V-, E- and R- numbers, in section 1A.

### Rules for AI coding agents

1. Section 8 (the API contract) is frozen once the contract-freeze milestone passes (Fri 13 Nov). Never rename, remove or retype a field on your own.
2. Never weaken a firmware safety limit (section 7.2) because a server value, a model output or a test asks for it.
3. Use Placeholder values exactly as written. If an Open question names a placeholder, use it and flag it. If something you need is missing, or is Open with no placeholder, stop and ask instead of inventing it.
4. Use the names in this document exactly: tables, columns, JSON fields, endpoints, constants and file paths.

## 1. Decision log

All 33 merge decisions are below with what was chosen and where it is built. All 33 are settled. "Hybrid" means the combined option recommended when the team discussed that decision. The arguments for every option are kept in this document's version history.

| ID | Decision | What was chosen (section) | Status |
| --- | --- | --- | --- |
| DEC-01 | Where the live server runs | An Oracle Cloud Always Free Arm virtual machine (Ubuntu, arm64), reached over HTTPS through a Cloudflare Tunnel (5). Replaced the Raspberry Pi on 9 Nov, when Pi prices made it too expensive (R-21) | A chosen (v2) |
| DEC-02 | Server language and framework | Python 3.12+ with FastAPI, SQLAlchemy 2, Pydantic v2, argon2-cffi, numpy and APScheduler, one language for API and model (10.9) | B chosen (Eli) |
| DEC-03 | Dashboard framework | React 18, Vite, TypeScript, React Router, TanStack Query and Recharts; styles in CSS files, no inline styles, no emojis (13) | B chosen (Eli) |
| DEC-04 | Firmware toolchain | PlatformIO with the Arduino-ESP32 core; logic that doesn't touch hardware is unit-tested on a laptop (7.9) | B chosen (Eli) |
| DEC-05 | When the stake uploads | A daily sync window: scans every 10 min from 11:30 to 12:40 local time, on Kayden's phone hotspot in period 4, or home WiFi over breaks (7.4) | A chosen (v2) |
| DEC-06 | Sync button | In. A button wakes the stake and forces a reading and a sync (6.2, 7.4) | A chosen (v2) |
| DEC-07 | Status LED | In. Shows ok, attention or fault on the stake. LED type is Q21, visibility rules Q26 (7.1) | A chosen (v2) |
| DEC-08 | Soil temperature sensor | Out. soil\_temp\_c stays in the contract, always null; the model uses light only (2.4) | B chosen (Eli) |
| DEC-09 | Final pin map | New map: button D2 (it can wake the chip), pump switch D10, float switch D7, LED D6, D8 and D9 left empty (6.2) | Other |
| DEC-10 | Battery divider | Two 1 MΩ resistors; the firmware doubles the reading (6.4) | B chosen (Eli) |
| DEC-11 | Pump runtime cap | A flat 15 s compiled into firmware; the server clamps to 15,000 ms and raises pump\_shortfall (7.2, 10.2) | B chosen (Eli) |
| DEC-12 | Water dose | target\_ml per plant, default 60 ml, adjusted after the first live week; pump time = target\_ml ÷ ml\_per\_s (10.2) | B chosen (Eli) |
| DEC-13 | Delivery check | About 45 min after a watering, moisture must have risen 3 points; two failures in a row stop automatic watering and raise an alert (7.1) | B chosen (Eli) |
| DEC-14 | Alert thresholds | Eli's battery, water and light rules; offline means more than 30 weekday hours without an upload (10.4) | Hybrid chosen |
| DEC-15 | Where calibration lives | Per plant on the server, sent in every config reply, with three guards: an input check, clearing on sensor change or reassignment, and the stake's live raw reading shown at setup (10.10) | Hybrid chosen |
| DEC-16 | Offline buffer | LittleFS files of 32-byte records; about 60 days of readings, oldest dropped first and counted; watering events kept separately and never overwritten (7.5) | Hybrid chosen |
| DEC-17 | Timestamps | Boot counter and seconds-since-boot on every item; the server back-dates at upload; "estimated" after 24 h without a clock sync (7.6) | B chosen (Eli) |
| DEC-18 | Device key | Authorization: Bearer header; the server stores only a hash (8.7) | B chosen (Eli) |
| DEC-19 | Upload fields | The combined set (8.1) | Hybrid chosen |
| DEC-20 | Config reply fields | The combined set, including the sync-window fields (8.2) | Hybrid chosen |
| DEC-21 | Linking a stake to an account | A script and USB tool create the stake and a claim code; the claim flow sets the owner; the Devices page manages it (8.5) | Hybrid chosen |
| DEC-22 | Endpoints | Both sets combined, using /refill (8.4) | Hybrid chosen |
| DEC-23 | Tables | Eli's definitions plus v2's additions; the config is computed on each upload, not stored (9) | Hybrid chosen |
| DEC-24 | When learning starts | A simple average from 3 valid cycles, blended with the species default; the light model replaces it only once it predicts better (11.3) | Hybrid chosen |
| DEC-25 | Interval safety factor | 0.75 × effective interval, clamped to 12–720 h, changing at most 25% per refit (11.3) | Hybrid chosen |
| DEC-26 | Model evaluation | Walk-forward from the sixth valid cycle; mean absolute error in hours against the species default (11.5) | B chosen (Eli) |
| DEC-27 | Diagnosis output | Ten fixed conditions with a self-check and no confidence score; species passed in; swappable provider (12) | Hybrid chosen |
| DEC-28 | Diagnosis priority | Optional. Built after B11 and first to cut; the learning model alone meets the AI requirement (Mr. Benrud, 29 Oct) (12) | Hybrid chosen |
| DEC-29 | Charging and reflashing | A waterproof USB-C port for routine charging and flashing; a screwed, gasketed lid only for battery swaps (6.7) | Hybrid chosen |
| DEC-30 | Light sensor placement | Under a glass slide in the lid, facing up; G25 checks for shading (6.8) | A chosen (v2) |
| DEC-31 | Timeline | Real dates worked back from a demo on Fri 14 May 2027; milestones dated, checkpoints by week; plant in Fri 18 Dec and home with Kayden over breaks; break dates checked against the district calendar on 5 Nov; demo date still a placeholder (4) | Other |
| DEC-32 | Gate list | One list, G1–G32, numbered for stable references (the Due column gives run order); the plant goes in only after G20 (14) | Hybrid chosen |
| DEC-33 | Who owns what | Leads named 5 Nov: Eli (Backend), Ca'Marion (Frontend), Megan (Design and QA), Kayden (Device). B7 goes to Megan and B14 to Kayden; Megan co-builds five frontend checkpoints (3.7) | Hybrid chosen |

### 1.1 DEC-33 · Who owns what (settled 5 Nov)

Leads were named on 5 Nov: Kayden on Device, Eli on Backend, Ca'Marion on Frontend, Megan on Design and QA. B7 (species integration) goes to Megan, because it builds on her species research (D1). B14 (photo diagnosis) goes to Kayden, who builds it when he has time; it stays optional and first to cut. Section 3 gives every checkpoint a due week.

- **A (v2):** Kayden owns Device and also takes B14 (diagnosis) and B15 (accounts) in March if Device is on time. Megan owns Design and QA. Backend and Frontend leads to be named.
- **B (Eli):** move B7 (species integration) to Design and B14 (diagnosis) to Frontend.
- **Hybrid (suggested):** name the leads first. Move B7 to Design, because it builds directly on Megan's species research (D1). Leave B14 unassigned until B11 lands, then give it to whoever has room; it is optional and first to cut.

## 1A. Problems found and fixed

Every problem below is resolved in this document. V and E items were contradictions inside v2 and inside Eli's spec. R items were found while writing the decisions into the spec on 3 Nov; each was small enough to fix directly, and the fix is noted where it matters. Object in a comment if any fix looks wrong.

### Inside the two sources

| # | Problem | Resolved as |
| --- | --- | --- |
| V-1 | v2 said "no plant until gate 13", but its 72-hour soil test was gate 15 | Plant goes in after G20 (DEC-32) |
| V-2 | v2's API section said "every six hours", its firmware section used the period-4 window | Sync window (DEC-05) |
| V-3 | v2 called the divider resistors "matched" but used 1 MΩ and 2 MΩ | Two 1 MΩ (DEC-10) |
| V-4 | v2's sync window was hardcoded in firmware | Window sent in the config reply (DEC-20) |
| V-5 | v2 never said when a reading becomes "estimated" | After 24 h without a clock sync (DEC-17) |
| V-6 | v2 put diagnosis in March in one place and November in another | After B11, due week of 15 Mar, optional (DEC-28) |
| E-1 | Eli's "5% assumption rate" was counted at an earlier revision | Recounted in 17.4 |
| E-2 | Eli placed the light sensor both in the lid and on an arm | Lid (DEC-30) |
| E-3 | Eli's summary table omitted columns that its table definitions had | Definitions in section 9 are the authority |
| E-4 | Eli used v1 checkpoint numbers (B6, B12) | v2 numbering (B7, B14) |
| E-5 | Eli listed a cloud server as settled and as still open | Pi (DEC-01) |
| E-6 | Eli's 336 buffer slots were shared with events | Separate event file (DEC-16) |
| E-7 | Readings sent before a stake had a plant were logged as rejects and lost | Stored under the stake, attached at setup (10.1) |
| E-8 | lux and battery\_mv could not be empty, but sensors can fail | lux nullable, with a fault flag (8.3, 9.2) |
| E-9 | Diagnosis results were never stored | diagnoses table (DEC-23) |

### Found during the rewrite

| # | Problem | Resolved as |
| --- | --- | --- |
| R-1 | MySQL 8.0 reached end of life in April 2026, and Raspberry Pi OS only packages MariaDB, not MySQL | MySQL 8.4 LTS, run from the official mysql:8.4 Docker image on the live server and every laptop alike (decided 5 Nov, Q28) |
| R-2 | D6 is the chip's serial transmit (TX) pin, driven high by the boot message. A float switch to ground there would short it at every boot | Float switch on D7 (an input at boot); LED on D6 (6.2) |
| R-3 | An LED that stays lit or blinks while the stake sleeps would drain the battery | LED shows status for 5 s after a button press, and flashes at hourly wakes only when something is wrong (Q26 placeholder, 7.1) |
| R-4 | A USB-C plug is wider than a PG7 gland opening, so a cable can't be threaded through one | Waterproof panel-mount USB-C extension with a cap (Q27 placeholder, 6.7) |
| R-5 | Neither source said how a button and LED reach the outside of a sealed box | Waterproof panel-mount button and LED holder (Q27 placeholder) |
| R-6 | The live server with backups (B16) was due in April, but real readings start in November | B16 due week of 16 Nov; restore test G32 by 11 Dec |
| R-7 | DEC-12 (adjust the dose) and DEC-15 (recalibrate) need to edit a plant, but no endpoint could | PATCH /api/plants/:id added (8.4) |
| R-8 | The ESP32 can't read time-zone names such as America/Los\_Angeles | Config reply sends a POSIX time-zone rule, tz\_posix (8.2) |
| R-9 | A recalibration changes the moisture scale in the middle of a cycle | Cycles spanning a calibration change are excluded from learning (11.2) |
| R-10 | A stuck button would wake the stake over and over and drain the battery | Stuck-button guard (7.2) |
| R-11 | After a power loss the stake has no clock, so it can't find the 11:30 window | It scans at every hourly wake until one sync succeeds (7.4) |
| R-12 | upload\_interval\_min only applied to 6-hourly uploads, which DEC-05 rejected | Removed from the config reply |
| R-13 | Both sources wired the float switch so that a broken wire would read "water OK" and let the pump run dry | Switch closed while water is above the mark; open (low water or broken wire) blocks the pump (6.5) |
| R-14 | water\_now was a yes/no flag that stayed true until the next upload, so the stake could water twice for one request | Config sends water\_request\_id; the stake handles each id once (7.3, 10.3) |
| R-15 | An internal pull-up left on during sleep would draw current through a closed float switch all night | Pull-up enabled only while reading (7.1) |
| R-16 | read\_interval\_min was sent by the server although READ\_EVERY\_MIN is a compiled constant (found by Eli's review, 6 Nov) | Removed from the config reply and from flash; the read interval is fixed at 60 min in firmware (7.1, 7.7, 8.2, 10.2) |
| R-17 | "Open" meant "stop and ask" in section 0 but "use the placeholder" in section 16, and 17.4 counted 3 Open values where section 16 has 5 (found by Megan's review, 6 Nov) | Open with a named placeholder: use it and flag it. Open with none: stop and ask (0, 16). Count corrected to 5 (17.4) |
| R-18 | The spec said learning rewrites the schedule and replaces the threshold, but the model only sets the minimum-interval safety floor; the threshold is fixed per species (Megan, 6 Nov) | Wording changed in 2.3, 8.2 and 13.3; mechanics and field names unchanged |
| R-19 | calibrations required dry\_raw and wet\_raw, but clearing a calibration (sensor replaced, reassigned) has no numbers to log (Megan, 6 Nov) | Both columns nullable; a row with both NULL means "cleared" (9.2, 10.10) |
| R-20 | Retire was undefined: a retired stake got 401, never received new settings and kept watering on its old calibration, and could never be claimed again. A used claim code returned 409 although its hash is gone (Megan, 6 Nov) | Retire is a reversible pause: the stake still syncs but gets null calibration and "attention", so it will not water; un-retiring restores it. Unknown and used codes both return 404 (8.4, 8.5.1, 9.2, 10.1–10.4, 11.2, 13) |
| R-21 | Raspberry Pi prices rose sharply in 2026 (memory shortage), making the planned home server too expensive | Live server moved to an Oracle Cloud Always Free Arm machine, sized to stay above Oracle's idle line (DEC-01, 5.1, 15, 9 Nov) |

## 2. At a glance

Sprout is a sensor stake you push into a plant pot you already own. A jar of water sits beside it. When the soil is actually dry, a small pump sends water through a thin tube into the pot. Over weeks, the system learns how fast that specific pot dries and corrects the generic advice from the plant database.

### How it fits together

&#91;embedded content: how data moves · stake, server, browser\]

Readings travel up to the server once a day, and the settings the stake should follow travel back in the same reply. The weekly model and the dashboard both work from the history kept in MySQL.

&#91;embedded content: the user's core flow · setup once, then the daily loop\]

Setup happens once. After that the stake does the daily work, and the owner only acts when an alert asks them to.

### 2.1 Three things the project must prove

1. It waters the plant without being told to.
2. It never overwaters when the server, the network or the sensors fail, because every cutoff lives in the firmware. A fault in the pump driver itself (a stuck output pin or a shorted MOSFET) is not covered by firmware; the jar size limits the damage, and a hardware cutoff is open question Q18.
3. It learns the pot's real drying rate, and the dashboard shows that learning happening.

A feature is complete only when its hardware path, data path, software behaviour and acceptance test all agree.

### 2.2 Tier 1 — required by the project guidelines

If any of these is missing, the project does not qualify.

| Requirement | How Sprout meets it | Section |
| --- | --- | --- |
| Data driven | Hourly sensor readings (moisture, light, battery, reservoir) plus every watering, and cited species reference data. About 8,700 readings per stake per year | 8, 9 |
| Connects to a MySQL database | MySQL 8.4 LTS on the live server holds accounts, stakes, plants, species, readings, events, cycles, model fits, alerts and supporting tables | 9 |
| At least one AI-enhanced feature | The learning model. Mr. Benrud confirmed on 29 Oct that it counts on its own. Photo diagnosis is an optional extra | 11, 12 |
| Usable by the public | A web app: any browser, any phone, nothing to install. A stranger can claim a stake with its sticker code | 8.5, 13 |
| Monetization strategy | Hardware sale plus a monthly subscription. Designed and costed, not operated | 2.5 |

### 2.3 Tier 2 — in scope

| Feature | Why | Decided by |
| --- | --- | --- |
| Core watering loop with every failsafe | The stake acting on its own, safely | — |
| Learning model | The product thesis: learn this pot's drying rate and use it to set the watering safety floor | DEC-24, 25, 26 |
| Dashboard: 14-day sawtooth chart, stat cards, AI card | The chart is the most persuasive thing in the project | DEC-03 |
| Real accounts, sessions, hashed passwords | Needed for a public app | — |
| Claim a stake by its sticker code | Links a stake to an account; also the best 30 seconds of the demo | DEC-21 |
| Alerts: low water, low battery, low light, offline, failed delivery, pump shortfall | Tells the owner when to act | DEC-13, 14 |
| Water now, refill, reset learning, recalibrate | Owner actions | DEC-12, 15 |
| Devices page and Help page | Manage stakes; explain alerts and the refill routine | DEC-21 |
| Sync button | Wakes the stake and forces a reading and a sync | DEC-06 |
| Status LED | Shows ok, attention or fault on the stake itself | DEC-07 |
| Photo leaf diagnosis (optional) | Extra AI feature for the demo; built after B11 and first to cut | DEC-27, 28 |

### 2.4 Tier 3 — deferred on purpose

Each of these was considered and set aside. They go on a slide as future work, not into the build. Never imply a feature exists unless it is built and tested.

| Deferred | Why |
| --- | --- |
| Soil temperature sensor | DEC-08. soil\_temp\_c stays in the contract as an always-null field, so a probe can be added later without a contract change |
| OLED screen | About $12 and roughly 10% of the battery budget; the status LED covers most of the value |
| Plant journal or photo timeline | Diagnosis stores images, but a timeline is a separate feature (Q14) |
| Over-the-air firmware updates | Needs secure delivery, integrity checks and rollback; the USB-C port covers updates |
| Rootbound detection | Needs most of a year of data before it says anything |
| Vacation mode | Pure software, not core |
| Solar charging | A natural future product feature |
| Multiple plants from one jar | Needs a valve per pot |
| Modularity as a marketed feature | Tubing is push-fit and the battery is socketed already; naming it is free, engineering it further is not |
| Flow or clog sensing | No sensor observes flow, so we don't claim it. The delivery check (7.1) is indirect evidence only |
| Continuous reservoir level sensor | The float switch plus a computed estimate covers safety and prediction |
| Continuous uploads via a classroom computer | Worth one test (Q13); the plan does not rely on it |

### 2.5 Monetization

- **Hardware:** the stake sells for about $45, priced near target production cost on purpose. The device is a customer acquisition cost, not the business.
- **Subscription:** $3 a month for multi-plant tracking, full history and photo diagnosis. The free tier covers monitoring and alerts for one plant.
- **Model:** sell the device near cost and earn on the recurring side, as AeroGarden, Keurig and printer companies do.
- **Honest limits:** at prototype quantities one stake costs about $175 to $205 in parts, far above that price; a margin appears only at production volume. The model is designed and costed, not operated.
- **Build rule:** no payment page in the demo build (Q12). A pricing slide covers this requirement.

### 2.6 Key numbers

| Quantity | Value | Status |
| --- | --- | --- |
| Sensor read interval | Every 60 min | Decided |
| Sync | One window a day, 11:30–12:40 local: the phone hotspot in period 4 on school days, home WiFi every day over breaks, plus any button press | DEC-05, 06 |
| Data staleness on the dashboard | Up to about 24 h on school days, about 71 h over a weekend | Follows from DEC-05 |
| Battery target | 180 days with a 20% reserve | Projected at G28 from measured currents |
| Parts cost | About $175 ordered (about $117 if the school shop has the tools), plus about $30 of additions (6.1) | Estimate |
| Water per watering | 60 ml default per plant, adjusted after the first live week | DEC-12 |
| Readings per stake per year | About 8,700 | — |
| Plant goes in | Fri 18 Dec 2026 | DEC-31 |
| Demo | Fri 14 May 2027 | Placeholder (Q16) |

## 3. Team, tracks and checkpoints

Four tracks, built so nobody waits on anybody else. Every checkpoint below has a due week (the Monday it starts); milestone dates are in section 4. Leads were named on 5 Nov. B7 (species integration) goes to Megan and B14 (photo diagnosis) to Kayden (DEC-33).

### 3.1 The API contract is frozen

- The contract (section 8) is the agreed shape of data between the stake, the server and the dashboard. It freezes on Fri 13 Nov.
- After that, nobody renames, removes or retypes a field alone. Changing it is allowed; changing it quietly is not. Say it out loud, get agreement, update section 8.
- The failure this prevents: someone renames moisture\_pct to moisture, the stake keeps sending the old name, the server stores nulls, the dashboard shows blanks, and nobody sees an error.

### 3.2 Plant data is faked on day one

- Backend's first job is a simulator that writes eight weeks of messy readings into the development database (10.7).
- Simulate badly on purpose: noise, dropouts, a manual watering, an outage, weekend gaps. Clean fake data produces code that only works on fiction.
- Because we generate it, we know the true drying rate. It is the only test with an answer key.

### 3.3 The AI is not a gate

The dashboard reads readings and events directly, never the model. The stake runs on species defaults until the model has something better. The model is one consumer of the data, like the dashboard.

### 3.4 Tracks

| Track | Owner | Owns |
| --- | --- | --- |
| Device | Kayden | Assembly, firmware, wiring, enclosure, provisioning, running the hardware gates, the plant over breaks; B14 (photo diagnosis) when there is time |
| Backend and AI | Eli | Database, API, simulator, model, alerts, the cloud server, backups |
| Frontend | Ca'Marion, with Megan on five checkpoints | Dashboard, charts, claim and setup flow, every screen state |
| Design and QA | Megan | Visual system, screens, species research, enclosure drawing, witnessing every gate, test log, documentation; B7 (species integration); builds C9, C10, C13, C14 and C15 with Frontend (3.7) |

The real risk is not waiting. It is four people building against assumptions that drift apart. The defence is a working end-to-end path by Fri 4 Dec, even if it is ugly.

### 3.5 Device checkpoints — Kayden

| # | Checkpoint | Done when | Due (week of) |
| --- | --- | --- | --- |
| A1 | First flash | Board LED blinks on command | Done |
| A2 | Network settled | Board makes a real HTTPS POST to a test endpoint over Kayden's hotspot in the classroom and over home WiFi; repeated against the live server at A9a (G2) | 9 Nov |
| A3 | Sensors reading | Moisture and light read sensibly; dry\_raw and wet\_raw recorded (G3–G5) | 9 Nov |
| A4 | Battery sensing | Divider built; reading matches a multimeter at three voltages (G7) | 16 Nov |
| A5 | Pump driver | An LED in the pump's place switches cleanly, then the pump runs (G9, G10) | 16 Nov |
| A6 | Pump calibrated | ml\_per\_s recorded; no siphoning after shutoff (G11) | 16 Nov |
| A7 | Float switch | Low water detected and the pump blocked (G12) | 16 Nov |
| A17 | Soldering sign-off | Supervision and ventilation confirmed before the first joint; Kayden's dad supervises at home (Q25, closed 9 Nov) | 16 Nov |
| A9a | First reading stored | First real reading in MySQL by Fri 20 Nov; the G2 network test repeated against the live server | 16 Nov |
| A9b | Posting to the server | Retries make no duplicates; buffering survives power loss (G15, G16) | 30 Nov |
| A8 | Control logic | Full loop runs into a cup; every failsafe fires; the button wakes the stake (G13, G14) | 30 Nov |
| A10 | Soldered permanent build | Perfboard version passes the same tests (G23) | 30 Nov |
| A11 | Enclosure sealed | Waterproof test passes with every opening fitted (G18, G19) | 30 Nov |
| A12 | Sleep current | Measured on the soldered, boxed stake (G23) | 30 Nov |
| A13 | 72-hour soil run | Three days in soil, no plant, clean (G20, Mon 7 – Thu 10 Dec) | 7 Dec |
| A15 | Firmware update | Reflash the sealed stake through its USB-C port; an interrupted update leaves the pump off (G21) | 7 Dec |
| A14 | Live deployment | Plant in at Kayden's home on Fri 18 Dec, a no-student day; it stays there for winter break, syncing on home WiFi (G22, Megan witnesses by video call) | 7 Dec |
| A16 | Second unit | Second stake built, fixing everything learned from the first | 12 Apr |

November is the tightest stretch: A2 to A12 land in three working weeks around Thanksgiving. 14–17 Dec is finals week, so it holds reruns only: if G20 fails, it re-runs then. Everything else is due by Fri 11 Dec.

### 3.6 Backend checkpoints — Eli

| # | Checkpoint | Done when | Due (week of) |
| --- | --- | --- | --- |
| B1 | Database schema | Every table in section 9 created by migration; ten species seeded from Design's CSV (D1). Kayden builds with Claude Code; Eli takes over from 19 Nov (3.9) | 9 Nov |
| B2 | Data simulator | Eight weeks of messy readings for SIM-001 to SIM-003 in the dev database (10.7), written through the shared ingest\_batch function (10.1); a test fits a straight line to one simulated cycle and recovers its true rate from sim\_truth.json within 10%. Kayden builds with Claude Code; Eli takes over from 19 Nov (3.9) | 9 Nov |
| B3 | Ingest endpoint | POST /api/readings stores and deduplicates (10.1); wraps ingest\_batch from B2 | 16 Nov |
| B4 | Device key auth | Requests without a valid key get 401 | 16 Nov |
| B16 | Live server on Oracle Cloud | API, MySQL and tunnel run on the Oracle virtual machine; nightly backup copied off it (5, 15) | 16 Nov |
| B17 | Provisioning tools | create\_device script and USB provisioning tool work (10.8) | 16 Nov |
| B5 | Config reply | Built per 10.2 and applied by the stake; closed loop by Fri 4 Dec | 30 Nov |
| B6 | Read endpoints | Every GET in 13.2 returns real data | 30 Nov |
| B8 | Claim and plant setup | Claim code links a stake; plant creation and the calibration guards work (8.5, 10.10) | 7 Dec |
| B9 | Water now and refill | Requests reach the stake and come back delivered or refused (10.3) | 7 Dec |
| B10 | Alerts engine | Every alert in 10.4 raises and clears | 7 Dec |
| B11 | First learned model | The simple average drives the config by Fri 8 Jan (11.3) | 4 Jan |
| B7 | Species integration | Perenual names, photos, toxicity and care text cached into species (Megan builds, DEC-33) | 18 Jan |
| B12 | Light model fitted | Regression stored with its version; used only once it beats the average (11.3) | 25 Jan |
| B15 | User accounts | Register, log in, log out, sessions, hashed passwords (8.6) | 8 Mar |
| B13 | Model evaluation | Walk-forward errors recorded by Fri 19 Mar (11.5, G30) | 15 Mar |
| B14 | Leaf diagnosis (optional) | Upload, Gemini call, stored result (12). Kayden builds it in any week with spare time once B11 is live; first to cut | Any week 4 Jan – 15 Mar |

Until B15, build against a seeded account: insert one account with id 1 and keep a single CURRENT\_USER constant. Every query still filters by account. When B15 lands, the constant becomes the session user and nothing else moves. G17b is run once B15 lands.

### 3.7 Frontend checkpoints — Ca'Marion, with Megan

| # | Checkpoint | Done when | Due (week of) |
| --- | --- | --- | --- |
| C1 | Dashboard shell | Layout built against mock JSON in the contract's shape, matching Design's screens, with the screen-folder layout from 3.7. Kayden builds with Claude Code; Ca'Marion takes over from 19 Nov (3.9) | 16 Nov |
| C2 | Live data | Reads the real API; shows current moisture | 30 Nov |
| C3 | The chart | 14-day sawtooth with threshold line and watering markers (13.3) | 30 Nov |
| C4 | Claim and plant setup | Add-device screen; species picker, name, calibration with the stake's latest raw reading shown, target ml, jar size | 7 Dec |
| C5 | Stat cards | Light today, reservoir, battery, waterings | 7 Dec |
| C7 | Water now and refill | Wired to the API, with honest wording for each request state (10.3) | 7 Dec |
| C6 | AI card | Species interval vs learned interval, learning progress | 4 Jan |
| C8 | Alerts | Shown and dismissible; offline banner | 4 Jan |
| C9 | Reset learning and recalibrate | Both actions ask for new calibration numbers and explain what happens. Megan builds; Ca'Marion tests | 1 Feb |
| C10 | Mobile | One column under 640 px; touch targets at least 44 px. Megan builds; Ca'Marion tests | 8 Feb |
| C15 | Devices and Help pages | Rename, reassign, retire or un-retire (a pause), "sensor replaced"; alert meanings and the refill routine. Megan builds; Ca'Marion tests | 15 Feb |
| C12 | Sign-up and log-in | Account screens; anyone signed out is redirected | 8 Mar |
| C11 | Leaf diagnosis (optional) | Photo upload and the result card (12.6). Build in any week with spare time once B14 has an endpoint; first to cut | Any week 4 Jan – 15 Mar |
| C13 | History view | Long-range charts and model accuracy over time. Megan builds; Ca'Marion tests | 12 Apr |
| C14 | Polish | Loading, error, empty and unknown states everywhere. Megan builds; Ca'Marion tests | 26 Apr |

**Sharing the frontend (agreed 5 Nov).** Design's work is heavy from October to mid-December and light from January to April, so Megan builds five checkpoints that are mostly wording and look: C9, C10, C13, C14 and C15. Ca'Marion owns the rest and tests Megan's five. To avoid clashing in the same code, each checkpoint lives in its own screen folder under web/src/screens/, shared pieces (web/src/api/types.ts and web/src/components/) change only through a pull request the other person reviews, and C1 sets up that layout.

### 3.8 Design and QA checkpoints — Megan

| # | Checkpoint | Done when | Due (week of) |
| --- | --- | --- | --- |
| D2 | Test log set up | Shared sheet, one row per gate, recording actual values | 2 Nov |
| D1 | Species research | Ten plants as a CSV with numeric thresholds, toxicity and a cited source each (9.3); delivered early in the week, because B1 needs it | 9 Nov |
| D3 | Visual system | Colours, type and components documented for Frontend | 9 Nov |
| D4 | Dashboard screens | Every screen in 13.1 designed before Frontend builds it; delivered early in the week (by Mon 16 Nov), because C1 needs it | 16 Nov |
| D6 | Enclosure drawing | Positions for 3 glands, the USB-C port, button, LED and light window; tube length; stake mounting (Q27) | 16 Nov |
| D5 | Bench gates witnessed | G2–G16 and G17a recorded with numbers | 30 Nov |
| D9 | 72-hour run monitored | G20 documented in full | 7 Dec |
| D7 | Build gates witnessed | G18, G19, G21, G23 and G32 recorded with photos | 7 Dec |
| D15 | Break checklist | Home WiFi is in the stake's network list; plant, control plant and jar travel together; logging continues | 7 Dec |
| D8 | Control plant | Hand-watered twin set up beside the live plant on Fri 18 Dec, travelling with it over breaks | 7 Dec |
| D10 | Maintenance routine | Jar cleaning, filter check and probe inspection written | 11 Jan |
| D11 | Build documentation | Photo record of the assembly written up | 15 Feb |
| D12 | Model evaluation witnessed | G17b, G30 and G31 recorded independently | 15 Mar |
| D13 | Presentation assets | Timelapse, charts, demo script | 3 May |
| D14 | Final report | Results, limitations, what we would change | 3 May |
| D16 | Simulator recovery witnessed | G24 recorded with numbers | 25 Jan |

The tester is not the builder: whoever built a thing tests it the way they built it. For every gate the log records date, who ran it, device version, actual measured values and photos where they apply. "Passed" alone is not a record. When Megan builds a frontend checkpoint, Ca'Marion tests it and Kayden witnesses any gate it touches, so nobody signs off their own work.

### 3.9 How a checkpoint gets built (agreed 5 Nov)

Every checkpoint goes through the same five steps. Code lives in one GitHub repository; this document stays the source of truth for what gets built.

1. **Task card.** Kayden uses Claude Code to write a task card from this spec and saves it in the repository as tasks/\<checkpoint>.md (for example tasks/B3.md). A card holds the checkpoint and its "Done when", the spec sections it depends on (copied in, not linked), the files it may create or change, the test or gate that proves it, and the standing rules below. Cards are written in weekly batches, a week ahead of their due week.
2. **Build on a branch.** The owner makes a branch named after the checkpoint (for example b3-ingest) and gives the task card to their coding agent. Replit Agent, Mistral and Google AI Studio can all work inside the repository. Code is never copied by hand out of a chat window.
3. **Pull request.** One pull request per checkpoint, titled with its ID, with the test output pasted into the description.
4. **Review.** Kayden reviews every pull request with Claude Code: against the task card, against sections 8 and 9, and by running the tests. Requested changes go back to the owner on the same branch. In January, decide whether leads can review each other's pull requests that touch no shared code.
5. **Test and merge.** The tester from 3.8 checks it, Megan witnesses any gate it touches, and it merges into main. Kayden's own Device pull requests still go through Claude Code review, but sign-off comes from the tester and Megan, so nobody signs off their own work.

**Standing rules in every task card:**

- MySQL 8.4 only. Never use Replit's built-in database, SQLite or any other database.
- Never rename, remove or retype a field in section 8 or a column in section 9.
- Change only the files the card lists. Anything else needs a line in the pull request saying why.
- If this spec does not say, stop and ask in the pull request instead of inventing an answer.

**Tools and budget.** Kayden uses Claude Code. Eli, Ca'Marion and Megan each have the Replit Core plan with about $20 of Replit credits, plus Mistral and Google AI Studio. Use Mistral or AI Studio for questions and small fixes so Replit credits last for the bigger checkpoints.

**Late start (agreed 5 Nov).** Eli, Ca'Marion and Megan start building around Thu 19 Nov, and Thanksgiving recess follows (23–27 Nov), so their first full build week is Mon 30 Nov. To keep the Fri 4 Dec end-to-end path and the plant date, Kayden builds the starting pieces with Claude Code: B1 (database schema) and B2 (data simulator) before the contract freeze on Fri 13 Nov, and C1 (dashboard shell) on Mon 16 – Wed 18 Nov, once Megan's screens (D4) arrive early that week. Each owner takes over from 19 Nov. B3, B4, B16 and B17 stay with Eli and are still due Fri 20 Nov; if they slip, they move to the week of 30 Nov, and the first-real-reading milestone moves with them. Megan's design checkpoints don't need a coding tool and keep their dates.

**Testing backend code (agreed 6 Nov).** Replit can't run Docker and has no MySQL, so Kayden is the only person who runs backend code against MySQL 8.4. Eli's agent writes the code and its tests. When a backend pull request opens, Kayden runs the tests with Claude Code within 24 hours, and Claude Code posts the error report as a comment on that pull request, with the exact error text so Eli can hand it straight to his agent. Frontend checkpoints run against mock JSON and are tested inside Replit as normal. If backend round trips get slow, try installing MySQL 8.4 inside Eli's Replit project after his first two pull requests.

## 4. Timeline

The plan works back from a demo on Fri 14 May 2027, which is still a placeholder until Mr. Benrud sets it (Q16). Break, holiday and finals dates come from the Grossmont Union High School District 2026–27 calendar, checked on 5 Nov (4.2). The plant goes in on Fri 18 Dec and goes home with Kayden for the break; Fri 18 Dec has no students, so planting happens at Kayden's home, and finals week (14–17 Dec) holds reruns only (4.2).

&#91;embedded content: milestones · Nov 2026 to May 2027, school breaks shaded\]

The chart is drawn from the milestone table below; change a date there and in the chart together.

### 4.1 Milestones

| Milestone | Date | What must be true | Checkpoints and gates |
| --- | --- | --- | --- |
| API contract frozen; simulated data in the dev database | Fri 13 Nov 2026 | Section 8 agreed; SIM-001 to SIM-003 loaded | B1, B2 |
| Live server up; first real reading in MySQL | Fri 20 Nov | The live server serves the API over HTTPS with nightly backups; a real stake reading is stored | B3, B4, B16, B17, A9a, C1 |
| Bench done, soldered and sealed; closed loop; dashboard on live data | Fri 4 Dec | G2–G19 (G17a only) and G23 pass; a server setting changes the stake's behaviour; the chart shows real data | A2–A12, B5, B6, C2, C3 |
| 72-hour soil test | Mon 7 – Thu 10 Dec | G20 passes clean | A13, D9 |
| Backup restore proven; claim and setup working | Fri 11 Dec | G32 passes; a stake is claimed and a plant set up through the dashboard; the firmware update test (G21) passes | A15, B8, C4, G21 |
| Spare week | 14–17 Dec | Finals week: reruns only, no new work. G20 re-runs here if it failed | G20 rerun only |
| Plant goes in | Fri 18 Dec | Live plant and control plant start at Kayden's home (no students that day); Megan witnesses G22 by video call | A14, D8, G22 |
| Simple learned model drives the stake | Fri 8 Jan 2027 | The average of real cycles feeds the config; AI card live | B11, C6 |
| Light model fitted | Fri 29 Jan | Regression stored; used only if it beats the average | B12, G24, D16 |
| Model evaluated | Fri 19 Mar | Walk-forward errors recorded and witnessed | B13, D12, G30, G31 |
| Photo diagnosis (optional, spare-time work) | Any time 4 Jan – Fri 19 Mar | Upload to result card works; built only in weeks with spare time after the simple model is live, and dropped first if anything slips | B14, C11, G29 |
| Second unit built | Fri 16 Apr | Second stake passes the bench gates | A16 |
| Demo-day fallback rehearsed | Fri 23 Apr | G32 re-run: the dashboard runs from a laptop with a fresh dump | — |
| Feature freeze | Fri 30 Apr | Bug fixes only after this | C14 |
| Report and presentation done | Fri 7 May | Assets and report finished | D13, D14 |
| Demo | Fri 14 May | — | — |

### 4.2 School breaks (placeholder dates)

| Break | Dates | Plan |
| --- | --- | --- |
| Thanksgiving | 23–27 Nov 2026 | No plant yet; nothing is due that week |
| Winter | 21 Dec 2026 – 1 Jan 2027 | Plant, control plant and jar go home with Kayden; the stake syncs every day on home WiFi |
| Spring | 22 Mar – 2 Apr 2027 (two weeks) | Same as winter: plant, control plant and jar go home with Kayden; nothing is due these two weeks |

**Checked against the district calendar (5 Nov).** Source: the Grossmont Union High School District 2026–27 calendar, as shown on third-party calendar sites; confirm on guhsd.net if anything looks off.

- First-semester finals are Tue 15 – Thu 17 Dec. Thu 17 Dec is the last day of first semester. Fri 18 Dec is a staff workday with no students.
- Second semester starts Mon 4 Jan. Spring finals are Tue 1 – Thu 3 Jun, and Thu 3 Jun is the last day of school.
- No school on Wed 11 Nov (Veterans Day), Mon 18 Jan (Martin Luther King Jr. Day), Mon 8 Feb (Lincoln Day), Mon 15 Feb (Washington Day) and Mon 31 May (Memorial Day). Those weeks have four school days.
- Spring recess is two weeks (22 Mar – 2 Apr), not one. Anything that was due the week of 22 Mar now falls the week before.
- **Settled 5 Nov:** the plant goes in at Kayden's home on Fri 18 Dec (a no-student day), everything once due the week of 14 Dec is now due the week of 7 Dec, and finals week holds reruns only.
- The demo date is not on the school calendar; Mr. Benrud sets it (Q16).

### 4.3 Rules

- Milestones are meetings everyone attends, not hopes in a document.
- There are no teacher checkpoint dates (Mr. Benrud), so this timeline is the only structure we have.
- A slip of a few days moves a checkpoint's week label, not the order of milestones.
- The spare week protects the plant date. If G20 fails twice, the plant moves to January rather than skipping the soil test.
- The 72-hour soil test is never shortened.

## 5. System architecture and hosting

The stake only makes outbound HTTPS calls. Everything else runs on one Oracle Cloud Always Free virtual machine, reached through a Cloudflare Tunnel: a free outbound connection that gives the server a public HTTPS address without opening any inbound web ports (DEC-01, DEC-02).

&#91;embedded content: system architecture · stake, Oracle Cloud server, dashboard, outside services\]

The dashboard never reads the model directly, and nothing waits on the model. The vision API is called only by the API, only for the optional leaf diagnosis.

### Data flow for developers

&#91;embedded content: data flow for developers · with key\]

Read this with sections 7 (firmware), 8 (the contract) and 10 (server rules). The key at the bottom defines each term.

### 5.1 What runs where

| Piece | Where | Details |
| --- | --- | --- |
| Live API | Oracle VM | One FastAPI app run by uvicorn with exactly one worker, as a systemd service named sprout-api that restarts on crash. Listens on 127.0.0.1:8000 |
| Dashboard | Oracle VM | The built React files (web/dist) served by the same FastAPI app. Any path that is not /api/... returns index.html so React Router works |
| Live database | Oracle VM | MySQL 8.4 LTS, listening on 127.0.0.1 only. Installed from the official mysql:8.4 Docker image (decided 5 Nov, Q28), which supports the server's arm64 chip, with a named volume, restart policy "unless-stopped" and innodb\_buffer\_pool\_size = 1G (5.1, idle rule). Every laptop runs the same image for development. |
| HTTPS | Cloudflare Tunnel | cloudflared runs as a systemd service and forwards https://\<hostname> to 127.0.0.1:8000. The hostname is Q19 |
| Scheduled jobs | Inside the API process | APScheduler (10.5). One worker means each job runs exactly once |
| Backups | Oracle VM, copied off it | Nightly database dump plus photos, pushed to a private GitHub repository (placeholder, 15.2) |
| Development | Backend lead's own machine | Local MySQL 8.4 plus the simulator. The stake never posts here |
| Code changes | git | Push from any machine. On the server, a deploy script pulls, runs database migrations, rebuilds the dashboard and restarts sprout-api (15.4) |

**Server (decided 9 Nov, closes Q28):** Oracle Cloud Always Free, shape VM.Standard.A1.Flex with 1 OCPU and 6 GB of memory, Ubuntu 24.04 (arm64), 50 GB boot volume. It lives in the account's home region, chosen once at sign-up: US West (San Jose), or US West (Phoenix) if San Jose isn't offered. Free machines exist only in the home region, so if Oracle reports "out of host capacity", retry later in the same region rather than switching. Python 3.12 or newer, installed with uv. Only SSH (port 22, key login only, password login off) is open inbound; HTTPS arrives through the tunnel.

**Why 1 OCPU and 6 GB, not the full free 2 and 12 (agreed 9 Nov):** Oracle may reclaim an Always Free machine when, over 7 days, its CPU, network and memory use all stay under 20%. Sprout would use about 1.5–2 GB, which is under 20% of 12 GB. On 6 GB, with MySQL's buffer pool set to 1 GB, steady memory use sits around 25–35%, so the machine is not idle by that rule. If Oracle changes the rule or the free tier, first resize the machine if that keeps it free; otherwise upgrade the account to Pay As You Go with a budget alert and pay the small cost to keep it running.

### 5.2 Environment rules

- Secrets live in /etc/sprout/sprout.env, readable only by the service user and loaded by systemd. Never in the repository: DATABASE\_URL, SECRET\_KEY, SESSION\_DAYS, PHOTO\_DIR, VISION\_API\_KEY, BACKUP\_REMOTE.
- Never point a development app at the live database. That is the one way simulated rows reach real training data.
- plants.is\_simulated marks demo plants, so they are obvious at a glance and left out of every real-plant view.
- Not used: the school Hostinger account (rejected in v2: an account we don't control and credentials on the open internet) and Replit (Q5, closed by DEC-01 and DEC-02).

### 5.3 Hostname (Open Q19)

A named Cloudflare Tunnel needs a domain added to a free Cloudflare account. A free "quick tunnel" address changes on every restart, and the stake's server URL is written into its flash, so a quick tunnel will not do. Placeholder: buy a cheap domain (about $10 a year) and use a subdomain such as sprout.\<domain>. Record it before B17 (provisioning), week of 16 Nov.

## 6. Hardware

The core parts and the pump circuit are unchanged from v2. The decisions add a sync button and a status LED (DEC-06, 07), drop the soil temperature probe (DEC-08), fix the pin map (DEC-09) and the battery divider (DEC-10), and settle how the sealed box is charged and reflashed (DEC-29).

### 6.1 Parts

Already ordered ($174.68):

| Item | Price | For |
| --- | --- | --- |
| Seeed XIAO ESP32-C3 | $9.90 | The controller, WiFi built in |
| Capacitive moisture sensor, 4-pack (TLC555) | $9.90 | Soil moisture |
| GY-302 BH1750 light sensor, 3-pack | $6.88 | Light in lux |
| Mini submersible pump 3–6 V, 4-pack | $6.99 | Moves water |
| Silicone tubing 6 mm, 1 m | $6.99 | Water line |
| IRLZ44N MOSFET, 10-pack | $9.99 | Pump switch |
| EEMB 3.7 V 2000 mAh LiPo, protected | $14.99 | Power |
| JST-PH connector kit | $5.99 | Battery plug |
| ELEGOO 235-piece starter kit | $9.99 | Breadboard, jumpers, resistors, 1N4007 diodes, headers, LEDs, buttons |
| Perfboard, 4-pack | $6.49 | Permanent circuit |
| Female header strips | $5.99 | Socket so the controller is removable |
| Zulkit IP65 enclosure 100 × 68 × 50 mm | $6.49 | Housing |
| PG7 cable glands, 50-pack | $8.99 | Sealed wire entries |
| Glass microscope slides | $6.99 | Light sensor window |
| Permatex clear RTV silicone \* | $5.37 | Sealing |
| Heat shrink tubing kit \* | $4.99 | Wire joints |
| Soldering iron kit \* | $18.98 | Assembly |
| ANENG multimeter \* | $9.99 | Verification and calibration |
| 22 AWG silicone wire, 6 colours \* | $12.79 | Permanent wiring |
| USB data cable, 2-pack \* | $5.99 | Flashing and charging |

Items marked \* may already be in the school shop (about $58 together).

Still to get (prices are estimates):

| Item | Est. | For |
| --- | --- | --- |
| Float switch | $3 | Reservoir interlock (6.5) |
| Two 1 MΩ 1% resistors | $1 (check the kit first) | Battery divider (6.4) |
| 100 nF ceramic capacitor | kit | Steadies the divider reading |
| Three 10 kΩ resistors | kit | Pump gate pulldown, sensor-power pulldown, button pull-up |
| Two 220 Ω resistors | kit | Pump gate series resistor, LED |
| Waterproof panel-mount momentary button, 12–16 mm | $5 | Sync button (Q27) |
| Sealed panel-mount 5 mm LED holder (the LED itself comes from the ELEGOO kit) | $2 | Status LED (Q27) |
| Waterproof panel-mount USB-C extension with cap | $10 | Charging and flashing without opening the box (Q27) |
| Gasket material and four screws | $3 | Resealable lid for battery swaps |
| Black heat shrink or foil wrap | kit | Blocks light on the tube to slow algae |
| Foam or mesh intake filter | $4 | Keeps debris out of the pump (G26) |
| Clear nail polish or conformal coat | $3 | Seals the moisture probe's cut edges |
| Non-Amazon | — | Opaque glass jar, plant pot, potting soil, basil plant (plus a twin for the control plant), stake body (dowel or PVC), drill with 12 mm bit, measuring cup |

Not needed any more: the DS18B20 soil temperature probe (DEC-08).

**Do not substitute these four:**

| Part | Why |
| --- | --- |
| Moisture sensor with the TLC555 chip | The NE555 version needs 4.5 V; the board supplies 3.3 V. Check the chip marking on arrival |
| IRLZ44N MOSFET (or another logic-level part) | The IRF520 needs about 10 V on the gate; at 3.3 V it half-conducts and overheats |
| Protected LiPo | An unprotected cell next to water is a fire risk |
| 1N4007 diode | The 1N4148 is rated 200 mA; the pump's switch-off spike destroys it and then the MOSFET |

### 6.2 Pin map (DEC-09)

Only D0, D1 and D2 can take analog readings while WiFi is on, and only GPIO0 to GPIO5 (D0 to D3) can wake the chip from deep sleep. That decides the map: moisture and battery take two analog pins, and the button takes D2 so it can wake the stake at any time.

| Pin | GPIO | Part | Notes |
| --- | --- | --- | --- |
| D0 | GPIO2 | Moisture signal (analog) | A boot-sensitive pin, but the sensor is unpowered at boot |
| D1 | GPIO3 | Battery divider (analog) | Two 1 MΩ resistors (6.4) |
| D2 | GPIO4 | Sync button | Deep-sleep wake source. External 10 kΩ pull-up to 3V3; the button connects D2 to ground; wake when D2 reads LOW |
| D3 | GPIO5 | Moisture sensor power | Output; HIGH only during a reading; 10 kΩ to ground so it can't float on during sleep |
| D4 | GPIO6 | Light sensor SDA | I2C |
| D5 | GPIO7 | Light sensor SCL | I2C |
| D6 | GPIO21 | Status LED, through 220 Ω | This is the chip's serial transmit pin. The boot message makes the LED flicker faintly at every wake; that is harmless |
| D7 | GPIO20 | Float switch | The serial receive pin, an input at boot, so a closed switch is safe here. Internal pull-up on only while reading (7.1) |
| D8 | GPIO8 | Empty | Boot pin; leave unconnected |
| D9 | GPIO9 | Empty | Boot pin wired to the board's BOOT button; leave unconnected |
| D10 | GPIO10 | Pump MOSFET gate, through 220 Ω | 10 kΩ from gate to ground holds the pump off at boot |
| 3V3 | — | Light sensor power, button pull-up | Always on; the light sensor sleeps itself |
| BAT+ / BAT− | — | Battery and pump power rail | Raw cell voltage, about 3.7 V |

Why this differs slightly from the map shown in chat: putting the float switch on D6 would short the serial transmit pin to ground during every boot whenever the switch is closed (R-2). Swapping it with the LED fixes that.

Bench-check before soldering (Q6): the stake boots normally with every part connected; the button wakes it from deep sleep; D0 and D1 read correctly with WiFi on; and the LittleFS storage area is big enough (7.5).

### 6.3 Pump circuit and full wiring

Nobody removes any of these parts thinking it is optional:

- **220 Ω gate resistor** limits current into the MOSFET gate and protects the controller pin.
- **10 kΩ pulldown, gate to ground,** holds the pump off while the controller boots. Without it, water can land in the pot at power-up.
- **1N4007 across the pump, striped end to positive,** absorbs the reverse voltage spike when the motor stops.
- **Tube's highest point above the jar's water line,** which stops siphoning after the pump stops.
- **Moisture sensor powered only during a reading:** D3 high, wait 100 ms, read, D3 low. The sensor draws about 5 mA, so this is required for battery life.

The IRLZ44N's legs, printed face toward you and legs down, are 1 gate, 2 drain, 3 source. All grounds are one common ground.

| From | To | Note |
| --- | --- | --- |
| Battery + (JST red) | XIAO BAT+ pad, and the pump rail node | Pump current is taken at the battery junction, not through the board |
| Battery − (JST black) | XIAO BAT− pad, and common ground | Check polarity with a multimeter before first connection |
| Pump rail node | Pump red lead, and 1N4007 cathode (striped end) | The diode sits across the pump |
| Pump black lead | MOSFET pin 2 (drain), and 1N4007 anode |  |
| MOSFET pin 3 (source) | Common ground |  |
| D10 | 220 Ω, then MOSFET pin 1 (gate) |  |
| MOSFET pin 1 (gate) | 10 kΩ to ground | Holds the pump off at boot |
| D3 | Moisture sensor VCC, and 10 kΩ to ground | Sensor powered only during a reading |
| Moisture sensor GND / AOUT | Common ground / D0 |  |
| BH1750 VCC / GND | 3V3 / common ground |  |
| BH1750 SDA / SCL | D4 / D5 |  |
| BH1750 ADDR | Common ground | Sets I2C address 0x23 |
| Float switch lead A / lead B | D7 / common ground | Mounted so the switch is closed while water is above the mark (6.5) |
| Battery + | 1 MΩ, divider node, 1 MΩ to ground |  |
| Divider node | D1, and 100 nF to ground |  |
| Sync button, one leg | D2, plus 10 kΩ from D2 to 3V3 |  |
| Sync button, other leg | Common ground |  |
| D6 | 220 Ω, then LED anode (long leg); LED cathode to ground |  |

### 6.4 Battery measurement and power budget (DEC-10)

The board can't read its own battery, so two equal 1 MΩ resistors run from battery + to ground with their middle point on D1.

- **Permanently connected, never switched.** A switched divider lets the pin float up to full battery voltage, above its maximum.
- **Maths:** battery\_mv = 2 × pin millivolts × batt\_cal. A full 4.2 V cell puts about 2.1 V on the pin, inside the 0–2.5 V range the chip measures accurately at its highest input setting.
- **100 nF capacitor** on the pin, so the high-resistance divider settles before the chip samples.
- **Reading:** average 16 samples. batt\_cal is a correction factor found by comparing against a multimeter at three voltages (G7); use 1% resistors.
- **Leak:** about 2.1 µA, around 0.05 mAh a day.

**Power budget.** Target: 180 days on a 2000 mAh cell with a 20% reserve, so 1600 mAh usable, about 8.9 mAh a day. All currents are estimates until measured.

| Activity | Assumption | mAh per day |
| --- | --- | --- |
| Hourly wake and read | 24 wakes, 1.5 s at 60 mA | 0.6 |
| Sync window | Up to 8 WiFi scans of about 2 s at 100 mA, then one upload of about 6 s at 120 mA; scanning stops after the first success | 0.3–0.6 |
| Button-triggered syncs | About 2 a day, 6 s at 120 mA | 0.4 |
| Pump | One watering every 2.8 days, up to 8.4 s at 250 mA | 0.2 |
| Delivery-check wake | One per watering, 1.5 s at 60 mA | 0.01 |
| LED flashes | A few seconds a day at about 5 mA | 0.01 |
| Divider leak | 2.1 µA continuous | 0.05 |
| Everything except sleep | Sum | about 1.6–1.9 |

That leaves about 7 mAh a day for sleep, so six months holds only if measured sleep current stays under about 0.3 mA. That one number decides the battery claim: measure it on the breadboard (G8) and on the soldered, boxed stake (G23), with the pump and sensor pins held low and the float switch pull-up off.

Retries: a failed connection attempt can cost up to 20 s of radio. So the stake scans first and only connects when a known network is visible, and a failed sync is retried only at the next scan slot or button press.

### 6.5 Reservoir sensing

Two signals, two jobs. **The float switch** is a hard interlock: when it reads low, the pump does not run, with no override. Running these pumps dry damages them. **The computed estimate** (volume pumped since the last refill) powers "refill in about N days" on the dashboard.

- **Fail-safe wiring:** mount the float so its switch is closed while water is above the mark. An open switch, whether from low water or a broken wire, reads HIGH and blocks the pump (R-13).
- **Trip point:** about 20% of the water left. Find it by draining a full jar and marking the point.
- **Debounce:** sample 5 times over about half a second; the majority counts. The low-water alert needs 2 readings in a row, so a bump or slosh doesn't cause a false alarm.
- **Battery:** enable D7's internal pull-up only while reading it, so a closed switch draws no current during sleep (R-15).
- Measure jar\_capacity\_ml by filling the jar from a measuring cup.
- The estimate can't see a manual top-up or a leak, so the owner presses Refill in the app.

### 6.6 Moisture calibration (DEC-15)

moisture\_pct is a calibrated, sensor-specific index from 0 to 100. It is not laboratory water content, and nothing in the product may imply that.

```latex
\text{moisture\_pct} = \operatorname{clamp}_{0}^{100}\left(100 \times \frac{\text{dry\_raw} - \text{raw}}{\text{dry\_raw} - \text{wet\_raw}}\right)
```

- Capacitive sensors read a higher raw number when drier, so dry\_raw is larger than wet\_raw.
- **Method:** record dry\_raw and wet\_raw in the real potting soil, dried and then soaked. Also record the air and water readings in the test log as a reference.
- **Repeatability:** five readings in the same soil condition within 2 points (G4).
- **Probe care:** seal the cut edges with clear nail polish or conformal coat before use; edge corrosion shifts the baseline. Recalibrate every 3 months.
- **Placement:** 2 to 3 inches from the stem, never deeper than the line marked on the probe.
- **Guards (server side, 10.10):** the numbers are checked when entered, cleared when the sensor or the plant's stake changes, and entered next to the stake's latest raw reading.

### 6.7 Enclosure, charging and reflashing (DEC-29)

- **Box:** IP65, 100 × 68 × 50 mm. Everything electrical sits above the water line.
- **Openings:** three PG7 glands (pump wires, moisture probe cable, float switch cable); one waterproof USB-C port; one waterproof button; one sealed LED holder; and a glass slide window for the light sensor. Design places them in the enclosure drawing (D6).
- **Routine charging and flashing** go through the USB-C port with the box shut. Keep its cap on except while plugged in, and point the port down or sideways, never up.
- **The screwed, gasketed lid** opens only for battery swaps. Repeat the waterproof test (G18) after every opening.
- Silicone cures 24 hours before any water test. Glands are sized to the measured cable.
- Most tuning needs no reflash: threshold, interval, pump time, sync window and calibration all arrive in the config reply.
- An interrupted firmware update must leave the pump off (G21).

### 6.8 Light sensor (DEC-30)

- Under a glass slide siliconed into the lid, facing up, unshaded.
- **Placement test (G25):** readings with the plant at different sizes and with leaves shading the lid, plus a labelled sketch. If readings mostly describe shade on the lid rather than light reaching the plant, record that in the report.
- **The LED must never be lit during a light reading.** The firmware reads light first, then shows the LED.
- **Units:** lux, a human-brightness measure. Fine for comparing days, which is all the model needs. Never claim it measures plant light (PPFD or DLI).
- **Mode:** one high-resolution one-time reading per wake, after which the sensor powers itself down.

### 6.9 Pump and tubing maintenance

- Opaque or light-blocking tubing and an opaque jar. Light on standing water grows algae, which fouls the intake.
- The intake filter must not cut flow by more than 20% against the calibrated rate (G26).
- Route the tube so its highest point sits above the jar's water line.
- Rinse the jar monthly. Design writes the cleaning and inspection routine (D10).

### 6.10 Breadboard first, then solder

- Breadboard everything you can supervise. Solder and seal only what has to run unattended.
- Keep water and breadboard apart. 3.7 V is harmless to people, but water bridging two contacts can short the lithium cell, the one genuinely hazardous failure here.
- Bench tests use cups, not pots. Power from USB during bench work; leave the battery unplugged except when testing battery behaviour.
- The breadboard phase ends where unattended running begins. Loose friction-fit wires produce data that looks exactly like a sensor bug.
- Solder at home, ventilated, with a fan pushing smoke away. Supervision is confirmed before the first joint (A17, Q25).

### 6.11 Mechanical summary

| Item | Specification |
| --- | --- |
| Enclosure | IP65 box, 100 × 68 × 50 mm, gasketed lid with four screws |
| Openings | Three PG7 glands, USB-C port, button, LED holder, light window (D6) |
| Stake body | Dowel or PVC carrying the box above the soil |
| Moisture probe | 2–3 inches from the stem, no deeper than its marked line |
| Light sensor | Under glass in the lid, facing up |
| Reservoir | Opaque glass jar; capacity measured and recorded as jar\_capacity\_ml |
| Pump | Submerged near the jar bottom, with a foam or mesh cover on the intake |
| Float switch | In the jar, tripping with about 20% of the water left; closed while water is above the mark |
| Tube | 6 mm silicone, black or wrapped; length taken from the enclosure drawing (D6) |

## 7. Firmware

The stake wakes every hour, reads its sensors, saves the reading, decides whether to water, syncs if it's time, and sleeps. On this chip every wake from deep sleep restarts the program from the top, so "boot" below means a real power-up, and "wake" means any start, including a timer or button wake.

### 7.1 The wake cycle

```
# ---------- compiled-in constants: nothing from the server can change these ----------
RUNTIME_CAP_MS     = 15000   # DEC-11
DAILY_CAP          = 2       # waterings per rolling 24 h, manual ones included
LOW_BATT_STOP_MV   = 3300
LOW_BATT_WARN_MV   = 3500    # LED "attention" only; the server raises the alert
SANITY_MARGIN      = 0.10    # of (dry_raw - wet_raw), each side (placeholder)
DELIVERY_CHECK_MIN = 45      # DEC-13
MIN_RISE_PTS       = 3.0     # DEC-13
FAILED_STOP        = 2       # failed checks in a row that stop automatic watering
CLOCK_FRESH_H      = 24      # DEC-17
WATCHDOG_S         = 30      # Q23 (placeholder)
READ_EVERY_MIN     = 60      # compiled in; changing it needs a reflash
MOISTURE_SAMPLES   = 5       # take the median (placeholder)
FALLBACK_PUMP_MS   = 8400    # used until the server sends a calibrated pump time

# RTC memory survives deep sleep but not power loss. It holds:
#   next_read_at, last_water_at, waterings_24h[], pending_check,
#   last_ntp_at, clock_known, synced_on_date, button_stuck
# Flash (NVS) survives everything; keys in 7.7.

setup():                                   # runs at power-up AND after every wake
  drive D10 (pump gate) LOW                # always the very first line
  start watchdog(WATCHDOG_S)
  release GPIO hold on D10 and D3; drive D6 (LED) LOW
  if reset reason is not "deep-sleep wake":   # power-on, brownout, watchdog or crash
      boot_id += 1                         # saved to flash
      clear RTC memory
      last_water_at = now                  # interval lock restarts as if just watered
      waterings_24h = [now]                # counts as 1 of the 2 allowed
      clock_known = false                  # time_status "unknown" until NTP succeeds
  by_button = (wake cause is D2 going LOW)
  read_now  = (now >= next_read_at) or by_button   # the button forces a fresh reading (DEC-06)

  if read_now:  do_reading()
  if now >= next_read_at:  next_read_at += READ_EVERY_MIN   # a button reading doesn't shift the hourly schedule
  if pending_check and now >= pending_check.due:  do_delivery_check()
  if read_now:  try_auto_watering()
  status = worst(last_status from the server, local_status())
  if by_button:                      led_show(status, 5 s)        # Q26 placeholder
  elif read_now and status != "ok":  led_show(status, 1 s)
  if by_button or sync_due():        do_sync()
  go_to_sleep()

do_reading():
  D3 HIGH; wait 100 ms; raw = median of MOISTURE_SAMPLES reads on D0; D3 LOW
  lux = one high-resolution BH1750 read, or null on an I2C error   # LED is off here
  battery_mv = mean of 16 reads on D1 x 2 x batt_cal
  enable D7 pull-up; reservoir_low = majority of 5 reads over ~500 ms of D7 == HIGH;
  disable D7 pull-up                                              # HIGH = open = low water
  if dry_raw and wet_raw are known:
      m = SANITY_MARGIN x (dry_raw - wet_raw)
      sensor_fault = raw < wet_raw - m or raw > dry_raw + m
      moisture_pct = null if sensor_fault
                     else clamp(100 x (dry_raw - raw) / (dry_raw - wet_raw), 0, 100)
  else:
      moisture_pct = null; sensor_fault = false
  read_ctr += 1
  buffer_save_reading(read_ctr, boot_id, uptime_s, device_time or none, time_status,
                      raw, moisture_pct, lux, battery_mv, reservoir_low, sensor_fault)

try_auto_watering():                       # all must hold
  moisture_pct is not null                 # calibrated, no sensor fault
  and moisture_pct < moisture_threshold
  and hours since last_water_at >= min_interval_hours
  and not reservoir_low
  and battery_mv >= LOW_BATT_STOP_MV
  and count of waterings_24h in the last 24 h < DAILY_CAP
  and failed_streak < FAILED_STOP
  and no pending_check                     # never water again before the last check ran
  -> run_pump(min(pump_duration_ms, RUNTIME_CAP_MS), trigger="auto", request_id=none)

run_pump(ms, trigger, request_id):
  if pending_check: mark that earlier event's delivery "unchecked"; pending_check = none
  D10 HIGH; wait ms (feeding the watchdog); D10 LOW
  event_ctr += 1; last_water_at = now; add now to waterings_24h
  buffer_save_event(event_ctr, boot_id, uptime_s, device_time, time_status, ms,
                    trigger, request_id, moisture_before = latest moisture_pct,
                    delivery = "unchecked")
  pending_check = (event_ctr, due = now + DELIVERY_CHECK_MIN, moisture_before)

do_delivery_check():
  D3 HIGH; wait 100 ms; raw = median read; D3 LOW; convert as in do_reading
  if moisture_pct is null or pending_check.moisture_before is null:  result = "unchecked"
  elif moisture_pct - moisture_before >= MIN_RISE_PTS:  result = "ok";  failed_streak = 0
  else:  result = "failed"; failed_streak += 1         # failed_streak lives in flash
  update that event's delivery in the buffer; pending_check = none
  # the check reading is not stored as an hourly reading

local_status():
  fault     if reservoir_low, battery_mv < LOW_BATT_STOP_MV, failed_streak >= FAILED_STOP,
               sensor_fault on the latest reading, or button_stuck
  attention if battery_mv < LOW_BATT_WARN_MV, or dry_raw/wet_raw unknown
  ok        otherwise

led_show(status, seconds):                 # Q21/Q26 placeholder: single-colour LED on D6
  repeat for `seconds`: ok = 1 blink, attention = 2 blinks, fault = 3 fast blinks, then pause

go_to_sleep():
  D10 LOW; D3 LOW; D6 LOW; enable GPIO hold on D10 and D3
  wake timer = earliest of: next_read_at, pending_check.due, next_scan_slot()
  if D2 reads HIGH: enable wake on D2 LOW; button_stuck = false
  else:             button_stuck = true    # timer wakes only until D2 reads HIGH again
  deep sleep
```

**Three ordering rules hidden in that list:**

- **Save before deciding.** If the watering logic crashes, the reading is already safe.
- **Light before LED.** The light reading happens before the LED shows anything, so the LED can't brighten its own reading.
- **Network last, and optional.** A stake that never sees a network again keeps watering correctly on its last saved settings. The only loss is a stale dashboard.

### 7.2 Failsafes — all mandatory, all in firmware

No server response and no model output can override any of these. The model suggests numbers; the firmware decides whether to obey them.

| Failsafe | Rule |
| --- | --- |
| Sanity check | A reading outside the calibrated range plus margin is a sensor fault: moisture\_pct is null and the stake does not water automatically. A disconnected sensor often reads bone dry; that must never trigger the pump |
| Calibration required | Without both dry\_raw and wet\_raw, no watering of any kind |
| Reservoir interlock | Float switch low (or its wire broken) means the pump does not run. No override |
| Interval lock | Never water automatically twice inside min\_interval\_hours, whatever the readings say |
| Runtime cap | 15 s per activation, compiled in |
| Daily cap | At most two waterings per rolling 24 hours, manual included |
| Failed delivery | Two failed checks in a row stop automatic watering. A manual watering whose check passes resets the streak and resumes it |
| Low battery | Below 3.3 V, no watering. A brownout mid-pump is worse than a dry plant |
| Offline mode | No network: keep watering on the last saved config and keep buffering |
| Boot state | Pump pin LOW as the first action of every start; the 10 kΩ gate pulldown holds it off before that; the watchdog restarts a stuck program |
| Sleep state | Pump pin and sensor power held LOW during deep sleep |
| Power loss | The interval lock restarts as if a watering just happened and the daily count starts at 1, so a power cut can delay a watering but never double one |
| Stuck button | If D2 is still LOW when the stake goes to sleep, button wakes are switched off until D2 reads HIGH again, so a stuck button can't drain the battery |

A pump-driver fault (a stuck pin or shorted MOSFET running the pump with no command) is not covered by firmware. The jar size limits the damage. A hardware cutoff is Q18.

### 7.3 Manual watering (water now)

- The owner presses Water now; the server queues a request with an id. At the stake's next sync, the config reply carries water\_request\_id (R-14).
- The stake stores the last id it handled (last\_request\_id) and acts on each id once.
- A manual watering skips only the moisture threshold and the interval lock. It still obeys the runtime cap, the daily cap, the reservoir interlock, the low-battery stop and the calibration requirement. It also runs while automatic watering is paused by failed checks.
- If a limit blocks it, the stake logs an event with duration\_ms 0, trigger "manual", the request\_id and delivery "refused". Refused events never count toward failed checks.
- The manual event uploads at the following sync, once its delivery check has run. The dashboard shows each state honestly (10.3).

### 7.4 Sync schedule and the button (DEC-05, DEC-06)

- **Window:** the stake scans for a known network every scan\_step\_min (10) from window\_start\_local (11:30) to window\_end\_local (12:40) in local time: 8 scan slots a day. The times arrive in the config reply; the compiled defaults are the same.
- **Scan first, connect only if seen:** a scan costs about 2 s. The stake connects only when a network from its list is visible.
- **Once a day:** after the first successful sync of the day, the stake skips the remaining slots until tomorrow, unless the button is pressed.
- **Where:** in period 4 Kayden turns on his phone hotspot. Over breaks the stake is at Kayden's home, so home WiFi syncs it every day, weekends included. Weekends at school simply buffer.
- **No clock:** after a power loss the stake doesn't know the time, so it can't find the window. It scans at every hourly wake until one sync succeeds and sets the clock (R-11).
- **Button:** pressing it wakes the stake at once. It takes a fresh reading, shows the LED status for 5 s, then syncs regardless of the window. It covers arriving late, leaving early and fresh data during a demo.
- There is no "sync now" in the app: a sleeping stake can't hear the server. That's also why water now is a queued request.

**One sync, step by step:**

1. Scan; connect to the first visible network from wifi\_list (WIFI\_TIMEOUT\_S, placeholder 20 s). None: give up until the next slot.
2. Set the clock by NTP (pool.ntp.org, then time.google.com). On success: clock\_known = true, last\_ntp\_at = now.
3. Read sent\_time (null if NTP failed), sent\_boot\_id and sent\_uptime\_s.
4. Send batches of at most BATCH\_MAX (placeholder 48) items, oldest first, HTTP timeout HTTP\_TIMEOUT\_S (placeholder 15 s). Always send at least one POST, even an empty one, so a fresh config arrives. Stop after 60 s of radio time.
5. On HTTP 200: confirm that batch in the buffer, reset dropped\_count to 0, save the config to flash. Anything else: stop and wait for the next slot.
6. If the config carries a water\_request\_id different from last\_request\_id: save it as last\_request\_id, then do the manual watering (7.3).
7. If any POST succeeded and the clock is known, synced\_on\_date = today. WiFi off.

### 7.5 Offline buffer (DEC-16)

The stake holds readings until the server confirms it stored them. Between syncs the flash is all there is, so it must survive sleep, reset and power loss.

- **Storage:** LittleFS, the small file system built into the Arduino ESP32 core. It survives power cuts and spreads wear on its own. It uses the board's data partition; confirm its size on the bench (Q6).
- **Readings:** files of 24 records each (about a day), in /r/, named by the first record's counter, e.g. /r/00000123.bin.
- **Events:** one file, /e/events.bin. Events are never deleted by the stake: about 130 a year at 32 bytes is about 4 KB a year.
- **Writing:** open, append one 32-byte record, close. LittleFS commits on close, so a power cut loses at most the record being written.
- **Bookmarks:** acked\_read\_ctr and acked\_event\_ctr in flash are the highest counters the server has confirmed. Uploads send records above them, oldest first.
- **Held back:** an event whose delivery check is still pending is not sent until the check has run (at most 45 min).
- **After an HTTP 200:** move the bookmarks to the highest counters in that batch. Delete any readings file whose last record is at or below acked\_read\_ctr.
- **Full:** at most 60 readings files (1,440 readings, about 60 days). Starting a 61st file deletes the oldest one, and any of its unsent readings are added to dropped\_count. dropped\_count is sent with the next upload, which turns it into a labelled gap on the chart.
- **Interface:** all of this sits behind three functions: buffer\_save(record), buffer\_peek(max) (the oldest unsent records) and buffer\_ack(batch). The laptop unit tests use a fake buffer behind the same functions.

**Record layout (32 bytes, little-endian):**

| Bytes | Reading record | Event record |
| --- | --- | --- |
| 0–3 | read\_ctr (uint32) | event\_ctr (uint32) |
| 4–5 | boot\_id (uint16) | boot\_id (uint16) |
| 6–9 | uptime\_s (uint32) | uptime\_s (uint32) |
| 10–13 | device\_time, Unix seconds UTC (uint32; 0 = unknown) | device\_time (uint32; 0 = unknown) |
| 14–15 | moisture\_raw (uint16) | duration\_ms (uint16) |
| 16–17 | moisture\_pct × 10 (int16; −1 = null) | moisture\_before × 10 (int16; −1 = null) |
| 18 | reserved (0) | trigger: 0 auto, 1 manual, 2 test (uint8) |
| 19 | reserved (0) | delivery: 0 unchecked, 1 ok, 2 failed, 3 refused (uint8) |
| 20–23 | lux (uint32; 0xFFFFFFFF = null) | request\_id (uint32; 0 = none) |
| 24–25 | battery\_mv (uint16) | reserved (0) |
| 26 | flags: bit 0 reservoir\_low, bits 1–2 time\_status (0 synced, 1 estimated, 2 unknown), bit 3 sensor\_fault | flags: bits 1–2 time\_status |
| 27 | CRC-8 of bytes 0–26 | CRC-8 of bytes 0–26 |
| 28–31 | reserved (0) | reserved (0) |

soil\_temp\_c is not stored: it is always null in v1 (DEC-08).

### 7.6 Time and timestamps (DEC-17)

- Everything is stored in UTC. The stake has no clock battery, so after a power loss it doesn't know the time until it syncs. It flags that rather than inventing precision.
- The clock is set by NTP at every successful sync and keeps running through deep sleep.
- **synced:** the clock was set this boot, within the last 24 hours. **estimated:** set this boot, but more than 24 hours ago. **unknown:** no NTP success since the last power-up.
- Every reading and event also carries boot\_id and uptime\_s (seconds since power-up, from the sleep-proof RTC clock, not the CPU timer, which stops in deep sleep).
- At upload the server re-dates every item from the current boot whose status is estimated or unknown, working back from the sync time (10.1). Those items become "estimated" with a good time and stay usable for learning.
- Under the sync window, readings older than 24 hours (most of every weekend) arrive as estimated. That's expected; the server's re-dating fixes their times.
- Items from a boot that ended before any sync stay unknown, because time spent powered off can't be measured. They are never charted and are excluded from learning.
- G16 measures the real clock drift over 24 hours.

### 7.7 Flash settings (NVS namespace "sprout")

| Key | Type | Meaning |
| --- | --- | --- |
| serial, api\_key, server\_url | string | Identity and endpoint, written by the provisioning tool |
| wifi\_list | blob | Up to 3 network names and passwords |
| dry\_raw, wet\_raw | int | Calibration from the config reply (absent = none) |
| threshold, min\_interval\_h, pump\_ms | float or int | Last config received |
| window\_start, window\_end, scan\_step, tz\_posix | int or string | Sync window and time-zone rule from the config reply |
| last\_status | string | Server status, for the LED |
| boot\_id | uint | Up by one at every power-up |
| read\_ctr, event\_ctr | uint | Counters behind reading\_id and event\_id |
| acked\_read\_ctr, acked\_event\_ctr | uint | Buffer bookmarks (7.5) |
| dropped\_count | uint | Readings lost to a full buffer since the last successful sync |
| failed\_streak | uint | Failed delivery checks in a row |
| last\_request\_id | uint | Last water request handled |
| batt\_cal | float | Battery correction factor from G7 (default 1.0) |

The runtime cap, daily cap, battery limits, sanity margin and watchdog timeout are compiled constants, not NVS values, so nothing from the server can change them.

### 7.8 WiFi networks

- The provisioning tool writes up to three networks into wifi\_list: Kayden's phone hotspot, Kayden's home WiFi (needed for breaks) and a spare.
- The firmware tries them through WiFiMulti, a library that connects to whichever listed network is visible.
- Changing a network needs a USB re-provision, not a new firmware build.
- Only WPA2-Personal networks work. School logins and captive portals (sign-in web pages) do not, which is why G2 tests the real networks first.

### 7.9 Toolchain, code layout and updates (DEC-04)

- **Build:** PlatformIO with the Arduino-ESP32 core, using the community pioarduino platform so the current core 3.x works; board seeed\_xiao\_esp32c3. Pin every version in platformio.ini.
- **Libraries:** BH1750 (Christopher Laws), ArduinoJson, WiFi and WiFiMulti, WiFiClientSecure, HTTPClient, Preferences (NVS), LittleFS; ESP-IDF calls for deep-sleep wake on D2, GPIO hold and NTP time.
- **Layout:** firmware/src/logic/ holds everything that doesn't touch hardware (calibration maths, the watering rule, every failsafe, record packing, status). It runs as unit tests on a laptop (pio test -e native). Separate modules for sensors, buffer, network, LED and power.
- **HTTPS:** the stake carries the root certificate bundle needed to check the server's certificate.
- **Updates:** over USB through the waterproof USB-C port (DEC-29). The pump stays off during an update and after an interrupted one, guaranteed by the boot rule and the gate pulldown (G21). Over-the-air updates are out of scope.

## 8. The API contract

This section is the agreed shape of data between the stake, the server and the dashboard (DEC-18 to DEC-22). It freezes on Fri 13 Nov; any later change is a group decision recorded here.

JSON in one sentence: a form with labelled boxes. "moisture\_pct": 42.5 is a label and a value; curly braces wrap a form; square brackets hold a list of forms. Comments after # in the examples below are explanations, not part of the JSON.

### 8.1 Stake to server: POST /api/readings

```
POST /api/readings
Authorization: Bearer <device key>
Content-Type: application/json

{
  "serial": "SPROUT-001",
  "firmware_version": "1.0.0",
  "sent_time": "2026-12-08T19:31:04Z",      # null if the clock sync failed
  "sent_boot_id": 17,
  "sent_uptime_s": 106264,
  "dropped_count": 0,
  "readings": [
    {
      "reading_id": "SPROUT-001-000123",
      "boot_id": 17,
      "uptime_s": 86400,
      "device_time": "2026-12-08T14:00:00Z",  # null if unknown
      "time_status": "synced",                 # synced | estimated | unknown
      "moisture_raw": 2025,
      "moisture_pct": 42.5,                    # null without calibration or on a sensor fault
      "lux": 8200,                             # null on a light-sensor error
      "battery_mv": 3810,
      "reservoir_low": false,
      "sensor_fault": false,
      "soil_temp_c": null                      # reserved; always null in v1 (DEC-08)
    }
  ],
  "events": [
    {
      "event_id": "SPROUT-001-E000045",
      "boot_id": 17,
      "uptime_s": 69120,
      "device_time": "2026-12-08T09:12:00Z",
      "time_status": "synced",
      "duration_ms": 8400,
      "trigger": "auto",                       # auto | manual | test
      "request_id": null,                      # the water request a manual watering answers
      "moisture_before": 28.1,                 # null if unknown
      "delivery": "ok"                         # ok | failed | unchecked | refused
    }
  ]
}
```

IDs: reading\_id is the serial, a hyphen, and read\_ctr zero-padded to 6 digits. event\_id is the serial, "-E", and event\_ctr zero-padded to 6 digits. Zero-padding keeps them sortable.

### 8.2 Server to stake: the config reply

Sent with HTTP 200 only after every item in the batch is safely written, or was already stored. Only then may the stake confirm that batch in its buffer.

```
{
  "moisture_threshold": 30.0,
  "min_interval_hours": 57.6,
  "pump_duration_ms": 8400,
  "window_start_local": "11:30",
  "window_end_local": "12:40",
  "scan_step_min": 10,
  "tz_posix": "PST8PDT,M3.2.0,M11.1.0",  # POSIX time-zone rule the chip understands
  "dry_raw": 2650,                       # null until calibrated: the stake will not water
  "wet_raw": 1180,
  "water_request_id": null,              # an integer when a water-now request is waiting
  "reservoir_pct": 62,                   # estimate; stored, not acted on
  "status": "ok"                         # ok | attention | fault; feeds the LED
}
```

The moisture threshold is the plant's species value and never changes. The minimum interval between waterings starts from the species table and is gradually replaced by a number learned from the pot (section 11). The stake follows orders; it has no idea it is being taught.

### 8.3 Field rules

| Field | Rule | Valid range |
| --- | --- | --- |
| serial | Which stake is talking; must already exist in devices | "SPROUT-" + 3 digits |
| firmware\_version | Version string | Up to 32 characters |
| sent\_time, sent\_boot\_id, sent\_uptime\_s | Read just after the clock-sync attempt; the anchor for re-dating (10.1) | sent\_time within 5 min of server time when not null |
| dropped\_count | Readings lost to a full buffer since the last successful sync; above 0 means the chart draws a labelled gap | 0 or more |
| reading\_id, event\_id | Stable unique IDs; re-sending a batch never creates duplicate rows | Format in 8.1 |
| boot\_id, uptime\_s | Power-up counter and seconds since power-up | 0 or more |
| device\_time | UTC time of the measurement, or null if unknown | Not in the future (5 min slack), not older than 90 days |
| time\_status | synced, estimated or unknown (7.6) | Enum |
| moisture\_raw | Raw probe value, always kept | 0 to 4095 |
| moisture\_pct | Calibrated index, not water content | 0 to 100, or null |
| lux | Light in lux; relative only | 0 to 120,000, or null |
| battery\_mv | Calibrated battery voltage in millivolts (3810 = 3.81 V) | 2,500 to 4,500 |
| reservoir\_low | True when the float switch is open | Boolean |
| sensor\_fault | True when moisture was outside the sanity range | Boolean |
| soil\_temp\_c | Reserved | Always null in v1 |
| duration\_ms | How long the pump ran (0 if refused) | 0 to 15,000 |
| trigger | auto, manual or test (bench runs; never used for learning) | Enum |
| request\_id | The water request a manual watering answers; null otherwise | A water\_requests id, or null |
| moisture\_before | moisture\_pct just before watering | 0 to 100, or null |
| delivery | Result of the delivery check, or refused | Enum |

- A watering event records that the pump ran, not that water reached the pot. The delivery check is evidence from the moisture sensor, not flow measurement.
- Volume is not sent. The server computes volume\_ml = duration\_ms ÷ 1000 × ml\_per\_s from the stake's calibration.
- An item outside its range is written to reject\_log with a reason and skipped. The batch still gets 200, so one bad value can't jam the buffer. An item rejected only for age is also recorded in data\_gaps, so the chart shows a gap instead of losing it silently.

### 8.4 Endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | /api/readings | Device key | Batch upload; returns the config |
| POST | /api/register | None | Create an account |
| POST | /api/login | None | Start a session |
| POST | /api/logout | Session | End a session |
| GET | /api/me | Session | The current account |
| GET | /api/plants | Session | The account's plants with status |
| POST | /api/plants | Session | Create a plant: species, name, calibration, sizes, stake |
| GET | /api/plants/:id | Session | One plant in full |
| PATCH | /api/plants/:id | Session | Rename; change target\_ml or jar\_capacity\_ml; recalibrate (R-7) |
| GET | /api/plants/:id/readings?days=14 | Session | Chart data, 1 to 90 days |
| GET | /api/plants/:id/events?days=14 | Session | Watering markers, 1 to 90 days |
| GET | /api/plants/:id/model | Session | Species vs learned interval, cycle count, fit history |
| POST | /api/plants/:id/water-now | Session | Queue a manual watering |
| GET | /api/plants/:id/water-requests | Session | The latest request and its state |
| POST | /api/plants/:id/refill | Session | Mark the jar refilled; reset the estimate |
| POST | /api/plants/:id/reset-learning | Session | New learning epoch, with new calibration |
| GET | /api/plants/:id/alerts | Session | Open alerts |
| POST | /api/alerts/:id/dismiss | Session | Hide an alert until it clears |
| POST | /api/plants/:id/diagnose | Session | Upload a leaf photo, get a diagnosis (optional feature) |
| GET | /api/plants/:id/diagnoses | Session | Diagnosis history |
| GET | /api/photos/:id/thumb and /api/photos/:id/full | Session | Diagnosis photo, owner only |
| GET | /api/species?q=basil | Session | Species search, up to 10 results |
| POST | /api/devices/claim | Session | Link a stake to the account by claim code |
| GET | /api/devices | Session | The account's stakes, with each one's latest raw moisture reading |
| PATCH | /api/devices/:id | Session | Rename, assign to a plant, retire or un-retire (a pause, 8.5.1), or mark "sensor replaced" |

Every session endpoint checks that the plant, stake, alert or photo belongs to the logged-in account, including water now, reset and diagnosis uploads. Response shapes are in 13.2.

### 8.5 Linking a stake to an account (DEC-21)

The stake has no idea who owns it. The everyday version is a gift card: it sits on a rack belonging to nobody, with a code on the back; entering the code makes it yours.

1. **Create.** create\_device makes the devices row and prints the serial, a random device key and a claim code (format WORD-4CHARS, such as BASIL-7X2K), once. Only hashes of the key and claim code are stored.
2. **Provision.** The provisioning tool writes the serial, key, network list and server URL into the stake over USB, then flashes the firmware. The claim code goes on a sticker on the stake.
3. **Before claiming.** The stake posts as normal. The server stores its readings with no plant (plant\_id null) and replies with no calibration, so the stake never waters. Unknown serials get 401.
4. **Claim.** The user logs in, opens Add device and types the code. The server sets the owner and burns the code. Any later attempt with that code returns 404, because the server no longer holds it.
5. **Set up.** The user picks a species, names the plant, enters calibration next to the stake's latest raw reading, and assigns the stake. Readings stored before setup are attached to the plant, so nothing is lost.

This is also the best thirty seconds of the demo: hold up the stake, read the sticker, type it into the app on the projector, and the dashboard fills.

**Two codes, two jobs.** The device key is the stake's ID badge: in the firmware, never typed by a person, proving a real stake is talking. The claim code is the sticker: proving you physically hold the stake, typed once, then dead.

#### 8.5.1 Retiring and un-retiring a stake (R-20)

Retire is a reversible pause, not a removal.

- Retiring (PATCH /api/devices/:id with retired true) sets retired\_at. It never clears the owner, the plant link, the plant's calibration or the device key hash.
- A retired stake authenticates and syncs normally. Its config reply carries null dry\_raw and wet\_raw and status "attention" (10.2). Null calibration already means the stake will not water (7.2), so the stake pauses with no firmware change. It keeps taking readings and buffering them.
- Un-retiring (retired false) clears retired\_at. The stake gets its calibration back in the next config reply and resumes at its next sync.
- While retired: Water now and Refill return 409 device\_retired (10.3), and assigning the stake to a different plant is refused with the same code. Un-retire it first.
- A retired stake does not raise the offline alert (10.4), and a cycle containing readings taken while paused is excluded from learning (11.2).
- To give a stake to someone else, run create\_device again and re-provision over USB, the same route as a leaked key (8.7). Retiring never releases a stake.

### 8.6 Accounts and sessions

- Registration is open with email, password and time zone (an IANA name such as America/Los\_Angeles). Passwords need at least 10 characters and are hashed with argon2.
- Login sets a cookie named sprout\_session: HttpOnly, Secure, SameSite=Lax, lasting 14 days. The server stores a SHA-256 hash of the cookie's token in sessions.
- Login is limited to 5 attempts per minute per IP address.
- No email verification and no emailed reset in v1; the team resets passwords by hand.
- Every page redirects anyone not signed in to the log-in screen.

### 8.7 Security baseline

- HTTPS for everything over the network. No reusable credential in plain text.
- Each stake has its own random device key, sent as Authorization: Bearer, never committed to the repository, and stored on the server only as a hash (DEC-18). A leaked key is replaced by re-provisioning over USB.
- Every stake upload is authenticated and checked against the schema.
- Dashboard actions need a logged-in user. Writes need Content-Type: application/json, except the photo upload.
- Photo uploads: JPEG or PNG only, under 5 MB, checked before any vision API call.
- The pump's runtime, daily and interval limits are enforced in firmware, so they hold even if the server is compromised.
- Credentials stay out of the repository and out of demo screenshots.

### 8.8 Timestamps and time zones

- Store UTC everywhere. Never subtract hours anywhere in the database, the API or the firmware to "fix" an offset. That works until the first Sunday in November, then every chart is an hour off.
- The browser converts UTC to the viewer's local time.
- The server uses the account's time zone for three things that count local days or hours: the low-light alert, the offline alert's weekday hours, and the chart's day ticks. It also turns that time zone into the POSIX rule sent to the stake as tz\_posix (10.2).

## 9. Database (DEC-23)

MySQL 8.4 LTS, InnoDB, utf8mb4, every time stored as DATETIME(3) in UTC. Eli's table definitions are the base, with v2's additions and the merge's fixes. readings is by far the largest table, about 8,700 rows per stake per year, and the (plant\_id, device\_time) index carries every chart query.

### 9.1 Tables at a glance

| Table | Holds |
| --- | --- |
| accounts | Logins, hashed passwords, time zone |
| sessions | Login sessions behind the cookie |
| species | Cited reference data per plant type, plus display data from Perenual |
| plants | One plant: owner, species, current calibration, dose, jar, learning epoch |
| devices | One stake: serial, key hash, claim code hash, owner, plant, pump flow rate |
| calibrations | Every calibration ever entered, with its reason (a row with both numbers NULL records a clearing) |
| water\_requests | The queue behind Water now, with each request's outcome |
| readings | The hourly time series |
| events | Every watering, refused ones included |
| data\_gaps | Labelled gaps from dropped\_count |
| cycles | Watering-to-watering cycles, valid or not, with the reason |
| model\_fits | Every model fit and its evaluation |
| alerts | Raised and cleared alerts |
| diagnoses | Leaf photos and their results (optional feature) |
| reject\_log | Rejected uploads and items, with reasons |

The config sent to a stake is computed on each upload (10.2), not stored, so there is never a stale copy.

### 9.2 Definitions

These are the source for the Alembic migrations. Tables are listed in creation order. Foreign keys use ON DELETE RESTRICT unless noted. trigger and condition are reserved words in MySQL, so the columns are trigger\_type and `condition`; the API calls them trigger and condition.

```sql
CREATE TABLE accounts (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,                 -- argon2
  timezone VARCHAR(64) NOT NULL DEFAULT 'America/Los_Angeles',
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
);

CREATE TABLE sessions (
  id CHAR(64) PRIMARY KEY,                             -- SHA-256 of the cookie token
  account_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(3) NOT NULL,
  expires_at DATETIME(3) NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE TABLE species (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  common_name VARCHAR(100) NOT NULL,
  scientific_name VARCHAR(150) NOT NULL,
  days_between_waterings DECIMAL(4,1) NOT NULL,
  light_hours DECIMAL(3,1) NOT NULL,
  water_threshold_pct DECIMAL(4,1) NOT NULL,
  source_url VARCHAR(500) NOT NULL,
  toxic_to_cats TINYINT(1) NULL,
  toxic_to_dogs TINYINT(1) NULL,
  perenual_id INT NULL,                                -- B7
  image_url VARCHAR(500) NULL,                         -- B7
  care_text TEXT NULL                                  -- B7, display only
);

CREATE TABLE plants (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  account_id BIGINT UNSIGNED NOT NULL,
  species_id INT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  dry_raw INT NULL,                                    -- current calibration; NULL = none
  wet_raw INT NULL,
  moisture_threshold DECIMAL(4,1) NOT NULL,            -- copied from species at creation
  target_ml DECIMAL(6,1) NOT NULL DEFAULT 60.0,        -- DEC-12
  jar_capacity_ml INT NOT NULL,
  ml_since_refill DECIMAL(8,1) NOT NULL DEFAULT 0,
  effective_interval_h DECIMAL(6,1) NULL,              -- last value used, for the 25% limit
  learning_epoch INT UNSIGNED NOT NULL DEFAULT 1,
  epoch_started_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  epoch_reason ENUM('created','repot','moved','soil_change','other') NOT NULL DEFAULT 'created', -- Q15
  is_simulated TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  FOREIGN KEY (account_id) REFERENCES accounts(id),
  FOREIGN KEY (species_id) REFERENCES species(id)
);

CREATE TABLE devices (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  serial VARCHAR(32) NOT NULL UNIQUE,
  key_hash VARCHAR(255) NOT NULL,                      -- argon2 hash of the device key
  claim_code_hash VARCHAR(255) NULL,                   -- NULL once burned
  claimed_at DATETIME(3) NULL,
  account_id BIGINT UNSIGNED NULL,
  plant_id BIGINT UNSIGNED NULL UNIQUE,
  name VARCHAR(100) NULL,
  ml_per_s DECIMAL(5,2) NULL,                          -- measured at G11
  firmware_version VARCHAR(32) NULL,
  last_seen DATETIME(3) NULL,
  retired_at DATETIME(3) NULL,                         -- set while retired (a pause, 8.5.1); NULL = active
  FOREIGN KEY (account_id) REFERENCES accounts(id),
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);

CREATE TABLE calibrations (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  device_id BIGINT UNSIGNED NULL,
  dry_raw INT NULL,                                    -- both NULL = calibration cleared (R-19)
  wet_raw INT NULL,
  reason ENUM('setup','recalibration','repot','sensor_replaced','reassigned') NOT NULL,
  set_at DATETIME(3) NOT NULL,
  FOREIGN KEY (plant_id) REFERENCES plants(id),
  FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE water_requests (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  requested_at DATETIME(3) NOT NULL,
  sent_at DATETIME(3) NULL,                            -- first config reply that carried it
  resolved_at DATETIME(3) NULL,
  outcome ENUM('pending','delivered','refused','expired') NOT NULL DEFAULT 'pending',
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);

CREATE TABLE readings (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NULL,                       -- NULL until the stake is set up (8.5)
  device_id BIGINT UNSIGNED NOT NULL,
  reading_id VARCHAR(40) NOT NULL UNIQUE,
  boot_id INT UNSIGNED NOT NULL,
  uptime_s INT UNSIGNED NOT NULL,
  device_time DATETIME(3) NULL,
  time_status ENUM('synced','estimated','unknown') NOT NULL,
  received_at DATETIME(3) NOT NULL,
  moisture_raw INT NOT NULL,
  moisture_pct DECIMAL(4,1) NULL,
  sensor_fault TINYINT(1) NOT NULL DEFAULT 0,
  lux INT UNSIGNED NULL,
  battery_mv INT NOT NULL,
  reservoir_low TINYINT(1) NOT NULL,
  soil_temp_c DECIMAL(4,1) NULL,                       -- reserved; always NULL in v1 (DEC-08)
  INDEX idx_readings_plant_time (plant_id, device_time),
  INDEX idx_readings_device_received (device_id, received_at),
  FOREIGN KEY (plant_id) REFERENCES plants(id),
  FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE events (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NULL,
  device_id BIGINT UNSIGNED NOT NULL,
  event_id VARCHAR(40) NOT NULL UNIQUE,
  boot_id INT UNSIGNED NOT NULL,
  uptime_s INT UNSIGNED NOT NULL,
  device_time DATETIME(3) NULL,
  time_status ENUM('synced','estimated','unknown') NOT NULL,
  received_at DATETIME(3) NOT NULL,
  duration_ms INT UNSIGNED NOT NULL,
  volume_ml DECIMAL(6,1) NULL,                         -- computed; NULL until ml_per_s is known
  trigger_type ENUM('auto','manual','test') NOT NULL,
  request_id BIGINT UNSIGNED NULL,
  moisture_before DECIMAL(4,1) NULL,
  delivery ENUM('ok','failed','unchecked','refused') NOT NULL,
  INDEX idx_events_plant_time (plant_id, device_time),
  FOREIGN KEY (plant_id) REFERENCES plants(id),
  FOREIGN KEY (device_id) REFERENCES devices(id),
  FOREIGN KEY (request_id) REFERENCES water_requests(id)
);

CREATE TABLE data_gaps (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  device_id BIGINT UNSIGNED NOT NULL,
  plant_id BIGINT UNSIGNED NULL,
  received_at DATETIME(3) NOT NULL,
  dropped_count INT UNSIGNED NOT NULL,
  gap_start DATETIME(3) NULL,                          -- latest stored reading before the gap
  gap_end DATETIME(3) NULL,                            -- oldest reading in the batch
  FOREIGN KEY (device_id) REFERENCES devices(id),
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);

CREATE TABLE cycles (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  epoch INT UNSIGNED NOT NULL,
  start_event_id BIGINT UNSIGNED NOT NULL,             -- events.id
  end_event_id BIGINT UNSIGNED NOT NULL,
  start_time DATETIME(3) NOT NULL,
  end_time DATETIME(3) NOT NULL,
  start_pct DECIMAL(4,1) NULL,
  end_pct DECIMAL(4,1) NULL,
  hours DECIMAL(7,2) NOT NULL,
  hours_to_threshold DECIMAL(7,2) NULL,
  rate_pct_per_hour DECIMAL(6,3) NULL,
  mean_daily_lux INT NULL,
  valid TINYINT(1) NOT NULL,
  exclusion_reason ENUM('manual_or_test_watering','failed_or_refused_event','sensor_fault',
    'reading_gap','data_gap_reported','unknown_time','too_few_readings',
    'non_positive_rate','calibration_changed','other') NULL,
  computed_at DATETIME(3) NOT NULL,
  UNIQUE KEY uq_cycle (plant_id, start_event_id),
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);

CREATE TABLE model_fits (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  epoch INT UNSIGNED NOT NULL,
  fitted_at DATETIME(3) NOT NULL,
  model_type ENUM('mean_interval','regression') NOT NULL,   -- DEC-24
  model_version VARCHAR(20) NOT NULL,
  in_use TINYINT(1) NOT NULL DEFAULT 0,                -- the fit that set effective_interval_h
  learned_interval_h DOUBLE NULL,
  intercept DOUBLE NULL,
  light_coef DOUBLE NULL,
  temp_coef DOUBLE NULL,                               -- reserved; always NULL in v1
  r2 DOUBLE NULL,
  cycle_count INT UNSIGNED NOT NULL,
  mae_learned_h DOUBLE NULL,                           -- G31: learned pipeline
  mae_species_h DOUBLE NULL,                           -- G31: species default
  mae_mean_h DOUBLE NULL,                              -- simple average, for the DEC-24 switch
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);

CREATE TABLE alerts (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  type ENUM('low_water','low_battery','low_light','device_offline',
            'failed_delivery','pump_shortfall') NOT NULL,
  raised_at DATETIME(3) NOT NULL,
  cleared_at DATETIME(3) NULL,
  dismissed TINYINT(1) NOT NULL DEFAULT 0,
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);

CREATE TABLE diagnoses (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  plant_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(3) NOT NULL,
  photo_path VARCHAR(500) NOT NULL,
  thumbnail_path VARCHAR(500) NULL,
  `condition` ENUM('healthy','underwatered','overwatered_or_root_rot',
    'nutrient_deficiency','too_much_light','too_little_light','pests',
    'fungal_or_leaf_spot','not_a_plant','unclear') NOT NULL,
  observation TEXT NULL,
  check_yourself TEXT NULL,
  search_term VARCHAR(200) NULL,
  advice TEXT NULL,
  provider VARCHAR(50) NOT NULL,
  raw_response MEDIUMTEXT NULL,                        -- stored on every call, failures too
  flagged_for_review TINYINT(1) NOT NULL DEFAULT 0,
  FOREIGN KEY (plant_id) REFERENCES plants(id)
);

CREATE TABLE reject_log (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  serial VARCHAR(32) NOT NULL,
  received_at DATETIME(3) NOT NULL,
  reason VARCHAR(200) NOT NULL,
  payload_excerpt VARCHAR(500) NULL
);
```

- At most one open alert (cleared\_at NULL) of each type per plant, enforced in code.
- At most one pending water request per plant, enforced in code.
- No photo-timeline table exists unless Q14 brings that feature into scope.
- No payment or phone data is stored anywhere.

### 9.3 Species seed data

Plant APIs return labels like "watering: average". The stake needs "water at 30%". No public API gives that number, because it depends on our sensor's calibration. So Design hand-researches ten species, each with a numeric threshold and a citation. Perenual then supplies names, photos, toxicity and care text for display only; it is never used for watering logic.

D1 delivers a CSV with one row per species and these columns: common\_name, scientific\_name, days\_between\_waterings, light\_hours, water\_threshold\_pct, toxic\_to\_cats, toxic\_to\_dogs, source\_url. Sources are university extension pages or seed-supplier growing guides, not blogs. Basil is one of the ten.

## 10. Server behaviour rules

These rules are what an AI agent needs to write the backend without guessing.

### 10.1 Handling POST /api/readings, in this order

1. Look up the stake by serial. Unknown serial, or a key not matching key\_hash → 401. A retired stake is not rejected: it continues below and receives the paused config in 10.2.
2. Validate the body against the schema in 8.1 → 422 on failure.
3. Open one database transaction.
4. **Readings:** an item outside its range in 8.3 is written to reject\_log and skipped. Otherwise insert it with plant\_id = the stake's current plant (NULL if none). A repeated reading\_id is ignored without error.
5. **Events:** same checks. volume\_ml = duration\_ms ÷ 1000 × ml\_per\_s (NULL while ml\_per\_s is unknown). If the event\_id already exists with delivery "unchecked" and the new copy says ok or failed, update delivery only; otherwise ignore the repeat.
6. **Re-date:** for every new item whose boot\_id equals sent\_boot\_id and whose time\_status is unknown or estimated, set device\_time = anchor − (sent\_uptime\_s − uptime\_s) and time\_status = "estimated". anchor is sent\_time, or received\_at when sent\_time is null. Items from earlier boots keep what they had (DEC-17).
7. If dropped\_count > 0, insert a data\_gaps row: gap\_start = the latest stored device\_time for this stake before this batch; gap\_end = the oldest device\_time in this batch.
8. Set devices.last\_seen = received\_at and firmware\_version.
9. Add each new, non-refused event's volume\_ml to plants.ml\_since\_refill.
10. For each new manual event with a request\_id: set that water request's outcome to "delivered" (or "refused" when delivery is refused) and resolved\_at = received\_at.
11. Commit. **Only after the commit succeeds** build the config (10.2) and return 200. If the config carries a water\_request\_id whose sent\_at is empty, set sent\_at = now. If the commit fails, return 503; the stake keeps its buffer and tries again at its next slot.

When a stake is assigned to a plant (claim and setup, or PATCH /api/devices), its earlier readings, events and data gaps with plant\_id NULL get that plant\_id. Nothing recorded before setup is lost.

### 10.2 Building the config reply

| Field | Rule |
| --- | --- |
| moisture\_threshold | plants.moisture\_threshold, copied from species.water\_threshold\_pct when the plant is created. The model never changes it |
| min\_interval\_hours | 0.75 × the effective interval (11.3), clamped to 12–720 h |
| pump\_duration\_ms | round(target\_ml ÷ ml\_per\_s × 1000), at least 1,000 and at most 15,000. Before ml\_per\_s is measured: 8,400. If the computed value is over 15,000, send 15,000 and raise pump\_shortfall |
| window\_start\_local, window\_end\_local, scan\_step\_min | "11:30", "12:40", 10 (server constants) |
| tz\_posix | The POSIX rule for the owner's time zone: the last line of that zone's TZif file (for America/Los\_Angeles: PST8PDT,M3.2.0,M11.1.0). A stake with no owner gets the America/Los\_Angeles rule |
| dry\_raw, wet\_raw | The plant's current calibration; null if the stake has no plant, the plant isn't calibrated, or the stake is retired. Null means the stake will not water |
| water\_request\_id | The plant's oldest request with outcome "pending", else null. Always null while the stake is retired |
| reservoir\_pct | round(100 × (1 − ml\_since\_refill ÷ jar\_capacity\_ml)), clamped 0–100; null with no plant |
| status | "fault" if failed\_delivery or pump\_shortfall is open, or the latest battery\_mv is under 3,300. "attention" if any other alert is open, the stake has no plant, the plant isn't calibrated, or the stake is retired. Otherwise "ok" |

### 10.3 Water-now queue

- POST water-now creates a request with outcome "pending". If the plant already has a pending request, return 409 already\_pending. If the plant's stake is retired, return 409 device\_retired and create nothing. Refill (POST /api/plants/:id/refill) returns 409 device\_retired in the same case.
- The request rides in every config reply as water\_request\_id until the stake's manual event for it arrives (10.1). The stake acts on each id once (7.3).
- A request still pending after REQUEST\_EXPIRY\_H (placeholder 72 h, Open) is marked "expired" by the hourly job.

| State | Dashboard wording |
| --- | --- |
| pending, not sent | Waiting for the stake's next sync, usually 11:30–12:40 on a school day |
| pending, sent | Sent to the stake at \<time>. Waiting for its report |
| delivered | Watered at \<time> |
| refused | The stake's safety limits blocked this watering |
| expired | Expired before the stake synced |
| stake retired | This stake is retired, so it will not water. Un-retire it on the Devices page |

### 10.4 Alerts (DEC-14)

The alerts job runs every 15 minutes. At most one alert of each type is open per plant. Dismissing hides an alert until it clears and is raised again.

| Alert | Raised when | Cleared when |
| --- | --- | --- |
| low\_water | reservoir\_low is true in the 2 latest readings, or ml\_since\_refill is at least 80% of jar\_capacity\_ml | Refill is pressed and the latest reading shows reservoir\_low false |
| low\_battery | battery\_mv is under 3,500 in the 2 latest readings | The latest reading is 3,600 or more |
| low\_light | On each of the last 3 complete days in the owner's time zone, the number of hourly readings with lux of 2,000 or more is below species.light\_hours. Days with any null lux are skipped, not counted | Any complete day meets light\_hours |
| device\_offline | More than 30 weekday hours since devices.last\_seen, counting only Monday–Friday hours in the owner's time zone. Not evaluated while the stake is retired | The next upload, or the stake being retired |
| failed\_delivery | The 2 latest events with delivery ok or failed are both failed | The next event with delivery ok |
| pump\_shortfall | The computed pump\_duration\_ms is over 15,000 (10.2) | target\_ml or ml\_per\_s changes so it fits |

Why weekday hours: under the sync window a healthy stake is silent about 23 hours every school day and about 71 hours over a weekend. Friday 12:40 to Monday 11:30 counts as about 23 weekday hours, so no alert; a missed Monday reaches about 48 by Tuesday afternoon. Holidays raise one alert that someone dismisses.

The offline alert also shows as a banner on the plant page, because a quiet failure that runs for two weeks is the expensive kind.

### 10.5 Scheduled jobs (APScheduler, inside the API process)

| Job | Schedule (UTC) | What it does |
| --- | --- | --- |
| Model refit | Sundays 03:00 | Rebuild cycles, fit, evaluate, store model\_fits, update effective\_interval\_h (11.4) |
| Alert evaluation | Every 15 minutes | Raise and clear alerts (10.4) |
| Request expiry | Hourly | Mark pending water requests older than REQUEST\_EXPIRY\_H as expired |
| Database backup | Daily 10:00 (2 am Pacific standard time) | Dump, copy off the server, keep 14 days (15.2) |
| Session cleanup | Daily 11:00 | Delete expired sessions |

### 10.6 Errors to the dashboard

Every error uses one shape, with status 400, 401, 403, 404, 409, 413, 415, 422, 429 or 503:

```
{ "error": { "code": "not_found", "message": "Plant not found" } }
```

### 10.7 The simulator

tools/simulate writes eight weeks of hourly readings into the development database through the shared ingest\_batch function that POST /api/readings also calls (10.1), using random seed 42, and writes sim\_truth.json with the true values. Every simulated plant has is\_simulated = 1.

| Setting | Value |
| --- | --- |
| Plants | SIM-001 and SIM-002 dry in straight lines; SIM-003 dries in a curve, so the code handles both shapes before we know which is real |
| True drying rate | SIM-001: 0.5 + 0.00008 × mean daily lux. SIM-002: 0.3 + 0.00005 × mean daily lux. SIM-003: SIM-001's rate × (moisture − 10) ÷ 50, so it dries faster when wet |
| Light | 06:00 to 18:00 local: peak × sin(π × (hour − 6) ÷ 12); daily peak 10,000 lux × a random factor from 0.4 to 1.0 |
| Moisture | Starts at 80; falls by the hour's rate; at 30 or below an automatic watering of 8,400 ms adds 50 points, capped at 90 |
| Noise | Normal, standard deviation 1.5 points, on every reading |
| Raw values | Computed from the percent with dry\_raw 2650 and wet\_raw 1180 |
| Upload pattern | Readings arrive in one batch a weekday between 11:30 and 12:40, none at weekends, so weekend readings arrive "estimated" and are re-dated |
| Mess | 2% of readings dropped, one 14-hour outage, one manual watering, a run of 6 sensor-fault readings, one day of zero lux, one recalibration halfway through |
| Pass condition | Early check (B2): a fit to one simulated cycle recovers its true rate within 10%. Full check (G24, after B12): the fit recovers each straight-line plant's true intercept and light coefficient within 10%; SIM-003 shows visible curvature in a drying plot |

### 10.8 Provisioning a stake

- server/scripts/create\_device creates the devices row and prints the serial, a new random device key and a claim code, once. Only hashes are stored.
- tools/provision writes the serial, key, network list (Kayden's hotspot, Kayden's home WiFi, a spare) and server URL into the stake's flash over USB, sets batt\_cal to 1.0, then flashes the firmware.
- Print the claim code on a sticker and stick it on the stake.

### 10.9 Repository and stack (DEC-02, DEC-03, DEC-04)

- **One repository** with folders firmware, server, web, tools and docs.
- **Server:** Python 3.12+, FastAPI, uvicorn, SQLAlchemy 2 with ordinary (not async) sessions, Alembic for migrations, PyMySQL plus cryptography (MySQL 8.4's default login method needs it), Pydantic v2, argon2-cffi, numpy, APScheduler 3.x, Pillow for thumbnails, and the Anthropic SDK only if diagnosis is kept. Tests with pytest; lint with ruff. Lock versions with uv.
- **Web:** React 18, Vite, TypeScript, React Router, TanStack Query, Recharts. Styles in .css files, no inline styles, no emojis. Tests with vitest. The TypeScript types for every API response in 13.2 live in one file, web/src/api/types.ts.
- **Firmware:** section 7.9.
- **Continuous integration** (GitHub Actions): server tests and lint, web type check and tests, firmware unit tests on a laptop target.

### 10.10 Calibration rules (DEC-15)

- **Input check:** accept dry\_raw and wet\_raw only if 0 ≤ wet\_raw < dry\_raw ≤ 4095 and dry\_raw − wet\_raw ≥ 800. Otherwise 422 with code calibration\_invalid.
- **History:** every accepted change also inserts a calibrations row with its reason: setup, recalibration (PATCH plant), repot (reset-learning), sensor\_replaced or reassigned. A clearing (sensor\_replaced, or reassigned with no new numbers) inserts a row with both numbers NULL, meaning "cleared". Any code that reads the latest calibrations row as the current calibration must treat NULL as uncalibrated (R-19).
- **Retiring:** retiring a stake does not touch the plant's calibration. The pause happens only in the config reply (10.2, 8.5.1).
- **Clearing:** PATCH /api/devices/:id with "sensor\_replaced": true sets the stake's plant's dry\_raw and wet\_raw to NULL. Assigning a different stake to a plant also clears that plant's calibration, unless the same request supplies new numbers.
- **Effect:** with no calibration the config sends nulls, the stake refuses to water, and status is "attention" until someone enters new numbers.
- **Setup help:** GET /api/devices returns each stake's latest moisture\_raw and when it was read, so the setup screen can show it next to the calibration fields.
- **Learning:** a cycle that contains a calibration change is excluded (calibration\_changed, 11.2).

## 11. Learning model (DEC-24, 25, 26)

The model learns how fast this pot really dries and turns that into one number the stake obeys: the minimum hours between waterings. It starts with a simple average of this pot's own cycles, blended with the species default, and only switches to a light-based model once that predicts better. Light is the only input (DEC-08).

### 11.1 Three numbers, three jobs

| Number | Comes from | Used for |
| --- | --- | --- |
| moisture\_threshold | The species table; the model never touches it | What the stake compares each reading against |
| min\_interval\_hours | 0.75 × the effective interval | The safety floor the stake obeys |
| Effective interval, in days | The model's prediction, blended with the species default | What the AI card shows the owner |

The threshold is a property of the plant, not the pot. Basil wants moist soil whether it sits in a fast-drying pot or a slow one; a fast pot just gets there sooner. It is like a car's fuel light, which comes on at the same level however you drive. So the model only answers "how long until we reach it".

The interval is a safety floor, not a schedule. Its job is to stop repeated watering if the sensor misbehaves. Set exactly at the prediction it would never act; set above, it would delay a watering the plant needs. Below the prediction is correct.

**Worked example:** post-watering level 82%, basil threshold 30%, so 52 points to fall. At 1.2 points an hour that is about 43 hours, roughly 1.8 days. With a factor of 0.75 the floor is 32 hours. Normally moisture crosses 30% at hour 43, long after the floor, and the pump runs. A sensor glitch at hour 5 is blocked by the floor.

### 11.2 Cycles: what the model learns from

A cycle runs from one watering event to the next. The weekly job rebuilds cycles and stores every one, with a reason for every exclusion, so the evaluation can be checked. Only cycles in the plant's current learning epoch are used.

1. Take the plant's events in device\_time order, skipping events whose time is unknown. Each pair of consecutive events bounds one cycle. The final open interval is not a cycle.
2. A cycle's readings run from 2 hours after its first event up to its second event; the first 2 hours are water still soaking in.
3. A cycle is **valid** only if all of these hold. Otherwise store it with valid = 0 and the first failing reason:
   - at least 12 readings (too\_few\_readings);
   - no gap over 2 hours between consecutive readings (reading\_gap);
   - no data\_gaps row overlapping it (data\_gap\_reported): a reported gap reads as time not drying;
   - no reading with sensor\_fault (sensor\_fault);
   - no reading or bounding event whose time is still unknown after re-dating (unknown\_time);
   - neither bounding event is manual or test (manual\_or\_test\_watering), or failed or refused (failed\_or\_refused\_event);
   - no calibration change inside it (calibration\_changed);
   - no reading with a null moisture\_pct for a reason other than sensor\_fault, which includes readings taken while the stake was retired and paused (other);
   - its fitted rate is above 0 (non\_positive\_rate).
4. For a valid cycle: rate = minus the least-squares slope of moisture\_pct against hours. hours = time between the two events. hours\_to\_threshold = time from the first event to the first reading at or below the threshold. mean\_daily\_lux = the mean lux over its readings. start\_pct = the first reading after the 2-hour skip.

### 11.3 From cycles to the interval sent to the stake

Let n = valid cycles in the current epoch and species\_h = days\_between\_waterings × 24.

| Stage | Learned value | Effective interval |
| --- | --- | --- |
| n < 3 | None; the AI card shows learning progress | species\_h |
| n ≥ 3 | mean\_h = the mean of the valid cycles' hours\_to\_threshold | Blended, below |
| The light model beats the average | The regression's prediction, below | Blended, below |

```
mean_h        = mean(hours_to_threshold of the valid cycles in this epoch)
regression    : rate = intercept + light_coef * mean_daily_lux        # light only (DEC-08)
post_level    = median start_pct of the last 5 valid cycles
regression_h  = (post_level - moisture_threshold) / rate(mean lux of the last 7 days)
learned_h     = regression_h if the regression is "in use" (11.4), else mean_h

weight        = min(1, (n - 3 + 1) / 6)                     # 1/6 at n = 3, full trust at n = 8
raw           = species_h + weight * (learned_h - species_h)
effective_h   = clamp(raw, 0.75 * previous, 1.25 * previous)  # skipped for the first learned
                                                              # value and after a reset
min_interval  = clamp(0.75 * effective_h, 12, 720)          # DEC-25; this clamp has the final say
```

- Store effective\_h in plants.effective\_interval\_h after each refit; it is the "previous" for the next 25% limit.
- Reject, and don't store, a regression that predicts a zero or negative rate for any cycle.
- The stake's firmware limits always apply, whatever the model says.

### 11.4 Weekly fit procedure

1. Rebuild cycles for each plant's current epoch (11.2).
2. If n ≥ 3, compute mean\_h and store a model\_fits row with model\_type "mean\_interval".
3. If n ≥ REGRESSION\_MIN\_CYCLES (placeholder 10, Open), fit rate on mean\_daily\_lux by ordinary least squares and store it with r2, cycle\_count and model\_version "v1", model\_type "regression".
4. If n ≥ 6, run the walk-forward test (11.5) and store mae\_learned\_h, mae\_species\_h and mae\_mean\_h on the newest fit.
5. **Switch rule:** the regression is put "in use" once its walk-forward error is lower than the simple average's over at least 4 predictions (placeholder 4, Open). Until then the average stays in use. Mark the fit that set the interval with in\_use = 1.
6. Recompute effective\_h (11.3) and save it.

### 11.5 Proving it helps (DEC-26, G30, G31)

Walk-forward means predicting each cycle using only the cycles before it, then checking against what actually happened, like testing yourself only on questions you haven't seen.

1. Keep only valid cycles, in time order.
2. For each cycle from the sixth onward, use only earlier cycles to predict hours\_to\_threshold two ways: the learned pipeline (11.3) and the species default (species\_h).
3. Record the absolute error in hours for both on every cycle.
4. Report the mean absolute error for both, with the cycle count, even when the learned model loses.
5. **Pass (G31):** the learned error is lower than the species default's.

The same walk-forward also produces mae\_mean\_h, which only drives the switch rule in 11.4; it is not part of the G31 claim.

**Honesty rules:**

- The method and metric above are fixed before results come in (this closes Q9).
- R² describes fit, not future accuracy. Never present it as proof.
- If the model never beats the default, record the negative result honestly and keep the safe default. A documented negative result is a real finding.
- The simulator's known rates are the only answer key; G24 checks the fit recovers them.

### 11.6 Curve shape check

The regression treats drying as a straight line. Soil probably dries faster when wet and slower when dry. Once three real cycles exist, plot moisture against time. If it curves, fit the slope of ln(moisture\_pct) against hours instead of moisture\_pct (half a day's work). SIM-003 makes the code handle both before we know.

### 11.7 Resetting learning

- reset-learning requires new dry\_raw and wet\_raw, because repotting changes the soil, and a reason (repot, moved, soil\_change or other; which events count is Q15).
- It raises learning\_epoch, stores epoch\_started\_at and epoch\_reason, and keeps all history visible. Older fits stay in the history chart.
- The plant returns to the species default until it has 3 new valid cycles.
- A recalibration without a reset (PATCH plant) keeps the epoch; only the cycle that spans the change is excluded.

## 12. Photo diagnosis

The owner uploads a leaf photo; a vision model picks one of ten fixed conditions and says what it saw and how the owner can check it themselves. **This feature is optional (DEC-28):** the learning model meets the AI requirement on its own. It is built only after the simple model drives the stake (B11, Fri 8 Jan), can be built in any week with spare time between 4 Jan and 19 Mar (B14, C11, G29), and is the first thing cut if the schedule slips. It depends on nothing else in the project: an upload form, one API call and a table. Output shape per DEC-27.

### 12.1 Principles *(v2; decided there, Eli silent)*

- **A fixed list, never free text.** The model may return exactly one of ten conditions, so the server can check the answer.
- **No confidence score.** A vision model's self-reported confidence is generated like the rest of the answer, not measured. Show it a doorknob and it can say "spider mites, 0.85". Removed from the contract, the schema and the card.
- **Instead, a check the owner can do.** Every diagnosis comes with a physical check and a search term for reference photos. A number asks the user to trust the model; a check tells them how to find out, in ten seconds.
- This matches the rest of the project: moisture is an index, not water content; a watering means the pump ran, not that water arrived. The AI feature does not get to claim more precision than the hardware does.

### 12.2 The ten conditions

| API value | Card headline |
| --- | --- |
| healthy | Looks healthy |
| underwatered | Possibly underwatered |
| overwatered\_or\_root\_rot | Possibly overwatered or root rot |
| nutrient\_deficiency | Possibly a nutrient deficiency |
| too\_much\_light | Possibly too much light |
| too\_little\_light | Possibly too little light |
| pests | Possibly pests |
| fungal\_or\_leaf\_spot | Possibly fungal or leaf spot |
| not\_a\_plant | That does not look like a plant — try another photo |
| unclear | Cannot tell from this photo |

The last two are escape hatches. "not\_a\_plant" handles the doorknob. "unclear" is the model's honest way out and does the job a confidence score pretended to do.

### 12.3 The prompt *(v2, with the species line added)*

The server sends this text with the image. {species\_common} and {species\_scientific} come from the plant's species row.

```
This image should show a leaf of a houseplant. The owner says the plant is
{species_common} ({species_scientific}); use that as context only, and judge the image itself.

Choose exactly one condition from this list and nothing outside it:

  healthy, underwatered, overwatered or root rot,
  nutrient deficiency, too much light, too little light,
  pests, fungal or leaf spot, not a plant, unclear

Then give:
  observation     - what you see in the image that led you
                    to that condition, in one or two sentences
  check_yourself  - a physical check the owner can do on the
                    plant right now to confirm it or rule it out
  search_term     - what to search to see reference photos
  advice          - what to do about it

If the image is not a plant, choose "not a plant".
If you cannot tell, choose "unclear" - do not guess.
Reply with JSON only. No prose before or after it. Use these keys:
condition, observation, check_yourself, search_term, advice.
```

The server maps the condition words to the API values in 12.2 (spaces to underscores, "or" kept).

### 12.4 Field rules *(v2)*

| Field | Holds | Rules |
| --- | --- | --- |
| condition | One of the ten | Anything else is rejected and stored as unclear |
| observation | What in the photo led there | One or two sentences, about the image, not the plant's history |
| check\_yourself | A check the owner can do now | Must name something physically checkable (a leaf underside, old vs new growth, the soil surface). Not "monitor closely" |
| search\_term | What to type for reference photos | Rendered as a button, never raw text |
| advice | What to do | Empty when the condition is healthy, not\_a\_plant or unclear; required for the other seven |

### 12.5 Server flow and failures *(v2, with Eli's limits)*

1. Reject before any API call: not JPEG or PNG → 415; 5 MB or larger → 413. This is the cheapest failure to catch.
2. Save the original to PHOTO\_DIR/{plant\_id}/{uuid}.jpg|png and a 320-px-wide JPEG thumbnail beside it *(thumbnail size Proposed)*.
3. Call diagnose(image\_bytes, species) — the single function that wraps the provider, so the provider can change without touching anything else *(Eli)*. Provider (decided 4 Nov, closes Q11): a Gemini Flash model on Google AI Studio's free tier, key in VISION\_API\_KEY. Google may use free-tier inputs to improve its products, which is acceptable for leaf photos. If the free tier changes or results disappoint at G29, switch to Claude Haiku 5.5 (paid, well under a cent per photo) by editing only diagnose().
4. Store the raw response text on every call, failures included.

| What goes wrong | What the server does |
| --- | --- |
| Provider down or timed out | Reply "could not check right now — try again". Store no diagnosis row |
| Reply is not valid JSON | Retry once. If it fails again, store as unclear with flagged\_for\_review = 1 |
| Condition not in the list | Store as unclear; the model invented a category |
| A required field other than advice missing or empty | Store as unclear; never show a half-filled card |
| Photo is not a plant | Condition not\_a\_plant. The normal path, not an error |

### 12.6 API response and card

POST /api/plants/:id/diagnose (multipart field image) returns 200 with the stored row; GET /api/plants/:id/diagnoses returns a list of the same objects, newest first.

```
{
  "id": 12,
  "created_at": "2026-11-04T19:02:11Z",
  "condition": "pests",
  "headline": "Possibly pests",
  "observation": "Fine pale stippling across the upper leaf surface, and one leaf edge curling upward.",
  "check_yourself": "Turn two or three leaves over and look along the veins. Spider mites leave fine webbing and specks that move. If you see neither, this is not mites.",
  "search_term": "spider mite damage houseplant leaf underside",
  "advice": "Wipe both leaf surfaces with soapy water, then photograph it again in four days.",
  "thumbnail_url": "/api/photos/12/thumb"
}
```

The card always shows three blocks in this order: **What we saw**, **Check it** (with a "See reference photos" button that opens an image search for search\_term), then **What to do**. The check sits above the advice on purpose: verify before acting. No percentage, and no progress bar standing in for one. For unclear, add one line on what makes a better photo: one leaf, filling the frame, in daylight.

Photo files live on the server's disk with paths in the database, and the photo folder is part of the nightly backup. *(Agreed)*

## 13. Dashboard (DEC-03)

The dashboard is the only part most people will ever see, and the 14-day sawtooth chart is the single most persuasive thing in the project. It is built against mock JSON in the contract's shape from week one, then against simulator data, and must work on a phone.

### 13.1 Screens

| Screen | Contents |
| --- | --- |
| Sign up / Log in | Email, password, time zone |
| Home | The account's plants with status; species search |
| Plant detail | Chart, stat cards, AI card, water now with its request state, refill, alerts, offline banner, reset learning, recalibrate, leaf diagnosis (if kept) |
| Add device | Type the claim code from the sticker |
| Plant setup | Species picker, name, stake, target ml (default 60), jar size, and calibration numbers entered next to the stake's latest raw reading |
| Devices | The account's stakes: which plant each waters, last seen, rename, reassign, retire or un-retire (a pause, with Undo), "sensor replaced" |
| Diagnosis history | Past photos and results, newest first (if diagnosis is kept) |
| History | Long-range charts and model accuracy over time |
| Account | Email and password |
| Help | Alert meanings, the refill routine, how the sync window works, common questions |

No payment page appears in the demo build (Q12). Monetization is a slide, not a screen.

### 13.2 Response shapes

Conventions: JSON only; times are UTC ISO-8601 ending in Z; units are percent, millivolts, lux, millilitres and hours. Every type below lives in web/src/api/types.ts.

POST /api/register and POST /api/login take email and password, plus timezone for register. They and GET /api/me return:

```
{ "id": 1, "email": "a@example.com", "timezone": "America/Los_Angeles" }
```

GET /api/plants returns one item per plant. status is ok, attention (any open alert, or the stake is retired), offline (device\_offline open) or no\_data:

```
[{
  "id": 7, "name": "Basil",
  "species": { "id": 3, "common_name": "Basil" },
  "status": "ok", "moisture_pct": 42.5,
  "last_reading_at": "2026-12-08T14:00:00Z",
  "last_sync_at": "2026-12-08T19:31:04Z",
  "device": { "id": 2, "name": "Kitchen stake", "serial": "SPROUT-001" },
  "open_alerts": 0,
  "is_simulated": false
}]
```

GET /api/plants/:id returns the plant in full. reservoir.state comes from the float switch (ok, refill or unknown); estimated\_pct and estimated\_days\_left come from the volume estimate:

```
{
  "id": 7, "name": "Basil",
  "species": { "id": 3, "common_name": "Basil", "scientific_name": "Ocimum basilicum",
               "days_between_waterings": 4.0, "light_hours": 6.0,
               "water_threshold_pct": 30.0, "source_url": "https://example.edu/basil",
               "toxic_to_cats": false, "toxic_to_dogs": false, "image_url": null },
  "moisture_threshold": 30.0, "target_ml": 60.0, "jar_capacity_ml": 1000,
  "dry_raw": 2650, "wet_raw": 1180, "calibrated": true,
  "learning_epoch": 1, "epoch_started_at": "2026-12-18T00:00:00Z",
  "device": { "id": 2, "name": "Kitchen stake", "serial": "SPROUT-001",
              "last_seen": "2026-12-08T19:31:04Z" },
  "latest": { "t": "2026-12-08T14:00:00Z", "moisture_pct": 42.5, "lux": 8200,
              "battery_mv": 3810, "time_status": "synced" },
  "reservoir": { "state": "ok", "estimated_pct": 63, "estimated_days_left": 9 },
  "waterings_last_7_days": 3, "light_hours_today": 6,
  "water_request": null,
  "is_simulated": false
}
```

estimated\_days\_left = remaining ml ÷ average ml used per day over the last 14 days; null with fewer than 2 waterings. water\_request is null or { "id": 12, "state": "sent", "requested\_at": "...", "sent\_at": "...", "resolved\_at": null }, where state is pending, sent, delivered, refused or expired (10.3). GET /api/plants/:id/water-requests returns the same object for the latest request.

GET /api/plants/:id/readings?days=14 and /events?days=14 accept 1 to 90 days and leave out items whose time is unknown. The readings response also carries the gaps the chart must draw:

```
{ "plant_id": 7,
  "readings": [{ "t": "...", "moisture_pct": 42.5, "lux": 8200, "battery_mv": 3810,
                 "time_status": "synced" }],
  "gaps": [{ "start": "...", "end": "...", "reason": "dropped" }] }

{ "plant_id": 7,
  "events": [{ "t": "...", "trigger": "auto", "duration_ms": 8400, "volume_ml": 60.0,
               "delivery": "ok", "moisture_before": 28.1 }] }
```

GET /api/plants/:id/model feeds the AI card. learned\_interval\_h and fit are null until learning starts:

```
{
  "epoch": 1, "cycle_count": 6, "cycles_needed": 3,
  "species_interval_h": 96.0, "learned_interval_h": 67.2, "effective_interval_h": 76.8,
  "model_type": "mean_interval",
  "fit": { "intercept": null, "light_coef": null, "r2": null, "fitted_at": "2027-01-10T03:00:00Z" },
  "history": [{ "fitted_at": "2027-01-10T03:00:00Z", "model_type": "mean_interval", "cycle_count": 6,
                "in_use": true, "r2": null, "mae_learned_h": 5.2, "mae_species_h": 14.8 }]
}
```

| Request | Body | Success response |
| --- | --- | --- |
| POST /api/plants | name, species\_id, device\_id (optional), dry\_raw, wet\_raw, target\_ml, jar\_capacity\_ml | 201 with the plant object; 422 calibration\_invalid (10.10) |
| PATCH /api/plants/:id | any of name, target\_ml, jar\_capacity\_ml, dry\_raw + wet\_raw (together) | 200 with the plant object |
| POST /api/plants/:id/water-now | none | 202 with the water\_request object; 409 already\_pending or device\_retired |
| POST /api/plants/:id/refill | none | 200 with { "ml\_since\_refill": 0 }; 409 device\_retired |
| POST /api/plants/:id/reset-learning | dry\_raw, wet\_raw, reason (repot, moved, soil\_change, other) | 200 with { "learning\_epoch": 2, "epoch\_started\_at": "..." } |
| POST /api/plants/:id/diagnose | multipart field image | 200 with the diagnosis (12.6); 413, 415, 503 |
| GET /api/plants/:id/diagnoses | none | List of diagnoses, newest first |
| GET /api/plants/:id/alerts | none | \[{ "id": 4, "type": "low\_water", "raised\_at": "...", "message": "Refill the jar" }\] |
| POST /api/alerts/:id/dismiss | none | 200 with { "dismissed": true } |
| GET /api/species?q=basil | none | Up to 10 items of id, common\_name, scientific\_name |
| POST /api/devices/claim | code | 200 with the device; 404 unknown or already-claimed code |
| GET /api/devices | none | Items of id, name, serial, plant\_id, firmware\_version, last\_seen, retired, latest\_moisture\_raw, latest\_raw\_at |
| PATCH /api/devices/:id | any of name, plant\_id, retired, sensor\_replaced | 200 with the device; 409 device\_retired when a retired stake is assigned to a different plant |
| GET /api/photos/:id/thumb and /full | none | The image file, owner only |

### 13.3 Screen rules

- **Chart:** moisture\_pct as a line on a fixed 0–100 axis over 14 days in the owner's time zone, a tick every 2 days. A dashed horizontal line marks the threshold. A vertical marker at each watering, drawn differently for ok and for failed or refused. The line breaks wherever readings are more than 3 hours apart or a gap is reported, and a reported gap is labelled. Estimated times are drawn like the rest; the tooltip says "time estimated". Unknown times are never drawn. A hidden table of the last 24 readings serves screen readers. Colours come from Design's visual system (D3).
- **Stat cards:** light today (hours with lux of 2,000 or more), reservoir (OK or Refill, with estimated percent and days left as smaller text), battery (volts to two decimals, or Unknown), waterings in the last 7 days.
- **AI card:** under 3 valid cycles it shows "Typical for this plant: every X days" (species\_interval\_h ÷ 24, one decimal) and "Learning: N of 3 valid cycles (needs 4 waterings)". From 3 cycles it shows "Typical for this plant: every X days" and "Your pot reaches its watering point in about Y days" (effective\_interval\_h ÷ 24) side by side, the line "Based on your pot's own drying", and how many waterings it is based on. The card never says the schedule was adjusted: the stake waters when moisture crosses the threshold, and the learned interval only sets the minimum gap between waterings (11.1). Until B11 the card uses hardcoded values and looks the same.
- **Water now:** disabled while a request is pending or sent, and while the stake is retired. Shows the wording for the request's state from 10.3.
- **Retired stake:** the plant page says "This stake is retired, so it will not water" with a link to the Devices page. Water now and Refill are disabled. The Devices page shows Retire as a pause with an Undo.
- **Reset learning and recalibrate:** both ask for new calibration numbers next to the stake's latest raw reading. Reset explains that history is kept but the schedule starts learning again; recalibrate explains that watering pauses until valid numbers are saved.
- **States:** every panel has a loading state, an error state with a retry button, and an empty state. No readings yet: "No readings yet. The stake reports at its next sync, usually 11:30–12:40 on a school day." No stake: "Assign a device." Not calibrated: "Enter calibration numbers so the stake can water."
- **Offline:** when device\_offline is open, a banner at the top of the plant page says when the stake was last seen.
- **Layout:** one column under 640 px wide, chart 240 px tall on a phone, touch targets at least 44 px.

### 13.4 Honest labelling

| Thing | Always said as | Never said as |
| --- | --- | --- |
| Moisture | Soil moisture index | Water content, exact percent |
| Reservoir | OK or Refill from the float switch; estimate as smaller text | A precise percentage |
| A watering | The pump ran; "moisture did not rise" when the check fails | Water delivered; clog detected |
| Timestamps | Estimated times marked as estimated | Silently shown as exact |
| Diagnosis | "Possibly …" with a check attached | A percentage or confidence bar |
| Water now | Queued until the stake's next sync | Instant |
| Light | Lux, relative | Plant light (PPFD or DLI) |

## 14. Test gates (DEC-32)

Nothing proceeds past a failed gate. Device runs the gates; Design witnesses them and records date, runner, device version, actual values and photos in the shared log. **No living plant enters the project until G20 (72 hours in soil) passes clean.** A failure there costs three days; the same failure in February costs two months and a dead plant.

One list, G1 to G32, numbered so references stay stable; the Due column gives the order the gates run. The last two columns give each gate's old number in v2 and in Eli's spec. G6 is retired with the soil temperature probe (DEC-08); its number is kept so references stay stable. G17 is split into G17a (device keys, 30 Nov) and G17b (accounts, after B15).

| G | What it proves | Passes when | Due (week of) | v2 # | Eli # |
| --- | --- | --- | --- | --- | --- |
| G1 | The board is alive | LED blinks; board shows up as a serial port | Done | 1 | 1 |
| G2 | It reaches the internet | IP within 10 s and a real HTTPS POST to a test endpoint succeeds on Kayden's hotspot in the classroom and on his home WiFi. Connect, DNS, TLS and POST times recorded for the power budget; repeated against the live server at A9a | 9 Nov | 2 | 2 |
| G3 | Moisture sensor works | Dry and wet readings differ by 800+ counts and are stable; dry\_raw and wet\_raw recorded | 9 Nov | 3 | 3 |
| G4 | Moisture calibration repeats | Five readings in the same condition within 2 points; formula and raw data recorded; air and water reference values logged | 9 Nov | — | T-26 |
| G5 | Light sensor works | Dark, indoor and window readings clearly different | 9 Nov | 4 | 4 |
| G6 | (Retired: soil temperature, DEC-08) | — | — | 5 | — |
| G7 | Battery sensing works | Reading within the recorded tolerance of a multimeter at three voltages; batt\_cal recorded; the 3.3 V watering stop demonstrated (the dashboard alert is checked again at B10) | 16 Nov | 6 | T-16 |
| G8 | Sleep current, breadboard | Deep-sleep current under about 0.3 mA with the sensors and pump circuit connected, pump and sensor pins held low, float pull-up off | 16 Nov | — | T-27 |
| G9 | The switch works | An LED in the pump's place turns fully on and fully off from D10 | 16 Nov | 7 | 5 |
| G10 | The pump runs | Spins and stops cleanly; never run dry for more than 2 s | 16 Nov | 8 | 6 |
| G11 | The pump is calibrated | Three 10 s runs deliver the same volume within 10%; ml\_per\_s recorded; tube level holds 10 min after stopping with no dripping | 16 Nov | 9 | 7 |
| G12 | Reservoir sensing works | Correct state at low and full, and with the float wire unplugged (must read low); reservoir\_low reaches the API; pump blocked when low | 16 Nov | 10 | T-15 |
| G24 | Simulator recovery | The fit recovers each straight-line simulated plant's true intercept and light coefficient within 10%; SIM-003 shows curvature | 25 Jan | — | T-28 |
| G13 | The control logic works | Probe out of water: pump runs once, then won't run again early. Whole loop into an empty cup with a sped-up clock, including at least one real deep-sleep wake and one button wake | 30 Nov | 11 | 8 |
| G14 | Every failsafe fires | Sensor unplugged: no watering. Float low: no pumping. Tube pulled from the jar: stops after two failed checks. Runtime and daily caps hold. Low battery stops watering. No calibration: no watering. Stuck button: no wake loop | 30 Nov | 12 | 9 |
| G15 | The offline buffer works | Readings survive sleep, reboot and network loss; pull power mid-cycle; everything uploads later with no duplicates; overflow tested with a shrunken buffer (dropped\_count and the gap appear) | 30 Nov | 13 | T-18 |
| G16 | Timestamps behave | Online and offline readings chart by measurement time; estimated times are re-dated; received\_at kept; uptime tracks wall time across several sleeps; 24 h drift recorded | 30 Nov | — | T-17 |
| G17a | Unauthorised requests fail | No or wrong device key: 401 | 30 Nov | 16 | T-19 |
| G17b | Accounts are separated | Another account cannot read a plant or trigger watering; run once B15 lands | 8 Mar | — | — |
| G18 | The box is waterproof | Tissue inside stays dry after a thorough spray with every opening fitted; repeated after every lid opening | 30 Nov | 14 | 10 |
| G19 | Charging and reseal | Battery charges through the USB-C port with the box shut; box passes G18 again after a lid opening | 30 Nov | — | T-21 |
| G23 | Sleep current, built stake | G8 repeated on the soldered build and on the finished, boxed stake | 30 Nov | — | T-27 |
| G20 | 72 hours in soil | Full stake, real timing, damp soil, no plant, calibration entered: no pooling, no leaks, no data gaps, battery as predicted. Record whether a 60 ml dose clears the 3-point delivery check. Any failure restarts the full 72 h | 7 Dec (Mon 7 – Thu 10) | 15 | 11 |
| G32 | Recovery works | A backup is restored onto a fresh machine and the dashboard runs from it. Re-run the week of 19 Apr as the demo-day fallback rehearsal | Fri 11 Dec | (§10.3) | — |
| G21 | Firmware update works | Reflash the sealed stake through its USB-C port; an interrupted update leaves the pump off | 7 Dec | 17 | T-23 |
| G22 | Live plant | Basil in on Fri 18 Dec, checked daily for a week (at Kayden's home over the break) | Fri 18 Dec | 18 | 12 |
| G26 | Pump maintenance | Intake filter cuts flow by no more than 20% against G11; cleaning steps written | 11 Jan | noted | T-25 |
| G27 | Repot reset | On a simulated plant: history stays visible, reset date stored, species default used until 3 new valid cycles | 1 Feb | — | T-22 |
| G25 | Light sensor position | Readings stay useful as the plant grows and shades the lid; sketch and photos recorded | 15 Feb | noted | T-24 |
| G28 | Battery endurance | Measured sleep, wake, sync and pump currents × the real schedule give at least 180 days with a 20% reserve. If six months can't be run inside the project, it is labelled a projection with stated assumptions | Projection by 15 Mar | 19 | 13 |
| G30 | Model evaluation recorded | Both walk-forward errors recorded on every eligible cycle (11.5) | 15 Mar | — | T-20 |
| G31 | The model beats the default | Learned error lower than the species default's on cycles it had not seen | 15 Mar | 20 | 14 |
| G29 | Leaf diagnosis (optional) | A photo returns one of the ten conditions with every field; wrong type: 415; 5 MB or more: 413; a non-plant photo: not\_a\_plant; the provider can be swapped by editing only diagnose() | When B14 and C11 are built, by Fri 19 Mar | — | T-29 |

### 14.1 The four that matter most

- **G9: switch an LED before the pump.** If the switch is miswired you find out with a dim LED, not water across a desk.
- **G13: run the whole loop into an empty cup.** Proves the control logic before soil, plants or time are involved.
- **G20: 72 hours in soil with no plant.** Whatever goes wrong here would have killed a plant. Never shorten it.
- **G28: the battery claim.** v1 claimed six months and tested a 90-day projection. The claim must now match the evidence.

## 15. Deployment, backup and failure modes

Two facts make almost every failure survivable: the stake buffers, so an outage costs freshness rather than data, and watering never depends on the network. Almost every failure below means stale charts and a healthy plant. The one unrecoverable failure is losing the server's database with no copy anywhere else.

### 15.1 What happens when something goes down

| What fails | Cost | Recovery |
| --- | --- | --- |
| The API crashes | Minutes, nothing lost | systemd restarts sprout-api automatically |
| The tunnel drops | Minutes, nothing lost | cloudflared reconnects; restart its service if not |
| Oracle has an outage | Hours, nothing lost | The stake buffers and catches up at a later sync; the dashboard is dark meanwhile |
| MySQL stops | Hours, nothing lost | The server can't store, so it doesn't send 200, so the stake keeps its readings. Restart MySQL |
| Oracle reclaims or deletes the free machine, with backups | Half a day, nothing lost | Create a new machine (15.4), restore the latest dump and photos |
| The machine is lost, no backups | Catastrophic | The project's data is the project |

### 15.2 Mitigations

- **Nightly backup, copied off the** server. At 10:00 UTC the backup job runs mysqldump with --single-transaction, gzips it, and with the photo folder pushes it to a private GitHub repository through a deploy key (placeholder target). Keep the last 14 daily dumps there. A backup with the same provider protects against nothing if that account has a problem.
- **Prove the restore (G32) by Fri 11 Dec,** before the plant goes in, and again the week of 19 Apr.
- **Acknowledge after the write, never before.** The stake clears its buffer only after the database has committed (10.1).
- **Know when it's down.** The offline alert and banner make a quiet two-week failure impossible to miss.
- **Demo-day fallback.** Keep a laptop that can run MySQL 8.4, the API and the dashboard from the latest dump. If the network fails on presentation morning, run locally and still demo. Rehearse the week of 19 Apr.

### 15.3 Realistic threats, ranked

| Cause | Likelihood | Note |
| --- | --- | --- |
| Human error | Highest by far | DELETE without WHERE, a migration on the wrong database, a dev app pointed at live data |
| Oracle reclaims the free machine or changes the free tier | Real | Machine sized to stay above the idle line (5.1); nightly off-server backup; restore proven at G32 |
| Credential exposure | Low | Nothing sensitive is reachable directly; secrets stay out of the repository |

The realistic threats are us and the provider. A nightly dump stored off the server covers both.

### 15.4 Setting up the server (the order an agent or a person follows)

1. Create the Oracle Cloud account in a parent's name and card, with Kayden added as an admin user (Q29); the free tier is not charged. Choose the home region (5.1). Create a VM.Standard.A1.Flex instance with 1 OCPU and 6 GB, Ubuntu 24.04 arm64 and an SSH key. Leave only SSH open in the network security rules, turn off SSH password login, and create a service user named sprout.
2. Install Docker and run MySQL 8.4 LTS from the official mysql:8.4 image (decided 5 Nov, Q28): port 3306 bound to 127.0.0.1 only, a named volume, restart unless-stopped, innodb\_buffer\_pool\_size = 1G. Create the sprout database and a database user with rights to it alone.
3. Install uv and Python 3.12+, the current Node LTS (to build the dashboard), and git.
4. Clone the repository; write /etc/sprout/sprout.env (5.2).
5. Run the Alembic migrations, then load the ten species from Design's CSV.
6. Build the dashboard (web/dist).
7. Install the systemd service sprout-api (uvicorn, one worker, restart always).
8. Install cloudflared, create a named tunnel for the hostname (Q19), and install it as a service.
9. Run the first backup by hand and check it arrives off the server.
10. deploy.sh, for every later change: git pull, migrations, dashboard build, restart sprout-api.

## 16. Parameters and constants

Every number a builder needs, with its status. **Decided** means the team chose it. **Placeholder** means use it as written until someone changes it. **Open** means the value is still awaiting a decision; its question, if it has one, is listed in 17.2. Every Open value in this section shows a placeholder: use it as written and flag it. For an Open question in 17.2 that names no placeholder, stop and ask its owner. **Measured** names the gate that produces it.

### 16.1 Firmware

| Constant | Value | Status |
| --- | --- | --- |
| Read interval | 60 min | Decided |
| Sync window | Every 10 min from 11:30 to 12:40 local; stop after the first success of the day | Decided (DEC-05); stop rule Placeholder |
| Sensor settle time | 100 ms | Decided |
| MOISTURE\_SAMPLES | 5, take the median | Placeholder |
| Battery samples | 16, take the mean | Decided |
| Float switch samples | 5 over about 500 ms, majority; low alert after 2 readings | Decided |
| SANITY\_MARGIN | 10% of the dry-to-wet span on each side | Placeholder |
| RUNTIME\_CAP\_MS | 15,000 | Decided (DEC-11) |
| DAILY\_CAP | 2 per rolling 24 h, manual included | Decided |
| LOW\_BATT\_STOP\_MV / LOW\_BATT\_WARN\_MV | 3,300 / 3,500 | Decided (DEC-14) |
| DELIVERY\_CHECK\_MIN / MIN\_RISE\_PTS / FAILED\_STOP | 45 min / 3 points / 2 in a row | Decided (DEC-13); G20 checks a 60 ml dose clears 3 points |
| CLOCK\_FRESH\_H | 24 | Decided (DEC-17) |
| WATCHDOG\_S | 30 s | Open (Q23) |
| WIFI\_TIMEOUT\_S | 20 s | Placeholder |
| HTTP\_TIMEOUT\_S | 15 s | Placeholder |
| BATCH\_MAX | 48 items per POST; stop after 60 s of radio per sync | Placeholder |
| Upload retry | Next scan slot or button press only | Decided |
| Readings buffer | 60 files of 24 records (about 60 days) | Decided (DEC-16); size Placeholder |
| Events | Never deleted on the stake | Decided (DEC-16) |
| Light sensor mode | One-time high-resolution read per wake | Placeholder |
| LED | Single colour on D6; 1, 2 or 3 blinks for ok, attention, fault; 5 s after a button press, 1 s at hourly wakes when not ok | Open (Q26) |
| FALLBACK\_PUMP\_MS | 8,400 until ml\_per\_s is measured | Placeholder |
| tz\_posix default | PST8PDT,M3.2.0,M11.1.0 | Decided |

### 16.2 Server

| Constant | Value | Status |
| --- | --- | --- |
| target\_ml default | 60 ml, adjusted after the first live week | Decided (DEC-12) |
| Interval factor, clamp, change limit | 0.75; 12–720 h; ±25% per refit | Decided (DEC-25) |
| Learning starts / full trust | 3 valid cycles / 8 valid cycles (blend over 6) | Decided (DEC-24) |
| REGRESSION\_MIN\_CYCLES | 10 | Open |
| Switch to the light model | Lower walk-forward error than the average over at least 4 predictions | Open |
| Cycle rules | Skip 2 h after watering; at least 12 readings; no gap over 2 h | Placeholder |
| Model refit | Sundays 03:00 UTC | Placeholder |
| Walk-forward start | Sixth valid cycle | Decided (DEC-26) |
| REQUEST\_EXPIRY\_H | 72 h | Open |
| Offline alert | More than 30 weekday hours without an upload; not evaluated while the stake is retired | Decided (DEC-14) |
| Low battery alert | Under 3,500 mV twice; clears at 3,600 mV | Decided (DEC-14) |
| Low water alert | Float low twice, or 80% of the jar used | Decided (DEC-14) |
| Low light alert | Hours with lux of 2,000 or more below light\_hours, 3 complete days running | Decided (DEC-14) |
| Calibration check | 0 ≤ wet\_raw < dry\_raw ≤ 4095 and a span of at least 800 | Decided (DEC-15) |
| Timestamp rejection | Future (5 min slack) or older than 90 days | Placeholder |
| Backups | Daily 10:00 UTC; keep 14 days | Placeholder |
| Account limits | Passwords 10+ characters; sessions 14 days; 5 logins per minute per IP | Placeholder |
| Photo upload limit | JPEG or PNG under 5 MB | Decided (DEC-27) |
| Thumbnail | 320 px wide JPEG | Placeholder |
| Chart | 14 days; line broken at gaps over 3 h | Placeholder |

### 16.3 Measured on the bench

| Value | Gate | Stored in |
| --- | --- | --- |
| dry\_raw, wet\_raw | G3, G4; again every 3 months and on reset | plants and calibrations |
| batt\_cal | G7 | The stake's flash |
| ml\_per\_s | G11 | devices |
| jar\_capacity\_ml | Measuring cup | plants |
| Float switch trip height | When mounting | Design's build notes |
| Sleep current | G8, G23 | Test log; feeds G28 |
| Clock drift | G16 | Test log |
| Network connect and POST time | G2 | Test log; feeds the power budget |
| Moisture rise from a 60 ml dose | G20 | Test log; confirms MIN\_RISE\_PTS |

### 16.4 Inputs from outside this document

| Input | From | Due (week of) |
| --- | --- | --- |
| Ten species as a cited CSV (9.3) | Design (D1) | 9 Nov |
| Visual system and screens | Design (D3, D4) | 9 and 16 Nov |
| Hostname | Backend (Q19) | 16 Nov |
| Oracle account (a parent's name and card, Kayden as admin) and server created | Kayden (Q29) | 16 Nov |
| Network names and passwords (hotspot, home WiFi) | Kayden | 9 Nov |
| Enclosure drawing and outside-facing parts | Design (D6, Q27) | 16 Nov |
| Owners for B7 and B14: settled 5 Nov (Megan takes B7, Kayden takes B14) | Team (DEC-33) | 9 Nov |

## 17. Agreements, open questions, risks

### 17.1 Agreed rules (beyond the DEC list in section 1)

| Rule | Settled as |
| --- | --- |
| Project approved | Yes |
| Teacher checkpoint dates | None; our timeline is the only structure |
| Controller | Seeed XIAO ESP32-C3 |
| Pump circuit | IRLZ44N, 220 Ω gate resistor, 10 kΩ gate pulldown, 1N4007 across the pump |
| Reservoir | Float switch as a hard interlock plus a computed estimate for display |
| Breadboard vs solder | Breadboard everything supervised; solder and seal before anything runs unattended |
| Soldering | At home, ventilated, fan pushing smoke away |
| Model and failsafes | The model suggests; the firmware decides. No model output overrides a failsafe |
| Model and threshold | The model sets the interval only; the threshold stays the species value |
| Species data | Hand-researched numeric thresholds with citations; no label-to-number conversion |
| Model must be proven | Against a baseline, on cycles it had not seen, with the method fixed first; negative results reported |
| Diagnosis confidence score | Removed everywhere; replaced by a physical check and a search term |
| Uploads acknowledged | Only after the database write succeeds |
| Unknown serials | Rejected |
| Accounts | Real accounts with hashed passwords; the device key is separate |
| Time zones | Store UTC; convert in the browser; the account time zone only for day-based rules and tz\_posix |
| Chart | 14-day sawtooth with watering markers, the project's centrepiece |
| Water now | Queued until the next sync, never shown as instant |
| Over-the-air updates | Out of scope; the USB-C port covers updates |
| Database backup | Nightly, copied off the server |
| Hostinger database, Replit | Not used |
| Control plant | Hand-watered twin beside the live plant, travelling with it over breaks |
| Plant over breaks | Goes home with Kayden; the stake syncs on his home WiFi (29 Oct, closes Q24) |

### 17.2 Open questions

v2's numbers are kept and never reused. A question that closes keeps its number in the closed list.

**Blocking: answer before the work it names starts**

| # | Question | Owner | Needed by (week of) | Placeholder or next step |
| --- | --- | --- | --- | --- |
| Q19 | What hostname does the server use? | Backend | 16 Nov (B17) | Buy a cheap domain; use sprout.\<domain> (5.3) |
| Q3 | Is the backup running and restorable? | Backend | Fri 11 Dec | A gate, not a question: prove it with G32 |

**Decide before building the affected part**

| # | Question | Owner | Needed by (week of) | Placeholder |
| --- | --- | --- | --- | --- |
| Q4 | Do the divider readings match a multimeter across the battery's range? | Device | 16 Nov (G7) | Two 1 MΩ (DEC-10) |
| Q6 | Does the final pin map behave on the bench: normal boot with every part connected, button wake, analog reads with WiFi on, LittleFS space? | Device | 30 Nov (before A10) | Map in 6.2 |
| Q27 | Exactly which outside-facing parts: waterproof USB-C port, button, LED holder? | Device + Design | 16 Nov (D6) | Panel-mount parts in 6.1 |
| Q26 | When does the LED show? | Device | 30 Nov (A8) | 5 s after a button press; 1 s at hourly wakes when not ok |
| Q23 | What watchdog timeout? | Device | 30 Nov (A8) | 30 s |
| Q18 | Is a hardware pump cutoff needed for a stuck pump driver? | Device | 30 Nov (A10) | None; the jar size limits the damage |
| Q12 | How is the design template reworked? | Design | 9 Nov (D3) | Phone-width navigation, autumn palette, no payment page |

**Lower priority**

| # | Question | Owner | Note |
| --- | --- | --- | --- |
| Q16 | What is the real demo date? (Break dates were checked on 5 Nov.) | Team | Breaks, holidays and finals now come from the district calendar (4.2). Demo date: ask Mr. Benrud before 13 Nov |
| Q15 | Does reset-learning cover moves and soil changes, or only repotting? | Backend | epoch\_reason is ready either way |
| Q13 | Is tethering off a classroom computer worth one test? | Kayden | The plan stays the hotspot |
| Q14 | Does a photo timeline come into scope? | Team | Deferred; never imply it exists because diagnosis does |

**Closed:** Q1 (Backend lead: Eli, 5 Nov), Q2 (Frontend lead: Ca'Marion, 5 Nov), Q5 (not hosted on Replit: DEC-01, DEC-02; Replit is used only as a coding tool, 3.9), Q7 and Q10 (closed in v2), Q11 (diagnosis uses Gemini's free tier, 4 Nov), Q8 (DEC-25), Q9 (DEC-26), Q17 (the learning model meets the AI requirement, Mr. Benrud, 29 Oct), Q20 (the button wakes from D2, DEC-09), Q22 (sensor failures send null plus a fault flag, 8.3), Q24 (Kayden takes the plant home over breaks), Q21 (status LED: a single-colour 5 mm LED from the ELEGOO kit, 9 Nov), Q25 (soldering supervision: Kayden's dad, at home, 9 Nov), Q28 (server: Oracle Cloud Always Free, 1 OCPU and 6 GB, 9 Nov), Q29 (Oracle account holder: a parent's name and card, with Kayden added as an admin user, 9 Nov).

### 17.3 Risks

| Risk | Severity | Response |
| --- | --- | --- |
| The tracks drift apart and nothing fits | High | Frozen contract on 13 Nov; end-to-end path by 4 Dec; milestone meetings on the calendar |
| November overloads Device | High | A2–A12 in three working weeks; the 14–17 Dec spare week protects the plant date; the plant moves to January rather than skipping G20 |
| The stake can't reach a network at school | High | G2 tests the hotspot first; 60-day buffer; the button forces a sync |
| Water reaches the electronics | High | G18 after every lid opening; every opening sealed; everything above the water line |
| The pump siphons after stopping | High | Tube high point above the water line, checked at G11 |
| The moisture sensor fails silently | High | Sanity check, delivery check, three spare sensors |
| The jar runs empty and the pump runs dry | High | Fail-safe float switch blocks the pump |
| The battery can't last six months | High | Sleep current under 0.3 mA checked at G8 and G23; G28 uses measured data |
| Oracle reclaims the free machine or changes the free tier | High | Machine sized to stay above the idle line (5.1); nightly off-server backup; restore proven at G32; demo-day laptop fallback; if the rules change, resize or pay a little to keep it |
| No Arm capacity when creating the machine | Medium | Retry later in the home region (capacity errors are temporary); fallback is a \~$5/month paid server |
| B14 is built only in spare time | Medium | Kayden builds it only when Device is on time; it is optional and first to cut |
| The model never beats the default | Medium | Report it honestly and keep the safe default; a negative result is still a result |
| The plant dies mid-project | Medium | G20 before any plant, a control plant, a spare pot |
| Home internet is out over a break | Low | The stake buffers 60 days and keeps watering |

### 17.4 How close is this to "an AI invents less than 10%"?

Every merge decision is made and written into the sections above. What is still open:

| Kind of open item | Count | What closes it |
| --- | --- | --- |
| Merge decisions | 0 | Nothing left; DEC-33 was settled on 5 Nov |
| Open questions | 13 (Q3, Q4, Q6, Q12–Q16, Q18, Q19, Q23, Q26, Q27) | Named owners and dates above; each has a placeholder or is a gate |
| Values marked Open in section 16 | 5 (regression minimum, switch rule, request expiry, watchdog timeout, LED behaviour) | Accept the placeholder or change it |
| Values only a bench can produce | 9 (16.3) | The gates; an AI never invents these |

With the placeholders accepted, an AI agent would still have to invent only:

- **Visual details** (colours, type, component look) until Design delivers D3 and D4.
- **File and module layout inside each folder.** Low risk; it doesn't change behaviour.
- **Perenual API field mapping** for B7, until someone adds the endpoint and field names when B7 starts.
- **Exact part numbers** for the outside-facing parts (Q27).

A rough estimate, not a measurement: that is well under 10% of the build.
