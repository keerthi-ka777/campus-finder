# Campus Finder: Smart Campus Lost and Found Management System

Full Stack Technologies, AAT-2 project. A Flask + SQLite web app where students report lost or found items,
search and filter them, claim open items, and track each item until it is returned.

> Listings are user-submitted and are not verified by the college administration.
> Hand over valuable items through the security office.

## Features
- Register / sign in (hashed passwords, Flask sessions)
- Report Lost or Found items (title, category, location, description)
- Search by keyword; filter by category, type and status
- Status tracking: Open -> Claimed -> Returned
- Other users can claim an Open item; only the reporter can mark it Returned
- Dashboard statistics on the home page

## Tech stack
Python 3.10+, Flask, Jinja2, SQLite (sqlite3), HTML5, CSS3, vanilla JavaScript

## Run locally
```bash
git clone <your-repo-url>
cd campus-finder
python -m venv venv
venv\Scripts\activate        # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000. The database `campus_finder.db` is created automatically with demo items.

## Structure
```
app.py            routes, validation, sessions
database.py       connection helper, schema, demo data
templates/        Jinja2 templates (base, index, items, new_item, login, register)
static/css, js    styling and small client script
```

## Known limitations
No admin role, image upload, or edit/delete. Claims are not verified. Add CSRF protection, a strong SECRET_KEY,
disable debug mode and make sign-out a POST request before any public deployment.
