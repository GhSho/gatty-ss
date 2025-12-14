from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import date

app = Flask(__name__)
app.secret_key = "super_secret_santa_key_change_this"


# ----------------------------
# File paths
# ----------------------------

USERS_PATH = "users.json"
ASSIGNMENTS_PATH = "data/assignments.json"
WISHLISTS_PATH = "data/wishlists.json"


# ----------------------------
# Helpers
# ----------------------------

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_users():
    with open(USERS_PATH, "r") as f:
        return json.load(f)


USERS = load_users()


# ----------------------------
# Gift day (31st)
# ----------------------------

GIFT_DAY = date(date.today().year, date.today().month, 31)

def days_left():
    today = date.today()
    return max((GIFT_DAY - today).days, 0)


# ----------------------------
# Routes
# ----------------------------

@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        pin = request.form.get("pin", "").strip()

        user = USERS.get(user_id)

        if user and user["pin"] == pin:
            session["user_id"] = user_id
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid ID or PIN."

    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["user_id"],
        days_left=days_left()
    )


@app.route("/reveal")
def reveal():
    if "user_id" not in session:
        return redirect(url_for("login"))

    assignments = load_json(ASSIGNMENTS_PATH, {})
    wishlists = load_json(WISHLISTS_PATH, {})

    user_id = session["user_id"]
    recipient = assignments.get(user_id)
    wishlist = wishlists.get(recipient, []) if recipient else []

    return render_template(
        "reveal.html",
        recipient=recipient or "Not assigned yet",
        wishlist=wishlist
    )


@app.route("/wishlist", methods=["GET", "POST"])
def wishlist():
    if "user_id" not in session:
        return redirect(url_for("login"))

    wishlists = load_json(WISHLISTS_PATH, {})
    user_id = session["user_id"]

    if request.method == "POST":
        items = request.form.get("wishlist", "")
        wishlists[user_id] = [i.strip() for i in items.split("\n") if i.strip()]
        save_json(WISHLISTS_PATH, wishlists)
        return redirect(url_for("dashboard"))

    return render_template(
        "wishlist.html",
        wishlist="\n".join(wishlists.get(user_id, []))
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ----------------------------
# ADMIN (SAFE)
# ----------------------------

@app.route("/admin")
def admin():
    assignments = load_json(ASSIGNMENTS_PATH, {})
    wishlists = load_json(WISHLISTS_PATH, {})

    return f"""
    <h2>Admin Panel</h2>
    <p>Total users: {len(USERS)}</p>
    <p>Assignments generated: {len(assignments)}</p>
    <p>Wishlists filled: {len(wishlists)}</p>
    <br>
    <a href="/admin/reset">Reset for next year</a>
    """


@app.route("/admin/reset")
def admin_reset():
    save_json(ASSIGNMENTS_PATH, {})
    save_json(WISHLISTS_PATH, {})
    return "✅ Reset complete. Ready for next year."


# ----------------------------
# Run locally
# ----------------------------

if __name__ == "__main__":
    app.run()
