# Daily Grind — Café Management System

A small café dashboard with a seeded menu, customer/table orders, preparation status tracking, and completed-sales totals. Orders are stored in SQLite; prices use integer paise and display in INR.

## Run

Requires Python 3.12 or newer. No third-party dependencies or installation needed.

```sh
python app.py
```

Open port 8000 in your local browser. Configure `HOST` (default `127.0.0.1`), `PORT` (default `8000`), and `CAFE_DB` (default `data/cafe.db`) as needed. Data is created on first launch and retained between restarts. Back up the SQLite database before deleting or relocating it. An optional Google Fonts stylesheet is used; system fonts work offline.

## Workflow

Choose menu items, enter a customer or table name, and place an order. Advance orders from Preparing to Ready to Completed, or cancel active orders. Only completed orders count toward all-time sales. Refresh the order board to see updates from other sessions.

```sh
python -m unittest discover -s tests -v
```

Tests use a temporary database and exercise the real HTTP server, validation, totals, transitions, and persistence. This is a single-user development app without authentication; keep it on a trusted local network. Authentication and deployment hardening are required before public use.

## Deploy to Render

This repository includes a Render Blueprint (`render.yaml`) for a Python web service with a 1 GB persistent disk. **It uses a paid Starter service and paid storage.** Review the price in Render before approving creation; the free service does not preserve the SQLite database across deployments.

1. Sign in at https://dashboard.render.com/ and choose **New → Blueprint**.
2. Connect GitHub and select `kkrish00870-source/cafe-mangement-system`, branch `main`.
3. Review the service and disk, then create the Blueprint.
4. Once deployed, open the service URL shown by Render. Sign in with username `admin` and the generated `CAFE_PASSWORD` from the service's Environment settings. Keep this password private; you can replace it securely in Render.

Render supplies HTTPS and PORT. HOST binds the server to all interfaces. `/healthz` provides an unauthenticated database readiness check; the dashboard, static assets, and API require HTTP Basic authentication when CAFE_PASSWORD is set. On Render, missing CAFE_PASSWORD blocks application access. Local development remains password-free unless you set CAFE_PASSWORD. Do not expose Basic authentication over plain HTTP outside localhost.

This is a lightweight prototype built with Python's standard-library HTTP server, which is not recommended for production use. The password gate provides shared access, not per-user roles or auditing. Before using it for business-critical operations, migrate to a production application server and add database backups, user accounts, and operational monitoring. Persistent storage survives deployments but is not a backup.
