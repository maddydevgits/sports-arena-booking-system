from flask import Flask, request, render_template, session, redirect, url_for ,jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId  
from datetime import datetime

# MongoDB Setup
cluster = MongoClient("127.0.0.1:27017")
db = cluster['sports-Arena']
owners = db['owners']
users = db['users']
grounds=db['grounds']
bookings = db['bookings']
# Flask Setup
app = Flask(__name__)
app.secret_key = "1234567890"

@app.route("/")
def home():
    return render_template("index.html")

# User Registration & Login Routes
@app.route("/user/register")
def user_register():
    return render_template("register.html", show_register=True, status="", status2="")

@app.route("/user/register", methods=['POST'])
def register_user():
    username = request.form.get('username')
    email = request.form.get('email')
    phone = request.form.get('phno')
    password = request.form.get('password')
    
    user = users.find_one({"email": email})
    if user:
        return render_template("register.html", show_register=True, status="Email already registered.", status2="")
    
    users.insert_one({"username": username, "email": email, "phno": phone, "password": password})
    return render_template("register.html", show_register=True, status="Registration successful. You can now log in.", status2="")

@app.route("/user/login", methods=['POST'])
def user_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = users.find_one({"email": email})
    if user and user['password'] == password:
        session['username'] = user['username']
        return redirect(url_for("user_dashboard"))
    
    return render_template("register.html", show_register=False, status="", status2="Invalid email or password.")

@app.route("/user/dashboard")
def user_dashboard():
    if 'username' in session:
        return render_template("Dashboard.html", username=session['username'])
    return redirect(url_for("user_register"))


@app.route("/findgrounds")
def find_grounds():
    if 'username' not in session:
        return redirect(url_for("user_login"))
    groundsdata=list(grounds.find())
    return render_template("findgrunds.html",groundsdata=groundsdata,username=session['username'])


# Owner Registration & Login Routes
@app.route("/owner/register")
def owner_register():
    return render_template("ownerregister.html", show_register=True, status="", status2="")

@app.route("/owner/register", methods=['POST'])
def register_owner():
    username = request.form.get('username')
    business_name = request.form.get('businessName')
    email = request.form.get('email')
    phone = request.form.get('phno')
    password = request.form.get('password')
    
    owner = owners.find_one({"email": email})
    if owner:
        return render_template("ownerregister.html", show_register=True, status="Email already registered.", status2="")
    
    owners.insert_one({"username": username, "businessname": business_name, "email": email, "phno": phone, "password": password})
    return render_template("ownerregister.html", show_register=True, status="Registration successful. You can now log in.", status2="")

@app.route("/owner/login", methods=['POST'])
def owner_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    owner = owners.find_one({"email": email})
    if owner and owner['password'] == password:
        session['ownerusername'] = owner['username']
        return redirect(url_for("owner_dashboard"))
    
    return render_template("ownerregister.html", show_register=False, status="", status2="Invalid email or password.")

@app.route("/owner/dashboard")
def owner_dashboard():
    if 'ownerusername' in session:
        return render_template("ownerDashboard.html", ownername=session['ownerusername'])
    return redirect(url_for("register_owner"))

@app.route("/addground")
def add_ground():
    return render_template("addground.html",ownername=session['ownerusername'])

@app.route("/addingground", methods=['post'])
def adding_ground():
    a=request.form.get("groundName")
    b=request.form.get("groundType")
    c=request.form.get("address")
    d=request.form.get("city")
    e=request.form.get("costPerHour")
    f=request.form.get("groundImage")
    ownername=session['ownerusername']
    grounds.insert_one({
        "groundname":a,
        "groundtype":b,
        "address":c,
        "city":d,
        "costperhour":e,
        "groundimg":f,
        "uploadedowner":ownername  
    })

    return render_template("addground.html",status="Ground uploaded successfully !")

@app.route("/mygrounds")
def mygrounds():
    if 'ownerusername' in session:
        ownergrounds=list(grounds.find({"uploadedowner":session['ownerusername']}))
        return render_template("mygrounds.html",groundlist=ownergrounds,ownername=session['ownerusername'])
    return redirect(url_for("register_owner"))


