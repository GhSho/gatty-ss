from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import random

app = Flask(__name__)
app.secret_key = "super_secret_santa_key_change_this"


# ----------------------------
# File paths
# ----------------------------

USERS_PATH = "users.json"
ASSIGNMENTS_PATH = "data/assignments.json"
WISHLISTS_PATH = "data/wishlists.json"


# ----------------------------
# Utility functions
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

    return render_template("dashboard.html")


@app.route("/reveal")
def reveal():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    assignments = load_json(ASSIGNMENTS_PATH, {})
    wishlists = load_json(WISHLISTS_PATH, {})

    recipient_id = assignments.get(user_id)

    if not recipient_id:
        recipient = "Not assigned yet"
        wishlist = []
    else:
        recipient = recipient_id
        wishlist = wishlists.get(recipient_id, [])

    return render_template(
        "reveal.html",
        recipient=recipient,
        wishlist=wishlist
    )


@app.route("/wishlist", methods=["GET", "POST"])
def wishlist():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    wishlists = load_json(WISHLISTS_PATH, {})

    if request.method == "POST":
        items = request.form.get("wishlist", "")
        wishlist_items = [i.strip() for i in items.split("\n") if i.strip()]
        wishlists[user_id] = wishlist_items
        save_json(WISHLISTS_PATH, wishlists)
        return redirect(url_for("dashboard"))

    current = wishlists.get(user_id, [])
    wishlist_text = "\n".join(current)

    return render_template("wishlist.html", wishlist=wishlist_text)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ----------------------------
# ADMIN: Generate assignments
# ----------------------------

@app.route("/admin/generate")
def generate_assignments():
    """
    Generates Secret Santa assignments with rules:
    - No one gets themselves
    - No one gifts within the same family
    """

    users = USERS
    user_ids = list(users.keys())

    max_attempts = 1000

    for _ in range(max_attempts):
        shuffled = user_ids[:]
        random.shuffle(shuffled)

        assignments = {}
        valid = True

        for giver, receiver in zip(user_ids, shuffled):
            if giver == receiver:
                valid = False
                break
            if users[giver]["family"] == users[receiver]["family"]:
                valid = False
                break
            assignments[giver] = receiver

        if valid:
            save_json(ASSIGNMENTS_PATH, assignments)
            return "✅ Secret Santa assignments generated successfully."

    return "❌ Could not generate valid assignments. Check family groups."


# ----------------------------
# Run locally only
# ----------------------------

if __name__ == "__main__":
    app.run()

 

