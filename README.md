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
