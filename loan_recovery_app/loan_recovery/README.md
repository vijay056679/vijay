# Casefile — Loan Recovery Desk

A Flask web app for tracking loan recovery: borrowers, case files (loans), payments, and collection activity, with a custom "ledger / case-file" themed UI (dark ink sidebar, paper-toned case cards, rubber-stamp status badges, monospace ledger figures).

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5050** in your browser. The SQLite database (`recovery.db`) is created automatically on first run.

## Features

- **Ledger Overview** — dashboard with total cases, outstanding balance, total recovered, recovery rate, oldest overdue cases, and recent payments.
- **Case Files** — every loan shown as a case-file card with a case number, principal/outstanding figures, due date, and a status stamp (Active / Overdue / Recovered / Defaulted). Filterable by status.
- **Open New Case** — create a loan for an existing borrower or a brand-new one.
- **Case Detail** — recovery progress bar, full payment history, log-a-payment form, collection activity timeline (calls, SMS, field visits, legal notices), and manual status override.
- **Borrowers** — directory of all borrowers with outstanding totals, and a per-borrower case list.

## Notes

- Loan status auto-updates to **Overdue** once the due date passes (unless already Recovered/Defaulted), and to **Recovered** once outstanding balance hits zero.
- Case numbers are auto-generated as `CF-<year>-<sequence>`.
- This is a development setup (Flask's built-in server + SQLite). For production, run behind a WSGI server (e.g. gunicorn) and switch to a production database.
