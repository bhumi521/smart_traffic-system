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

conn.commit()

# ---------------- DATA ---------------- #

slots = ["A1", "A2", "A3", "A4", "A5"]
occupied = []

# ---------------- QR ---------------- #

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
        session["user"] = request.form["username"]
        return redirect("/")
    return render_template("login.html")

# ---------------- BOOK SLOT ---------------- #

@app.route("/book", methods=["POST"])
def book():

    if "user" not in session:
        return redirect("/login")

    name = request.form.get("name")
    vehicle = request.form.get("vehicle")

    slot = None
    for s in slots:
        if s not in occupied:
            slot = s
            break

    if slot is None:
        return "No Slots Available"

    time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    qr_data = f"{name}|{vehicle}|{slot}|{time}"
    qr_image = generate_qr(qr_data)

    cur.execute("""
        INSERT INTO bookings(username, vehicle_number, slot, booking_time)
        VALUES (?, ?, ?, ?)
    """, (name, vehicle, slot, time))

    conn.commit()

    occupied.append(slot)

    return f"""
    <html>
    <body style="background:#0f172a;color:white;text-align:center;font-family:Arial">
        <h1>Booking Success</h1>
        <h2>{name}</h2>
        <h2>{vehicle}</h2>
        <h2>{slot}</h2>
        <img src="data:image/png;base64,{qr_image}">
        <br><br>
        <a href="/" style="color:white">Back</a>
    </body>
    </html>
    """

# ---------------- MAP ---------------- #

@app.route("/map")
def map_page():
    if "user" not in session:
        return redirect("/login")

    cur.execute("SELECT * FROM bookings")
    data = cur.fetchall()

    return render_template("map.html", data=data)

# ---------------- HISTORY ---------------- #

@app.route("/history")
def history():
    cur.execute("SELECT * FROM bookings")
    data = cur.fetchall()
    return render_template("history.html", data=data)

# ---------------- VACATE ---------------- #

@app.route("/vacate/<slot>")
def vacate(slot):

    if slot in occupied:
        occupied.remove(slot)

    cur.execute("DELETE FROM bookings WHERE slot=?", (slot,))
    conn.commit()

    return redirect("/")

# ---------------- LOCATION ---------------- #

@app.route("/location", methods=["POST"])
def location():
    return jsonify({"status": "ok"})

# ---------------- ENTRY POINT (IMPORTANT) ---------------- #

if __name__ == "__main__":
    app.run()