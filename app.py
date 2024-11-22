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
        userbookings=list(bookings.find({"bookedBy":session['username']}))
        count=len(userbookings)
        return render_template("Dashboard.html", username=session['username'],userbookings=userbookings,count=count)
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
        ownerbookings=list(bookings.find({"uploadedBy":session['ownerusername']}))
        bookedbookings=list(bookings.find({"status":"booked"}))
        count=len(bookedbookings)
        ownergrounds=list(grounds.find({"uploadedowner":session['ownerusername']}))
        totalgrounds=len(ownergrounds)
        print()
        cost=0

        for i in bookedbookings:
            cost+=int(i['cost'])

        return render_template("ownerDashboard.html", ownername=session['ownerusername'],ownerbookings=ownerbookings,count=count,totalgrounds=totalgrounds,cost=cost)
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

@app.route("/ground/<ground_id>/slots", methods=['GET'])
def get_slots(ground_id):
    date = request.args.get('date')
    if not date:
        return jsonify({"message": "Date parameter is required"}), 400

    ground = grounds.find_one({"_id": ObjectId(ground_id)})
    if not ground:
        return jsonify({"message": "Ground not found"}), 404

    # All possible time slots
    all_time_slots = [
        "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM",
        "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM",
        "6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM",
        "10:00 PM"
    ]

    # Fetch booked and pending slots for the selected date
    booked_slots = bookings.find({
        "ground_id": ObjectId(ground_id),
        "booking_date": date,
        "$or": [
            {"status": "booked"},
            {"status": "pending"}
        ]
    })

    # Create a dictionary to track slot statuses
    slot_statuses = {}
    for booking in booked_slots:
        # Handle full-day booking
        if booking.get("booking_type") == "full_day":
            for slot in all_time_slots:
                slot_statuses[slot] = "booked" if booking["status"] == "booked" else "pending"
        else:
            # Handle individual slot bookings
            if "time_slots" in booking:
                for slot in booking["time_slots"]:
                    slot_statuses[slot] = "booked" if booking["status"] == "booked" else "pending"
            else:
                slot_statuses[booking["time_slot"]] = "booked" if booking["status"] == "booked" else "pending"

    # Prepare slot data with statuses
    time_slots = [
        {"time": slot, "status": slot_statuses.get(slot, "available")}
        for slot in all_time_slots
    ]

    return jsonify(time_slots), 200

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
        booked_time_slots = {}
        for booking in booked_slots:
            if booking.get("booking_type") == "full_day":
                # For full-day bookings, mark all time slots as booked
                for slot in [
                    "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM",
                    "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM",
                    "6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM",
                    "10:00 PM"
                ]:
                    booked_time_slots[slot] = True
            elif "time_slot" in booking:
                # Handle individual slot bookings
                booked_time_slots[booking["time_slot"]] = True

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
    groundname=ground['groundname']
    sportname=ground['groundtype']
    ownername=ground['uploadedowner']
    groundcost=ground['costperhour']
    if not ground:
        return jsonify({"message": "Ground not found."}), 404

    # Check if the slot is already booked
    existing_booking = bookings.find_one({
        "ground_id": ObjectId(ground_id),
        
        "time_slot": time_slot,
        "booking_date": booking_date,
        "status": "booked"
    })
    existing_pending=bookings.find_one({
        "ground_id": ObjectId(ground_id),
        
        "time_slot": time_slot,
        "booking_date": booking_date,
        "status": "pending"
    })
    
    if existing_booking or existing_pending:
        print("slot already booked")
        return jsonify({"message": "Slot is already booked!"}), 409

    # If the slot is available, create a new booking


    booking = {
        "ground_id": ObjectId(ground_id),
        "user_id": user["_id"],
        "groundname":groundname,
        "sportname":sportname,
        "uploadedBy":ownername,
        "bookedBy":session['username'],
        "time_slot": time_slot,
        "cost":groundcost,
        "booking_date": booking_date,
        "status": "pending"
    }
    bookings.insert_one(booking)

    return jsonify({"message": "Booking successful!"}), 200





