# EduVision AI

Smart Examination Result Analytics System built with Flask, SQLite, scikit-learn, Chart.js, HTML, CSS, and JavaScript.

## Run Locally

```powershell
.venv\Scripts\python.exe app.py
```

Open:

```text
http://127.0.0.1:5000/
```

## Demo Accounts

- Admin: `admin` / `admin123`
- Teacher: `teacher` / `teacher123`
- Student: `STU001` / `student123`

## Highlights

- Role authentication for admins, teachers, and students
- Sign up, sign in, logout, and remember-me sessions
- Student marks entry, CSV/XLS/XLSX upload, search, filters, and ranking
- Linear Regression, Decision Tree, and Random Forest powered predictions
- AI confidence, improvement chance, weak/strong subjects, and recommendations
- Animated Chart.js dashboard with bar, line, doughnut, radar, scatter, and heatmap-style visuals
- PDF reports plus Excel and CSV exports
- Admin user management

Runtime data is stored in `instance/eduvision.db` locally. On Vercel, the demo database uses `/tmp/eduvision.db` so the serverless function can write safely during runtime.

## Deploy On Vercel

This project is Vercel-ready as a zero-config Flask backend. Push the repo to GitHub, import it into Vercel, and keep the framework preset as Flask or auto-detected Python.

Recommended environment variable:

- `SECRET_KEY`: set to a secure random value

For long-lived production data, set `DATABASE_URL` to a managed database. The default Vercel SQLite path is only for demos because serverless storage is temporary.

## Deploy On Render

Push this folder to a GitHub repository, then create a Render Web Service with:

- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Environment Variable: `SECRET_KEY` set to a secure random value

This repo also includes `render.yaml`, so Render can create the web service as a Blueprint.

Note: the default SQLite database is good for demos, but Render's filesystem is ephemeral. For a long-lived production deployment, switch `DATABASE_URL` to Render Postgres.
