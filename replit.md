# Running Sprout on Replit

Use **Run** to start the React dashboard and FastAPI service. The dashboard opens in Preview on port 5000. The current checkout renders the checkpoint C1 placeholder; FastAPI starts on port 8000 and serves `/docs` and `/openapi.json`, but has no application routes yet.

## Restore dependencies

From the repository root, with Node.js 22, Python 3.12, and `uv` available:

```bash
npm --prefix web ci
uv export --project server --locked --no-dev --no-emit-project -o .cache/sprout-server-requirements.txt
uv pip install --target .cache/sprout-server -r .cache/sprout-server-requirements.txt
```

The API workflow loads these Python packages from `.cache/sprout-server`. Rerun the install commands after importing a fresh copy or changing a lockfile.

## Checks and database

```bash
npm --prefix web run typecheck
npm --prefix web test
npm --prefix web run build
```

The current preview and API startup do not need database credentials. Database-backed features require an external MySQL **8.4** server reachable from Replit. When one is available, add its SQLAlchemy connection string as `DATABASE_URL` through Replit Secrets; use a development database, never the live one. See `.env.example` for the URL format. No database is provisioned or migrated by the Run workflows.

Backend tests run against a separate, disposable MySQL 8.4 database in GitHub Actions. Do not run them against the development or production database: the fixtures truncate tables.
