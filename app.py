from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = "super_secret_santa_key"  # change before deployment


# ----------------------------
# Utility functions
# ----------------------------

def load_valid_ids():
    ids = set()
    with open("valid_ids.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                ids.add(line)
    return ids


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# Load data
VALID_IDS = load_valid_ids()
ASSIGNMENTS_PATH = "data/assignments.json"
WISHLISTS_PATH = "data/wishlists.json"


# ----------------------------
# Routes
# ----------------------------

@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()

        if user_id in VALID_IDS:
            session["user_id"] = user_id
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid Secret ID. Please try again."

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
        recipient_name = "Not assigned yet"
        wishlist = []
    else:
        recipient_name = recipient_id  # can later map ID → display name
        wishlist = wishlists.get(recipient_id, [])

    return render_template(
        "reveal.html",
        recipient=recipient_name,
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

    current_wishlist = wishlists.get(user_id, [])
    wishlist_text = "\n".join(current_wishlist)

    return render_template(
        "wishlist.html",
        wishlist=wishlist_text
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ----------------------------
# Run app
# ----------------------------

if __name__ == "__main__":
    app.run()
