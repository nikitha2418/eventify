"""AI Event Planner — Flask application (multi-page + login).

Pages:
  /register   create an account
  /login      sign in
  /logout     sign out
  /           the planner (protected)
  /history    your saved plans (protected)
  /plan/<id>  view one saved plan (protected)

API:
  /api/generate   POST event details -> Groq few-shot plan, saved to DB
  /health         server + database check
"""
import json
import sqlite3
from functools import wraps

from flask import (
    Flask, jsonify, render_template, request,
    session, redirect, url_for, flash,
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
import ai_service
import db

app = Flask(__name__)
app.config.from_object(Config)

# Create tables on startup if they don't exist yet (zero setup).
db.init_db()


# ---------- Auth helpers ----------

def login_required(view):
    """Decorator: redirect to /login if the user isn't signed in."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    """Make the current username available to every template."""
    return {"current_user": session.get("username")}


# ---------- Auth routes ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            flash("Username and password are required.", "error")
        elif len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            try:
                db.create_user(username, generate_password_hash(password))
            except sqlite3.IntegrityError:
                flash("That username is already taken.", "error")
            else:
                flash("Account created! Please log in.", "success")
                return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db.get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ---------- Pages ----------

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/history")
@login_required
def history():
    plans = db.get_plans_for_user(session["user_id"])
    return render_template("history.html", plans=plans)


@app.route("/plan/<int:plan_id>")
@login_required
def view_plan(plan_id):
    row = db.get_plan(plan_id, session["user_id"])
    if row is None:
        flash("Plan not found.", "error")
        return redirect(url_for("history"))
    plan = json.loads(row["plan_json"])
    return render_template("view_plan.html", row=row, plan=plan)


@app.route("/plan/<int:plan_id>/delete", methods=["POST"])
@login_required
def delete_plan(plan_id):
    deleted = db.delete_plan(plan_id, session["user_id"])
    flash("Plan deleted." if deleted else "Plan not found.",
          "success" if deleted else "error")
    return redirect(url_for("history"))


# ---------- API ----------

@app.route("/api/generate", methods=["POST"])
@login_required
def generate():
    """Generate a plan with Groq and save it for the logged-in user."""
    data = request.get_json(silent=True) or {}

    if not str(data.get("event_type", "")).strip():
        return jsonify(error="event_type is required"), 400

    try:
        plan = ai_service.generate_plan(data)
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 502

    # Persist the plan so it appears on the History page.
    plan_id = db.save_plan(session["user_id"], data, json.dumps(plan))
    return jsonify(plan=plan, plan_id=plan_id)


@app.route("/health")
def health():
    """Quick check that the server is up and the database is reachable."""
    try:
        db_ok = db.ping()
    except Exception as exc:  # noqa: BLE001
        return jsonify(status="error", database=False, detail=str(exc)), 500
    return jsonify(status="ok", database=db_ok)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)
