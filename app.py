from flask import Flask, render_template, request, redirect, jsonify, session
from datetime import datetime
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = "smart_parking_secret"

# ---------------- DATA (NO DB FOR VERCEL) ---------------- #

slots = ["A1", "A2", "A3", "A4", "A5"]
occupied = []
bookings = []

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

    occupied.append(slot)
    bookings.append((name, vehicle, slot, time))

    return f"""
    <html>
    <body style="background:#0f172a;color:white;text-align:center;font-family:Arial">
        <h1>Booking Success</h1>
        <h2>Name: {name}</h2>
        <h2>Vehicle: {vehicle}</h2>
        <h2>Slot: {slot}</h2>
        <h2>Time: {time}</h2>
        <img src="data:image/png;base64,{qr_image}">
        <br><br>
        <a href="/" style="color:white">Back Home</a>
    </body>
    </html>
    """

# ---------------- MAP ---------------- #

@app.route("/map")
def map_page():
    if "user" not in session:
        return redirect("/login")

    return render_template("map.html", data=bookings)

# ---------------- HISTORY ---------------- #

@app.route("/history")
def history():
    return render_template("history.html", data=bookings)

# ---------------- VACATE ---------------- #

@app.route("/vacate/<slot>")
def vacate(slot):

    if slot in occupied:
        occupied.remove(slot)

    return redirect("/")

# ---------------- LOCATION ---------------- #

@app.route("/location", methods=["POST"])
def location():
    return jsonify({"status": "ok"})

# ---------------- ENTRY POINT ---------------- #

if __name__ == "__main__":
    app.run()