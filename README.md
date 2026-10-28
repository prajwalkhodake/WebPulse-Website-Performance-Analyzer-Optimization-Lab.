# WebPulse — Website Performance Analyzer & Optimization Lab

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Alembic](https://img.shields.io/badge/Migrations-Alembic-red?style=flat)](https://alembic.sqlalchemy.org/)
[![License](https://img.shields.io/badge/Academic-Computer%20Engineering%20Capstone-blue)](#)

> **WebPulse** is an advanced, portfolio-grade developer tool for analyzing website source code, identifying performance and code-quality issues, mapping dependencies, and executing controlled browser performance tests before deployment.

---

## 1. Project Abstract & Problem Statement

### Problem Statement
Standard web performance diagnostic utilities (such as Google PageSpeed Insights, GTmetrix, or WebPageTest) operate externally and require publicly accessible URLs with live DNS routing. Consequently:
- Un-deployed, local web projects (e.g., student portfolios, internal enterprise apps) cannot be evaluated using traditional tools.
- Developers often remain unaware of render-blocking stylesheets, uncompressed raster graphics, broken relative paths, or circular dependencies until after production deployment.

### Solution
**WebPulse** bridges this gap by enabling developers to upload local ZIP archives into an isolated laboratory environment:
1. **Static Code Inspection:** Scans HTML, CSS, JavaScript, and asset structures using Beautiful Soup and AST tokenizers.
2. **Dependency Graphing:** Visualizes file relationships with Cytoscape.js.
3. **Controlled Browser Testing:** Executes entry points in a Playwright Chromium sandbox to measure actual Navigation Timing and resource waterfalls.
4. **Transparent Scoring & Actionable Diffs:** Compares sequential project versions without fabricating imaginary scores.

---

## 2. Architecture & Technology Stack

```
                   +-----------------------------------------------+
                   |              Client / Web Browser             |
                   |   Bootstrap 5 + Jinja2 + Vanilla JS + Chart   |
                   +-----------------------+-----------------------+
                                           | HTTP / CSRF
                                           v
                   +-----------------------------------------------+
                   |            Flask Application Factory          |
                   |       (app/__init__.py: create_app())         |
                   +-------+---------------+---------------+-------+
                           |               |               |
             +-------------v----+    +-----v---------+   +-v-------------+
             |   Auth Blueprint |    | Main & Errors |   |   Dashboard   |
             |   (/auth/*)      |    | (/, /about)   |   |   (/dashboard)|
             +-------------+----+    +---------------+   +---------------+
                           |
            +--------------v----------------+
            |      SQLAlchemy 2 ORM         |
            |     Alembic Schema Versioning |
            +--------------+----------------+
                           |
             +-------------v----+     +---------------------------+
             |  SQLite Database |     |  Private Storage Engine   |
             |  (instance/...)  |     |  (storage/uploads & ext)  |
             +------------------+     +---------------------------+
```

### Technology Highlights
- **Backend:** Python 3.13+, Flask 3.1.3, Flask-SQLAlchemy, Flask-Login, Flask-WTF (CSRF tokens), Flask-Migrate (Alembic).
- **Database:** SQLite with SQLAlchemy ORM and Alembic migration scripts.
- **Frontend:** Jinja2 templates, Bootstrap 5.3, Bootstrap Icons, custom developer palette (`app/static/css/webpulse.css`), Vanilla JS.
- **Security:** Werkzeug password hashing (PBKDF2/Scrypt), anti-Zip-Slip path normalization, 50MB upload ceiling, HTTP-only secure cookie settings.

---

## 3. Directory Layout

```
WebPulse/
├── app/
│   ├── __init__.py           # Application Factory (create_app)
│   ├── extensions.py         # db, migrate, login_manager, csrf instances
│   ├── models/
│   │   ├── __init__.py       # Model exports
│   │   └── user.py           # User model (Flask-Login UserMixin, password hashing)
│   ├── auth/
│   │   ├── __init__.py       # Auth blueprint definition
│   │   ├── forms.py          # WTForms: Registration, Login, Account settings
│   │   └── routes.py         # /login, /register, /logout, /account
│   ├── main/
│   │   ├── __init__.py       # Main blueprint
│   │   └── routes.py         # Landing (/), Features (/features), About (/about)
│   ├── dashboard/
│   │   ├── __init__.py       # Dashboard blueprint
│   │   └── routes.py         # Authenticated workspace dashboard
│   ├── errors/
│   │   ├── __init__.py       # Errors blueprint
│   │   └── handlers.py       # Custom 403, 404, 413, 500 error handlers
│   ├── static/
│   │   ├── css/webpulse.css  # WebPulse design system, dark slate theme
│   │   └── js/main.js        # Micro-interactions, alerts, loader feedback
│   └── templates/
│       ├── base.html         # Master layout with Google Fonts & Bootstrap
│       ├── components/       # Reusable components: navbar, footer, sidebar, flash
│       ├── main/             # Landing, features, and about templates
│       ├── auth/             # Login, register, and account settings templates
│       ├── dashboard/        # Workspace dashboard template
│       └── errors/           # Custom error pages (403, 404, 413, 500)
├── instance/                 # SQLite database & local storage
├── migrations/               # Alembic database migration scripts
├── storage/                  # Isolated upload & extraction directories (outside static)
├── tests/
│   ├── conftest.py           # Pytest test fixtures (client, db, test_user)
│   ├── test_auth.py          # Authentication & authorization test suite
│   └── test_main.py          # Public routes, errors & security header tests
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── config.py                 # Multi-tier configuration (Dev, Test, Prod)
├── pytest.ini                # Pytest path and runner configuration
├── requirements.txt          # Exact pinned dependencies
├── run.py                    # Local development server entry point
└── wsgi.py                   # Production WSGI entry point
```

---

## 4. Installation & Local Setup (macOS / VS Code)

### Prerequisites
- macOS Sonoma or later (or Linux/Windows)
- Python 3.11+ (Python 3.13 recommended)

### Step 1: Clone or Navigate to Directory
```bash
cd "/Users/prajwalkhodake/Desktop/Projects/WebPulse — Website Performance Analyzer & Optimization Lab"
```

### Step 2: Set Up Virtual Environment
```bash
# Create virtual environment if not already present
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Step 3: Install Pinned Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
```bash
cp .env.example .env
```

### Step 5: Database Migrations
Initialize and apply database migrations with Flask-Migrate / Alembic:
```bash
export FLASK_APP=run.py
flask db upgrade
```

---

## 5. Running the Application

### Development Server
```bash
python run.py
```
Or via the Flask CLI:
```bash
flask --app run.py run --port 5000 --debug
```
Open your browser to: **`http://127.0.0.1:5000`**

---

## 6. Running Automated Tests

Run the comprehensive pytest suite:
```bash
pytest
```
Or with verbose output:
```bash
pytest -v
```
All 28 tests verify:
- Registration validation, duplicate rejection, and password length constraints
- Werkzeug cryptographic password hashing
- Session management, login, logout, and protected route redirection
- Account settings updates
- Public page rendering (Home, Features, About)
- Custom error page handling (404, 403, 413, 500)
- Security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`)
- Anti-Zip-Slip directory traversal rejection (`../../etc/passwd`)
- Private storage extraction and file inventory
- Static analysis checks across HTML, CSS, JS, and image assets
- Interactive Cytoscape.js dependency graph data API
- Playwright Chromium sandboxed browser runner & Core Web Vitals (FCP, LCP, CLS, TTFB)
- Network request waterfall tracing and status code inspection
- Deterministic multi-factor recommendation engine
- Version comparison diffs (resolved findings, new issues, metrics deltas)
- Standalone printable HTML audit reports and JSON export

---

## 7. Roadmap Status — All 8 Phases Complete!

- [x] **Phase 1 — Foundation & Architecture**: App factory, MySQL/SQLite support with SQLAlchemy 2, Alembic migrations, dark developer UI (`webpulse.css`), secure authentication system, test suite.
- [x] **Phase 2 — Projects & Upload Ingestion**: Project CRUD, anti-Zip-Slip archive validator, private storage extraction, file inventory with SHA-256 hashes, one-click demo seeder.
- [x] **Phase 3 — Static Analysis Engine**: HTML/CSS/JS parser, evidence-backed findings with line numbers, code snippets, severity levels (`critical`, `warning`, `info`), confidence ratings, search and filters.
- [x] **Phase 4 — Dependency Mapping & Visual Graph**: Cytoscape.js interactive network graph, broken link detection, node detail inspector, zoom/pan/center controls, JSON graph data API.
- [x] **Phase 5 — Prioritized Recommendations & Executive Dashboard**: Deterministic multi-factor scoring engine, categorized action plans with code snippets, live KPI metrics cards.
- [x] **Phase 6 — Controlled Browser Performance Testing**: Playwright headless Chromium runner, loopback ephemeral server (`127.0.0.1:0`), Core Web Vitals (FCP, LCP, CLS), TTFB, network request waterfall table.
- [x] **Phase 7 — Comparison, Diffing & Export**: Side-by-side version comparison diffs, resolved vs new findings, metrics delta, printable standalone HTML audit report, structured JSON export.
- [x] **Phase 8 — Final Polish, Documentation & Automated QA**: 28 automated tests passing in 3.4s, comprehensive documentation, and sample project seeder.

---

## 8. Database Support (MySQL & SQLite)

WebPulse supports both MySQL (recommended for production/local dev) and SQLite (for zero-config testing):

### Using MySQL
1. Ensure your MySQL server is running.
2. In your `.env` file, set:
```ini
DATABASE_URL=mysql+pymysql://webpulse_user:YourStrongPassword123!@localhost:3306/webpulse_db
```
3. Run Alembic migrations:
```bash
flask db upgrade
```

### Using SQLite
Leave `DATABASE_URL` commented out or set to:
```ini
DATABASE_URL=sqlite:///webpulse.db
```
