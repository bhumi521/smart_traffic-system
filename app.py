from flask import Flask, render_template, request, redirect, jsonify, session
import sqlite3
from datetime import datetime
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = "smart_parking_secret"

# ---------------- DATABASE ---------------- #
conn = sqlite3.connect("parking.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS bookings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    vehicle_number TEXT,
    slot TEXT,
    booking_time TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

conn.commit()

# ---------------- DATA ---------------- #
slots = ["A1", "A2", "A3", "A4", "A5"]
occupied = []

# ---------------- QR GENERATOR ---------------- #
def generate_qr(data):
    qr = qrcode.make(data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

# ---------------- HOME ---------------- #
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("home.html", slots=slots, occupied=occupied)

# ---------------- LOGIN ---------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur.execute("SELECT * FROM users WHERE username=? AND password=?",
                    (username, password))
        user = cur.fetchone()

        if user:
            session["user"] = username
            return redirect("/")
        else:
            return "❌ Invalid Login"

    return render_template("login.html")

# ---------------- REGISTER ---------------- #
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur.execute("INSERT INTO users(username, password) VALUES (?, ?)",
                    (username, password))
        conn.commit()

        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGOUT ---------------- #
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------------- BOOK SLOT ---------------- #
@app.route("/book", methods=["POST"])
def book():

    if "user" not in session:
        return redirect("/login")

    name = request.form["name"]
    vehicle = request.form["vehicle"]

    # find slot
    slot = None
    for s in slots:
        if s not in occupied:
            slot = s
            break

    if slot is None:
        return "❌ No Slots Available"

    time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    qr_data = f"{name}-{vehicle}-{slot}-{time}"
    qr_image = generate_qr(qr_data)

    # save DB
    cur.execute("""
        INSERT INTO bookings(username, vehicle_number, slot, booking_time)
        VALUES (?, ?, ?, ?)
    """, (name, vehicle, slot, time))

    conn.commit()

    occupied.append(slot)

    return render_template(
        "qr.html",
        name=name,
        vehicle=vehicle,
        slot=slot,
        time=time,
        qr=qr_image
    )

# ---------------- ADMIN ---------------- #
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/login")

    cur.execute("SELECT * FROM bookings")
    data = cur.fetchall()

    return render_template("admin.html", data=data, total=len(data))

# ---------------- HISTORY ---------------- #
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    cur.execute("SELECT * FROM bookings")
    data = cur.fetchall()

    return render_template("history.html", data=data)

# ---------------- LOCATION API ---------------- #
@app.route("/location", methods=["POST"])
def location():
    return jsonify({"status": "received"})

# ---------------- SCAN ---------------- #
@app.route("/scan")
def scan():
    if "user" not in session:
        return redirect("/login")
    return render_template("scan.html")
#---------------------MAP---------------
@app.route("/map")
def map_page():
    cur.execute("SELECT * FROM bookings")
    data = cur.fetchall()
    return render_template("map.html", data=data)

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)