@app.route("/ground/<ground_id>/check-full-day-availability", methods=['GET'])
def check_full_day_availability(ground_id):
    date = request.args.get('date')
    
    # All possible time slots for the day
    all_time_slots = [
        "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM",
        "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM",
        "6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM",
        "10:00 PM"
    ]

    # Check for any booked or pending slots
    booked_slots = bookings.find({
        "ground_id": ObjectId(ground_id),
        "booking_date": date,
        "$or": [
            {"status": "booked"},
            {"status": "pending"}
        ]
    })

    # Check if any slots are already booked
    booked_time_slots = set()
    for booking in booked_slots:
        # If it's a full-day booking, all slots are considered booked
        if booking.get("booking_type") == "full_day":
            return jsonify({
                "is_available": False,
                "booked_slots": all_time_slots
            })
        
        # For individual slot bookings
        if "time_slots" in booking:
            booked_time_slots.update(booking["time_slots"])
        else:
            booked_time_slots.add(booking["time_slot"])

    # Check if all slots are available
    is_available = len(booked_time_slots) == 0

    return jsonify({
        "is_available": is_available,
        "booked_slots": list(booked_time_slots)
    })

@app.route("/book-full-day", methods=['POST'])
def book_full_day():
    if 'username' not in session:
        return jsonify({"success": False, "message": "User not logged in."}), 401

    # Get request data
    data = request.json
    ground_id = data.get("ground_id")
    booking_date = data.get("booking_date")

    # Get user and ground details
    user = users.find_one({"username": session['username']})
    ground = grounds.find_one({"_id": ObjectId(ground_id)})

    if not ground:
        return jsonify({"success": False, "message": "Ground not found."}), 404

    # All possible time slots
    all_time_slots = [
        "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM",
        "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM",
        "6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM",
        "10:00 PM"
    ]

    # Prepare a single booking document for full-day booking
    full_day_booking = {
        "ground_id": ObjectId(ground_id),
        "user_id": user["_id"],
        "groundname": ground['groundname'],
        "sportname": ground['groundtype'],
        "uploadedBy": ground['uploadedowner'],
        "bookedBy": session['username'],
        "booking_date": booking_date,
        "cost": float(ground['costperhour']) * len(all_time_slots),
        "status": "pending",
        "booking_type": "full_day",
        "time_slots": all_time_slots  # Store all time slots in a single array
    }

    # Insert the full-day booking
    bookings.insert_one(full_day_booking)

    return jsonify({"success": True, "message": "Full day booking initiated!"})








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


@app.route("/deletebooking/<ownerbooking_id>", methods=['post'])
def delete_booking(ownerbooking_id):
    bookings.delete_one({"_id":ObjectId(ownerbooking_id)})
    return redirect(url_for("owner_dashboard"))

@app.route("/deletesbooking/<booking_id>", methods=['post'])
def delete_bookings(booking_id):
    bookings.delete_one({"_id":ObjectId(booking_id)})
    return redirect(url_for("user_dashboard"))

@app.route("/updatebooking/<ownerupdatebooking_id>" ,methods=['post'])
def ownerupdatebooking(ownerupdatebooking_id):
    bookings.update_one(
        {"_id": ObjectId(ownerupdatebooking_id)},  # Filter
        {"$set": {"status": "booked"}}             # Update
    )
    return redirect(url_for("owner_dashboard"))

@app.route("/rejectbooking/<ownerupdatebooking_id>" , methods=['post'])
def rejectbooking(ownerupdatebooking_id):
    bookings.update_one(
        {"_id": ObjectId(ownerupdatebooking_id)},  # Filter
        {"$set": {"status": "rejected"}}             # Update
    )
    return redirect(url_for("owner_dashboard"))


@app.route("/updateground/<ground_id>" ,methods=['post'])
def updateground(ground_id):
    ground = grounds.find_one({"_id": ObjectId(ground_id)})
    return render_template("updateground.html",ground=ground)


from flask import Flask, request, redirect, url_for
from bson import ObjectId

@app.route("/updatingground/<ground_id>", methods=['POST'])
def updatingground(ground_id):
    # Retrieve form data
    a = request.form.get("groundName")
    b = request.form.get("groundType")
    c = request.form.get("address")
    d = request.form.get("city")
    e = request.form.get("costPerHour")
    f = request.form.get("groundImage")

    # Prepare update data
    updatedata = {
        "groundname": a,
        "groundtype": b,
        "address": c,
        "city": d,
        "costperhour": e,  # Ensure numeric data for cost
        "groundimg": f
    }

    # Correct syntax for `update_one`
    grounds.update_one(
        {"_id": ObjectId(ground_id)},  # Filter
        {"$set": updatedata}           # Update
    )

    # Redirect to dashboard
    return redirect(url_for("mygrounds"))



# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(port=6020, debug=True)