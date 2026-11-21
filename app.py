import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db, init_db

app = Flask(__name__)
# Set SECRET_KEY in the environment for any real deployment.
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')

CATEGORIES = ['ID card', 'Electronics', 'Books', 'Accessories', 'Other']
TYPES = ['Lost', 'Found']
STATUSES = ['Open', 'Claimed', 'Returned']

init_db()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to continue.", "info")
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


@app.route('/')
def index():
    db = get_db()
    counts = {s: db.execute("SELECT COUNT(*) FROM items WHERE status=?", (s,)).fetchone()[0] for s in STATUSES}
    total = sum(counts.values())
    latest = db.execute("SELECT items.*, users.name AS reporter FROM items JOIN users ON users.id = items.user_id "
                        "ORDER BY created_at DESC LIMIT 3").fetchall()
    db.close()
    return render_template('index.html', counts=counts, total=total, latest=latest, categories=CATEGORIES)


@app.route('/items')
def items():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    item_type = request.args.get('type', '').strip()
    status = request.args.get('status', '').strip()

    sql = ("SELECT items.*, users.name AS reporter FROM items "
           "JOIN users ON users.id = items.user_id WHERE 1=1")
    args = []
    if q:
        sql += " AND (title LIKE ? OR location LIKE ? OR description LIKE ?)"
        args += [f"%{q}%"] * 3
    if category in CATEGORIES:
        sql += " AND category=?"
        args.append(category)
    if item_type in TYPES:
        sql += " AND item_type=?"
        args.append(item_type)
    if status in STATUSES:
        sql += " AND status=?"
        args.append(status)
    sql += " ORDER BY created_at DESC"

    db = get_db()
    rows = db.execute(sql, args).fetchall()
    db.close()
    return render_template('items.html', items=rows, q=q, category=category, item_type=item_type,
                           status=status, categories=CATEGORIES, types=TYPES, statuses=STATUSES)


@app.route('/item/new', methods=['GET', 'POST'])
@login_required
def new_item():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '')
        item_type = request.form.get('item_type', '')
        if not title or not location or not description:
            flash("Title, location and description are required.", "error")
        elif len(title) > 120:
            flash("Title must be 120 characters or fewer.", "error")
        elif category not in CATEGORIES or item_type not in TYPES:
            flash("Please choose a valid category and type.", "error")
        else:
            db = get_db()
            db.execute("INSERT INTO items (user_id, title, category, item_type, location, description, status, created_at) "
                       "VALUES (?, ?, ?, ?, ?, ?, 'Open', ?)",
                       (session['user_id'], title, category, item_type, location, description,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            db.commit()
            db.close()
            flash("Your item has been reported.", "success")
            return redirect(url_for('items'))
    return render_template('new_item.html', categories=CATEGORIES, types=TYPES)


@app.route('/item/<int:item_id>/claim', methods=['POST'])
@login_required
def claim(item_id):
    db = get_db()
    cur = db.execute("UPDATE items SET status='Claimed', claimed_by=? "
                     "WHERE id=? AND status='Open' AND user_id != ?",
                     (session['user_id'], item_id, session['user_id']))
    db.commit()
    db.close()
    if cur.rowcount:
        flash("Item marked as claimed. Please collect it through the security office.", "success")
    else:
        flash("This item cannot be claimed.", "error")
    return redirect(url_for('items'))


@app.route('/item/<int:item_id>/return', methods=['POST'])
@login_required
def mark_returned(item_id):
    db = get_db()
    cur = db.execute("UPDATE items SET status='Returned' WHERE id=? AND user_id=?",
                     (item_id, session['user_id']))
    db.commit()
    db.close()
    if cur.rowcount:
        flash("Item marked as returned.", "success")
    else:
        flash("Only the reporter can mark an item as returned.", "error")
    return redirect(url_for('items'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not name or not email:
            flash("Name and email are required.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        else:
            db = get_db()
            try:
                cur = db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                                 (name, email, generate_password_hash(password)))
                db.commit()
                session['user_id'] = cur.lastrowid
                session['user_name'] = name
                flash("Account created. Welcome!", "success")
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                flash("This email may already be registered.", "error")
            finally:
                db.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        db.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('index'))
        flash("Email or password is incorrect.", "error")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for('index'))


if __name__ == '__main__':
    # debug=True is for local development only.
    app.run(debug=True)
