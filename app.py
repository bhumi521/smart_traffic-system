from flask import Flask, render_template, request, redirect, jsonify, session
from datetime import datetime
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = "smart_parking_secret"

# ---------------- DATA ---------------- #
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

    name = request.form.get("name")
    vehicle = request.form.get("vehicle")

    # find slot
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

    bookings.append({
        "name": name,
        "vehicle": vehicle,
        "slot": slot,
        "time": time
    })

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

    return render_template("admin.html", data=bookings)

# ---------------- HISTORY ---------------- #
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    return render_template("history.html", data=bookings)

# ---------------- VACATE ---------------- #
@app.route("/vacate/<slot>")
def vacate(slot):
    if slot in occupied:
        occupied.remove(slot)
    return redirect("/")

# ---------------- API ---------------- #
@app.route("/location", methods=["POST"])
def location():
    return jsonify({"status": "ok"})

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)