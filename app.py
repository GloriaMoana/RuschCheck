import os
import sqlite3
from flask import Flask, render_template, request, jsonify, g, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sys

# Flask-Login
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin

# Add utils folder
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
from detection import average_people_in_video

BASE_DIR = os.path.dirname(__file__)
DATABASE = os.path.join(BASE_DIR, "data.sqlite")

# Upload folders
IMAGE_UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "images")
VIDEO_UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "videos")
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_UPLOAD_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif"}
ALLOWED_VIDEO_EXT = {"mp4", "mov", "avi", "mkv"}

app = Flask(__name__, static_url_path="/static")
app.secret_key = os.environ.get("RUSHCHECK_SECRET", "dev-secret-change-this")

login_manager = LoginManager()
login_manager.login_view = "admin_login"
login_manager.init_app(app)


# -------------------------
# DB HELPERS
# -------------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db:
        db.close()


def init_db():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id TEXT PRIMARY KEY,
            name TEXT,
            capacity INTEGER,
            image TEXT,
            address TEXT,
            video TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS status (
            id TEXT PRIMARY KEY,
            location_name TEXT,
            average_people INTEGER,
            capacity INTEGER,
            percent REAL,
            level TEXT,
            address TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
    """)

    db.commit()

    # Seed admin user
    cur = db.execute("SELECT username FROM admin_users WHERE username = ?", ("Admin195B",)).fetchone()
    if not cur:
        pw_hash = generate_password_hash("admin1")
        db.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)", ("Admin195B", pw_hash))
        db.commit()

    # Seed sample locations
    cur = db.execute("SELECT COUNT(*) as c FROM locations").fetchone()
    if cur["c"] == 0:
        sample = [
            ("student_union", "Student Union, SJSU", 33,
             "uploads/images/library.jpg", "Student Union, SJSU", "uploads/videos/lotsofpeoplewalking.mp4"),

            ("clark_hall", "Clark Hall, SJSU", 60,
             "uploads/images/library.jpg", "Clark Hall, SJSU", "uploads/videos/lotsofpeoplewalking.mp4"),

            ("engineering_building", "Engineering Building, SJSU", 150,
             "uploads/images/library.jpg", "Engineering Building, SJSU", "uploads/videos/lotsofpeoplewalking.mp4")
        ]

        for row in sample:
            db.execute("INSERT INTO locations (id,name,capacity,image,address,video) VALUES (?,?,?,?,?,?)", row)
        db.commit()


with app.app_context():
    init_db()


# -------------------------
# ADMIN USER CLASS
# -------------------------
class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(username):
    db = get_db()
    row = db.execute("SELECT username FROM admin_users WHERE username = ?", (username,)).fetchone()
    return AdminUser(row["username"]) if row else None


# -------------------------
# PUBLIC ROUTES
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/spaces")
def spaces():
    db = get_db()
    locs = db.execute("SELECT * FROM locations ORDER BY name").fetchall()
    statuses = {
        r["id"]: dict(r)
        for r in db.execute("SELECT * FROM status").fetchall()
    }
    locations = [dict(r) for r in locs]
    return render_template("spaces.html", locations=locations, statuses=statuses)


@app.route("/help")
def help_page():
    return render_template("help.html")


# -------------------------
# ADMIN ROUTES
# -------------------------
@app.route("/admin")
def admin_index():
    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        row = db.execute(
            "SELECT username, password_hash FROM admin_users WHERE username = ?",
            (username,)
        ).fetchone()

        if row and check_password_hash(row["password_hash"], password):
            login_user(AdminUser(row["username"]))
            return redirect(url_for("admin_dashboard"))

        error = "Invalid credentials"

    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    db = get_db()
    locs = db.execute("SELECT * FROM locations ORDER BY name").fetchall()
    statuses = db.execute("SELECT * FROM status ORDER BY updated_at DESC LIMIT 50").fetchall()
    return render_template("admin_dashboard.html",
                           locations=[dict(r) for r in locs],
                           statuses=[dict(r) for r in statuses])


# -------------------------
# API: ANALYZE
# -------------------------
@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json()
    loc_id = data.get("location")

    db = get_db()
    loc = db.execute("SELECT * FROM locations WHERE id = ?", (loc_id,)).fetchone()
    if not loc:
        return jsonify({"error": "Unknown location"}), 400

    loc = dict(loc)

    # Correctly build absolute path to video
    safe_video = loc["video"].replace("\\", "/")
    video_path = os.path.join(BASE_DIR, "static", *safe_video.split("/"))

    if not os.path.exists(video_path):
        return jsonify({"error": f"Video file not found: {loc['video']}"}), 404

    try:
        avg_people = average_people_in_video(video_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    capacity = loc.get("capacity", 100)
    percent = (avg_people / capacity) * 100 if capacity > 0 else 0
    level = "High" if percent > 60 else "Medium" if percent >= 40 else "Low"

    db.execute("""
        INSERT OR REPLACE INTO status
        (id, location_name, average_people, capacity, percent, level, address, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (loc_id, loc["name"], int(avg_people), capacity, round(percent,1), level, loc["address"]))
    db.commit()

    return jsonify({
        "id": loc_id,
        "location": loc["name"],
        "average_people": int(avg_people),
        "capacity": capacity,
        "percent": round(percent, 1),
        "level": level,
        "address": loc["address"],
    })


# -------------------------
# API: GET LAST STATUS (FIXED)
# -------------------------
@app.route("/api/get_last_status", methods=["POST"])
def get_last_status():
    data = request.get_json()
    loc_id = data.get("location")

    db = get_db()
    row = db.execute("SELECT * FROM status WHERE id = ?", (loc_id,)).fetchone()

    if not row:
        return jsonify({"error": "No previous data"}), 404

    return jsonify(dict(row))


# -------------------------
# ADMIN: ADD / EDIT LOCATION
# -------------------------
def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


@app.route("/admin/locations/add", methods=["POST"])
@login_required
def admin_locations_add():
    form = request.form
    key = form.get("id").strip()
    name = form.get("name").strip()
    capacity = int(form.get("capacity") or 0)
    address = form.get("address", "").strip()

    image_file = request.files.get("image")
    video_file = request.files.get("video")

    image_path = None
    video_path = None

    # Image upload
    if image_file and image_file.filename and allowed_file(image_file.filename, ALLOWED_IMAGE_EXT):
        fname = secure_filename(image_file.filename)
        image_file.save(os.path.join(IMAGE_UPLOAD_FOLDER, fname))
        image_path = f"uploads/images/{fname}"

    # Video upload
    if video_file and video_file.filename and allowed_file(video_file.filename, ALLOWED_VIDEO_EXT):
        vname = secure_filename(video_file.filename)
        video_file.save(os.path.join(VIDEO_UPLOAD_FOLDER, vname))
        video_path = f"uploads/videos/{vname}"

    final_image = image_path or "uploads/images/default.jpg"

    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO locations (id, name, capacity, image, address, video)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (key, name, capacity, final_image, address, video_path or ""))
    db.commit()

    flash("Location added/updated", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/locations/delete", methods=["POST"])
@login_required
def admin_locations_delete():
    key = request.form.get("id")
    db = get_db()
    db.execute("DELETE FROM locations WHERE id = ?", (key,))
    db.execute("DELETE FROM status WHERE id = ?", (key,))
    db.commit()
    flash("Location deleted", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/locations/edit", methods=["POST"])
@login_required
def admin_locations_edit():
    return admin_locations_add()


if __name__ == "__main__":
    app.run(debug=True)
