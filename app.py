from flask import Flask, render_template, request, redirect, jsonify, session
import sqlite3
from datetime import datetime
import qrcode
import io
import base64
import webbrowser

app = Flask(__name__)
app.secret_key = "smart_parking_secret"

# ---------------- DB ---------------- #

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

# ---------------- QR ---------------- #

def generate_qr(data):
    qr = qrcode.make(data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

# ---------------- LOGIN ---------------- #

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("home.html", slots=slots, occupied=occupied)

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

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------------- BOOK SLOT ---------------- #
@app.route("/book", methods=["POST"])
def book():

    if "user" not in session:
        return redirect("/login")

    name = request.form.get("name")
    vehicle = request.form.get("vehicle")

    # Find empty slot
    slot = None

    for s in slots:
        if s not in occupied:
            slot = s
            break

    if slot is None:
        return "❌ No Slots Available"

    # Time
    time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # QR
    qr_data = f"{name} | {vehicle} | {slot} | {time}"

    qr_image = generate_qr(qr_data)

    # Save DB
    cur.execute("""
        INSERT INTO bookings(
            username,
            vehicle_number,
            slot,
            booking_time
        )
        VALUES (?, ?, ?, ?)
    """, (name, vehicle, slot, time))

    conn.commit()

    occupied.append(slot)

    # Direct HTML response
    return f"""

    <html>

    <head>

        <title>Booking Success</title>

        <style>

            body {{
                background: #0f172a;
                color: white;
                text-align: center;
                font-family: Arial;
            }}

            .box {{
                margin-top: 50px;
            }}

            img {{
                width: 250px;
            }}

        </style>

    </head>

    <body>

        <div class="box">

            <h1>✅ Booking Successful</h1>

            <h2>Name: {name}</h2>

            <h2>Vehicle: {vehicle}</h2>

            <h2>Slot: {slot}</h2>

            <h2>Time: {time}</h2>

            <img src="data:image/png;base64,{qr_image}">

            <br><br>

            <a href="/" style="
                color:white;
                background:#38bdf8;
                padding:10px 20px;
                text-decoration:none;
                border-radius:10px;
            ">
                🔙 Back Home
            </a>

        </div>

    </body>

    </html>

    """

# ---------------- VACATE SLOT ---------------- #

@app.route("/vacate/<slot>")
def vacate(slot):

    # Remove slot from occupied list
    if slot in occupied:
        occupied.remove(slot)

    # Delete from database
    cur.execute(
        "DELETE FROM bookings WHERE slot=?",
        (slot,)
    )

    conn.commit()

    return redirect("/")
# ---------------- HISTORY ---------------- #
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/login")

    cur.execute("SELECT * FROM bookings")
    data = cur.fetchall()

    total = len(data)

    return render_template("admin.html", data=data, total=total)
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    cur.execute("SELECT * FROM bookings")
    data = cur.fetchall()
    return render_template("history.html", data=data)

# ---------------- LOCATION ---------------- #

@app.route("/location", methods=["POST"])
def location():
    data = request.get_json()
    return jsonify({"status": "received"})

# ---------------- MAP ---------------- #

@app.route("/map")
def map_page():

    # Login check
    if "user" not in session:
        return redirect("/login")

    # Fetch booking data
    cur.execute("SELECT * FROM bookings")

    data = cur.fetchall()

    # Open map page
    return render_template(
        "map.html",
        data=data
    )

# ---------------- SCAN ---------------- #

@app.route("/scan")
def scan():
    if "user" not in session:
        return redirect("/login")
    return render_template("scan.html")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