@app.route("/grounddetails")
def grounddetails():
    if 'username' in session:
        return render_template("book.html")
    return redirect(url_for("user_register"))

@app.route("/ground/<ground_id>")
def view_ground_details(ground_id):
    if 'username' in session:
        ground = grounds.find_one({"_id": ObjectId(ground_id)})

        if not ground:
            return "Ground not found!", 404

        # Example: Fetch bookings for today's date
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get all bookings for this ground and today
        booked_slots = bookings.find({
            "ground_id": ObjectId(ground_id),
            "booking_date": today,
            "status": "booked"
        })

        # Create a dictionary of booked time slots
        booked_time_slots = {booking["time_slot"]: True for booking in booked_slots}

        # Define all available time slots
        all_time_slots = [
            "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM",
            "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM",
            "6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM",
            "10:00 PM"
        ]

        # Prepare slot data with statuses
        time_slots = [
            {"time": slot, "status": "booked" if slot in booked_time_slots else "available"}
            for slot in all_time_slots
        ]

        return render_template("book.html", ground=ground, time_slots=time_slots, username=session['username'])

    return redirect(url_for("user_login"))

@app.route("/ground/<ground_id>/available-slots/<booking_date>")
def available_slots(ground_id, booking_date):
    ground = grounds.find_one({"_id": ObjectId(ground_id)})
    
    if not ground:
        return "Ground not found", 404

    # Define all possible time slots
    all_slots = [
        '10:00 AM', '11:00 AM', '12:00 PM', '1:00 PM', '2:00 PM', '3:00 PM',
        '4:00 PM', '5:00 PM', '6:00 PM', '7:00 PM', '8:00 PM', '9:00 PM', '10:00 PM'
    ]
    
    # Check which slots are booked
    booked_slots = bookings.find({"ground_id": ObjectId(ground_id), "booking_date": booking_date})
    booked_times = [booking["time_slot"] for booking in booked_slots]

    # Create a response indicating available slots
    available_slots = [
        {"time": slot, "status": "available" if slot not in booked_times else "booked"}
        for slot in all_slots
    ]
    
    return jsonify(available_slots)

# Route to book a slot for a ground
from flask import jsonify

@app.route("/book-slot", methods=['POST'])
def book_slot():
    if 'username' not in session:
        return jsonify({"message": "User not logged in. Please log in first."}), 401

    user = users.find_one({"username": session['username']})
    ground_id = request.json.get("ground_id")  # Updated to get JSON input
    time_slot = request.json.get("time_slot")
    booking_date = request.json.get("booking_date")

    print(ground_id, time_slot, booking_date, user)

    ground = grounds.find_one({"_id": ObjectId(ground_id)})

    if not ground:
        return jsonify({"message": "Ground not found."}), 404

    # Check if the slot is already booked
    existing_booking = bookings.find_one({
        "ground_id": ObjectId(ground_id),
        "time_slot": time_slot,
        "booking_date": booking_date,
        "status": "booked"
    })
    
    if existing_booking:
        return jsonify({"message": "Slot is already booked!"}), 409

    # If the slot is available, create a new booking
    booking = {
        "ground_id": ObjectId(ground_id),
        "user_id": user["_id"],
        "time_slot": time_slot,
        "booking_date": booking_date,
        "status": "booked"
    }
    bookings.insert_one(booking)

    return jsonify({"message": "Booking successful!"}), 200

# Route to show ground details and available time slots
@app.route("/ground/<ground_id>/book", methods=["GET"])
def ground_booking_page(ground_id):
    if 'username' not in session:
        return redirect(url_for("user_register"))
    
    ground = grounds.find_one({"_id": ObjectId(ground_id)})
    if not ground:
        return "Ground not found!", 404

    # Get available time slots for today (or a given date)
    today = datetime.today().strftime('%Y-%m-%d')
    return render_template("book.html", ground=ground, username=session['username'], booking_date=today)

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(port=6020, debug=True)