# Sprout

A sensor stake that waters a potted plant by itself and learns how fast that pot dries out.

- **What gets built:** [`docs/Sprout Master Specification v3.md`](docs/Sprout%20Master%20Specification%20v3.md), the spec. It's the source of truth.
- **How the team works together:** [`docs/orchestration-plan.md`](docs/orchestration-plan.md).
- **What each checkpoint's agent may do:** [`tasks/`](tasks/README.md), one task card per checkpoint.

## What each folder holds

| Folder | What's in it | Owner |
| --- | --- | --- |
| `firmware/` | Code that runs on the stake (Seeed XIAO ESP32-C3). `src/logic/` holds rules that don't touch hardware, so they can be tested on a laptop | Kayden |
| `server/` | The API, database migrations, simulator, learning model and alerts (Python, FastAPI) | Eli |
| `web/` | The dashboard people use in a browser (React, TypeScript) | Ca'Marion, with Megan |
| `tools/` | Helper tools, such as provisioning a stake over USB (B17) | Eli |
| `docs/` | The spec and the team's plans | Everyone, through pull requests |
| `tasks/` | Task cards, one per checkpoint | Kayden |
| `.github/workflows/` | The automatic checks GitHub runs on every pull request | Kayden |

At the root:
- `docker-compose.yml` runs the local MySQL 8.4 database.
- `.env.example` lists the settings each part needs, with fake values.

## How work flows

1. **Code lives in GitHub.** Nobody copies code by hand out of a chat window.
2. **Teammates import this repo into Replit to build.** Each checkpoint gets its own branch, named after it (for example `b3-ingest`), and its own pull request.
3. **GitHub Actions runs every test on every pull request:**
   - server: lint and tests against a real MySQL 8.4
   - web: type check and tests
   - firmware: laptop tests

   A pull request merges only when all three pass.
4. **Backend tests need MySQL, which Replit can't run.** That's fine: GitHub Actions runs them for you on every pull request, and the error text shows up on the pull request.
5. **MySQL 8.4 only.** Never SQLite, Replit's built-in database or any other database.

The full process (task cards, reviews, merging, who owns which files) is in [`docs/orchestration-plan.md`](docs/orchestration-plan.md).

## Running each part on Windows

You don't have to run anything locally: GitHub Actions runs every test on every pull request. Run things locally when you want to try something before pushing.

If you'd rather not type commands, there are two ways around it:
- **Ask Claude** in the Claude desktop app to run the command for you. Every command below is a single line it can run.
- **Use VS Code's buttons.** Each section below says which button replaces the command.

### One-time installs

| Install | Needed for | Notes |
| --- | --- | --- |
| [Git for Windows](https://git-scm.com/download/win) | Everything | |
| [VS Code](https://code.visualstudio.com/) | Everything | Add the **Python**, **Docker** and **PlatformIO IDE** extensions |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Running MySQL locally | Must be open whenever you use the database |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | The server | uv also installs the right Python version for you |
| [Node.js LTS](https://nodejs.org/) | The dashboard | |
| A C++ compiler such as MinGW-w64 (through [MSYS2](https://www.msys2.org/)) | Firmware laptop tests only | PlatformIO's laptop tests need a compiler on your PATH. You can skip this and let GitHub Actions run them |

### 1. Settings file (once)

Copy `.env.example` to a new file named `.env` in the same folder, and change the fake passwords.
- **In VS Code:** right-click the file, then Copy and Paste, and rename the copy.
- **Rules:**
  - The password inside `DATABASE_URL` must match `MYSQL_PASSWORD`.
  - Never commit `.env`. Git already ignores it.

### 2. The database

Start Docker Desktop, then:

```bash
docker compose up -d
```

- **In VS Code:** right-click `docker-compose.yml` and choose **Compose Up**.
- **To stop it:** `docker compose down`, or **Compose Down**. Your data is kept in a Docker volume.

### 3. The server

```bash
cd server
uv sync
uv run --env-file ../.env pytest
```

- **In VS Code:** after `uv sync`, choose the `server/.venv` Python interpreter. The **Testing** panel (flask icon) then runs the tests with a button. VS Code reads `.env` from the repo root.

### 4. The dashboard

```bash
cd web
npm ci
npm run dev
```

- `npm run dev` shows a local address to open in your browser.
- Run `npm test` for the tests and `npm run typecheck` for the type check.
- **In VS Code:** the **NPM Scripts** section of the Explorer sidebar lists `dev`, `test` and `typecheck` as buttons.

### 5. The firmware

Open the `firmware` folder in VS Code (File, then Open Folder) so PlatformIO finds the project.

- **Laptop tests:** in the PlatformIO sidebar, choose **native**, then **Advanced**, then **Test**. The command is `pio test -e native`.
- **Flash the stake:** choose **seeed_xiao_esp32c3**, then **Upload**.
