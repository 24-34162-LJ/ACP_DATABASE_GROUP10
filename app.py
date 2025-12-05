from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify, current_app, abort
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, AddTerminal
from models import (
    db, User, Terminal, Jeepney, Trip, Seat, TerminalJeepneys,
    Route, Auditlog, Userfavorite, Notification
)

from forms import (
    UserForm, TerminalForm, RouteForm, JeepneyForm,
    TripForm, SeatForm, TerminalJeepneysForm,
    UserfavoriteForm, NotificationForm, AuditlogForm
)

from datetime import datetime
from sqlalchemy import func

# ---------------- GLOBAL CONSTANTS ----------------
MAIN_TERMINAL_ID = 1


# ---------------- FLASK APP SETUP ----------------
app = Flask(__name__)

app.config['SECRET_KEY'] = 'lj123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jeep.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False

db.init_app(app)

#-------------------------------------------------
MODEL_MAP = {
    "users": User,
    "terminals": Terminal,
    "routes": Route,
    "jeepneys": Jeepney,
    "trips": Trip,
    "seats": Seat,
    "terminaljeeps": TerminalJeepneys,
    "userfavorites": Userfavorite,
    "notifications": Notification,
    "auditlogs": Auditlog,
}

FORM_MAP = {
    "users": UserForm,
    "terminals": TerminalForm,
    "routes": RouteForm,
    "jeepneys": JeepneyForm,
    "trips": TripForm,
    "seats": SeatForm,
    "terminaljeeps": TerminalJeepneysForm,
    "userfavorites": UserfavoriteForm,
    "notifications": NotificationForm,
    "auditlogs": AuditlogForm,
}

# ---------------- BASIC PAGES ----------------
@app.route('/home')
def home():
    return render_template("index.html")


@app.route('/view')
def view():
    data = {
        "users": User.query.all(),
        "terminals": Terminal.query.all(),
        "jeepneys": Jeepney.query.all(),
        "terminal_queue": TerminalJeepneys.query.all(),
        "trips": Trip.query.all(),
        "seats": Seat.query.all(),
        "routes": Route.query.all(),
        "favorites": Userfavorite.query.all(),
        "notifications": Notification.query.all(),
        "auditlogs": Auditlog.query.all(),
    }
    return render_template("view_database.html", data=data)


# ---------------- AUTH ----------------
@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if request.method == 'POST':
        print("FORM DATA:", form.data)
        print("FORM ERRORS:", form.errors)

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):

            session['user_id'] = user.user_id
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name
            session['role'] = user.role

            flash('Login successful!', 'success')

            # Redirect based on role
            if session['role'] == 'player':
                return redirect(url_for("commuter"))
            elif session['role'] == 'operator':
                return redirect(url_for("operator"))
            elif session['role'] == 'viewer':
                return redirect(url_for("commuter"))
            else:
                return redirect(url_for("admin"))

        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@app.route('/sign', methods=['GET', 'POST'])
def sign():
    form = RegisterForm()

    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        role = form.role.data
        email = form.email.data
        password = form.password.data

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email already registered. Try another.", "danger")
            return redirect(url_for("sign"))

        hashed_pw = generate_password_hash(password)

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hashed_pw,
            role=role,
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! You may now log in.", "success")
        return redirect(url_for("login"))

    return render_template("sign.html", form=form)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))


@app.route("/")
def index():
    return redirect(url_for("home"))

# ---------------- ROLE PAGES ----------------
@app.route("/commuter")
def commuter():
    return render_template("commuter.html")


@app.route("/operator")
def operator():
    main_id = current_app.config["MAIN_TERMINAL_ID"]
    terminals = Terminal.query.all()
    return render_template(
        "operator.html",
        terminals=terminals,
        main_terminal_id=main_id
        )


@app.route("/operator/seat/<int:terminal_id>")
def operator_seat(terminal_id):
    terminal = Terminal.query.get_or_404(terminal_id)
    return render_template(
        "operator_seat.html",
        terminal_id=terminal_id,
        terminal_name=terminal.terminal_name
    )


@app.route("/addterminal", methods=['GET', 'POST'])
def Add():
    form = AddTerminal()

    if form.validate_on_submit():
        terminal_name = form.terminal_name.data
        location = form.location.data

        terminal = Terminal(
            terminal_name=terminal_name,
            location=location
        )

        db.session.add(terminal)
        db.session.commit()
        flash("data added in database")
        return redirect(url_for("operator"))
    return render_template("terminal.html", form=form)
    

@app.route('/delete/<string:model>/<int:id>', methods=['POST'])
def delete_record(model, id):
    model_class = MODEL_MAP.get(model)
    if model_class is None:
        abort(404)

    obj = model_class.query.get_or_404(id)
    db.session.delete(obj)
    db.session.commit()
    flash(f'{model.capitalize()} record deleted successfully', "success")
    return redirect(url_for('view'))

@app.route('/edit/<string:model>/<int:id>', methods=['GET', 'POST'])
def update_record(model, id):
    model_class = MODEL_MAP.get(model)
    form_class = FORM_MAP.get(model)

    if model_class is None or form_class is None:
        abort(404)

    obj = model_class.query.get_or_404(id)

    # Bind form to existing object
    form = form_class(obj=obj)

    # ---------- fill choices for SelectFields depending on model ----------
    if model == "routes":
        form.start_terminal_id.choices = [
            (t.terminal_id, t.terminal_name) for t in Terminal.query.all()
        ]
        form.end_terminal_id.choices = [
            (t.terminal_id, t.terminal_name) for t in Terminal.query.all()
        ]

    if model == "trips":
        form.jeepney_id.choices = [
            (j.jeepney_id, j.plate_number) for j in Jeepney.query.all()
        ]
        form.route_id.choices = [
            (r.route_id, r.route_name) for r in Route.query.all()
        ]
        form.origin_terminal_id.choices = [
            (t.terminal_id, t.terminal_name) for t in Terminal.query.all()
        ]
        form.destination_terminal_id.choices = [
            (t.terminal_id, t.terminal_name) for t in Terminal.query.all()
        ]

    if model == "seats":
        form.trip_id.choices = [
            (t.trip_id, f"Trip {t.trip_id}") for t in Trip.query.all()
        ]

    if model == "terminaljeeps":
        form.terminal_id.choices = [
            (t.terminal_id, t.terminal_name) for t in Terminal.query.all()
        ]
        form.jeepney_id.choices = [
            (j.jeepney_id, j.plate_number) for j in Jeepney.query.all()
        ]

    if model == "userfavorites":
        form.user_id.choices = [
            (u.user_id, f"{u.first_name} {u.last_name}") for u in User.query.all()
        ]
        form.terminal_id.choices = [
            (t.terminal_id, t.terminal_name) for t in Terminal.query.all()
        ]
        form.route_id.choices = [
            (r.route_id, r.route_name) for r in Route.query.all()
        ]

    if model == "notifications":
        form.user_id.choices = [
            (u.user_id, f"{u.first_name} {u.last_name}") for u in User.query.all()
        ]
        form.trip_id.choices = [
            (t.trip_id, f"Trip {t.trip_id}") for t in Trip.query.all()
        ]

    if model == "auditlogs":
        form.user_id.choices = [
            (u.user_id, f"{u.first_name} {u.last_name}") for u in User.query.all()
        ]

    # ---------- handle POST ----------
    if form.validate_on_submit():
        # Copy form data into the SQLAlchemy object
        form.populate_obj(obj)
        db.session.commit()
        flash(f"{model.capitalize()} updated successfully!", "success")
        return redirect(url_for('view'))   # back to your DB viewer

    # GET or failed validation
    return render_template('edit_form.html', form=form, model=model)


@app.route("/admin")
def admin():
    return render_template("admin.html")


# ---------------- MAP + MAIN TERMINAL PAGES ----------------
from flask import current_app

@app.route("/map")
def map_view():
    main_id = current_app.config.get("MAIN_TERMINAL_ID", MAIN_TERMINAL_ID)

    terminals = (
        Terminal.query
        .filter(Terminal.terminal_id != main_id)
        .order_by(Terminal.terminal_id.asc())
        .limit(4)
        .all()
    )

    return render_template("map.html", terminals=terminals, main_terminal_id=main_id)


# SEAT SIMULATION PAGE PER TERMINAL
@app.route("/seat/<int:terminal_id>")
def seat(terminal_id):
    main_id = current_app.config["MAIN_TERMINAL_ID"]
    if terminal_id == main_id:
        # redirect main seat page to mainterminal UI
        return redirect(url_for("mainterminal"))

    terminal = Terminal.query.get_or_404(terminal_id)
    return render_template(
        "seat.html",
        terminal_id=terminal_id,
        terminal_name=terminal.terminal_name,
        main_terminal_id=main_id
    )


@app.route("/mainterminal")
def mainterminal():
    main_id = current_app.config["MAIN_TERMINAL_ID"]
    terminals = Terminal.query.all()
    return render_template(
        "mainterminal.html",
        terminals=terminals,
        main_terminal_id=main_id
    )

@app.route("/main-destination")
def main_destination():
    # re-use mainterminal.html for now
    terminals = Terminal.query.order_by(Terminal.terminal_id.asc()).all()
    return render_template(
        "mainterminal.html",
        terminals=terminals,
        main_terminal_id=MAIN_TERMINAL_ID
    )


# ---------------- API: QUEUE DATA FOR A TERMINAL ----------------
@app.route("/api/terminal/<int:terminal_id>/queue")
def api_terminal_queue(terminal_id):
    """
    Returns jeepneys currently in this terminal's queue (Waiting/Boarding).
    If may multiple rows for the same jeepney_id, we keep only
    the latest (pinaka-bagong arrival_time).
    """
    rows = (
        TerminalJeepneys.query
        .filter_by(terminal_id=terminal_id)
        .filter(TerminalJeepneys.status.in_(["Waiting", "Boarding"]))
        .order_by(TerminalJeepneys.arrival_time.asc())
        .all()
    )

    # keep only latest per jeepney_id
    latest_by_jeep = {}
    for r in rows:
        j_id = r.jeepney_id
        if j_id not in latest_by_jeep:
            latest_by_jeep[j_id] = r
        else:
            # choose the row with the newest arrival_time
            if r.arrival_time and latest_by_jeep[j_id].arrival_time:
                if r.arrival_time > latest_by_jeep[j_id].arrival_time:
                    latest_by_jeep[j_id] = r
            else:
                # kung may null sa arrival_time, keep the one that is not null
                latest_by_jeep[j_id] = r

    data = []
    for r in latest_by_jeep.values():
        jeep = r.jeep_jeep_fk  # relationship to Jeepney
        data.append({
            "jeepney_id": jeep.jeepney_id,
            "plate_number": jeep.plate_number,
            "capacity": jeep.capacity,
            "passengers": r.current_passengers or 0,
        })

    return jsonify(data)




# ---------------- API: WHEN JEEP DEPARTS FROM MAIN TERMINAL ----------------
@app.route("/api/trips/depart-from-main", methods=["POST"])
def api_trip_depart_from_main():
    """
    Jeep departs from MAIN going back to its origin terminal.
    We DO NOT trust destination_terminal_id from frontend.
    Instead, we look at the last trip that arrived to MAIN and
    send the jeep back to that origin terminal.
    """
    data = request.get_json() or {}

    jeepney_id = data.get("jeepney_id")
    passengers = data.get("passengers", 0)

    if not jeepney_id:
        return jsonify({"error": "jeepney_id is required"}), 400

    main_id = current_app.config["MAIN_TERMINAL_ID"]

    jeep = Jeepney.query.get_or_404(jeepney_id)
    capacity = jeep.capacity

    # 1) Find latest queue row in MAIN (Waiting/Arrived) and mark it Departed
    tj_main = (
        TerminalJeepneys.query
        .filter_by(terminal_id=main_id, jeepney_id=jeepney_id)
        .order_by(TerminalJeepneys.arrival_time.desc())
        .first()
    )

    if tj_main:
        tj_main.status = "Departed"
        tj_main.departure_time = datetime.utcnow()
        tj_main.current_passengers = passengers

    # 2) Find the last trip that ARRIVED TO MAIN for this jeep
    #    That trip's origin_terminal_id will be the new destination
    last_inbound_trip = (
        Trip.query
        .filter_by(jeepney_id=jeepney_id, destination_terminal_id=main_id)
        .order_by(Trip.arrival_time.desc())
        .first()
    )

    if not last_inbound_trip:
        return jsonify({
            "error": "No inbound trip to MAIN found for this jeep, cannot determine origin terminal."
        }), 400

    destination_terminal_id = last_inbound_trip.origin_terminal_id

    # 3) Create NEW trip: MAIN -> PREVIOUS ORIGIN
    trip = Trip(
        jeepney_id=jeepney_id,
        route_id=data.get("route_id", 1),
        origin_terminal_id=main_id,
        destination_terminal_id=destination_terminal_id,
        departure_time=datetime.utcnow(),
        status="En Route",
    )
    db.session.add(trip)
    db.session.flush()

    # 4) Seat summary
    seat = Seat(
        trip_id=trip.trip_id,
        total_seats=capacity,
        occupied_seats=passengers,
        available_seats=max(capacity - passengers, 0),
    )
    db.session.add(seat)

    jeep.status = "En Route"
    db.session.commit()

    return jsonify({"trip_id": trip.trip_id}), 201


# ---------------- API: ADD JEEP TO TERMINAL ----------------
@app.route("/api/terminal/<int:terminal_id>/jeepneys", methods=["POST"])
def api_add_jeep_to_terminal(terminal_id):
    """
    Operator adds a new jeepney to the system AND assigns it
    to the given terminal's queue as 'Waiting'.
    """
    data = request.get_json()

    plate_number = data.get("plate_number")
    capacity = data.get("capacity", 22)

    if not plate_number:
        return jsonify({"error": "plate_number is required"}), 400

    # 1) Create new Jeepney record
    jeep = Jeepney(
        plate_number=plate_number,
        capacity=capacity,
        status="Available"
    )
    db.session.add(jeep)
    db.session.flush()  # so jeep.jeepney_id is available

    # 2) Attach it to this terminal as 'Waiting'
    tj = TerminalJeepneys(
        terminal_id=terminal_id,
        jeepney_id=jeep.jeepney_id,
        arrival_time=datetime.utcnow(),
        status="Waiting"
    )
    db.session.add(tj)

    db.session.commit()

    return jsonify({
        "jeepney_id": jeep.jeepney_id,
        "plate_number": jeep.plate_number,
        "capacity": jeep.capacity,
        "terminal_id": terminal_id
    }), 201


# ---------------- API: LIST TERMINALS ----------------
@app.route("/api/terminals")
def api_terminals():
    terminals = Terminal.query.all()
    return jsonify([
        {
            "terminal_id": t.terminal_id,
            "terminal_name": t.terminal_name,
            "location": t.location
        }
        for t in terminals
    ])


# ---------------- API: UPDATE PASSENGERS IN TERMINAL QUEUE ----------------
@app.route("/api/terminal/<int:terminal_id>/jeepneys/<int:jeepney_id>/passengers", methods=["PATCH"])
def api_update_terminal_jeep_passengers(terminal_id, jeepney_id):
    data = request.get_json()
    new_passengers = data.get("passengers")

    if new_passengers is None:
        return jsonify({"error": "passengers is required"}), 400

    tj = (
        TerminalJeepneys.query
        .filter_by(terminal_id=terminal_id, jeepney_id=jeepney_id)
        .order_by(TerminalJeepneys.arrival_time.desc())
        .first()
    )

    if not tj:
        return jsonify({"error": "TerminalJeep entry not found"}), 404

    tj.current_passengers = new_passengers
    db.session.commit()

    return jsonify({"ok": True, "current_passengers": tj.current_passengers})


# ---------------- API: MAIN ORIGIN JEEPS (FOR MAINTERMINAL UI) ----------------
@app.route("/api/main/origin-jeeps")
def api_main_origin_jeeps():
    """
    Returns the latest 'Departed' jeep from each ORIGIN terminal
    that is currently en route to MAIN TERMINAL.
    """

    main_id = current_app.config.get("MAIN_TERMINAL_ID", MAIN_TERMINAL_ID)


    # Subquery → find latest departure per terminal    
    subq = (
        db.session.query(
            TerminalJeepneys.terminal_id,
            func.max(TerminalJeepneys.departure_time).label("max_dep")
        )
        .filter(
            TerminalJeepneys.status == "Departed",
            TerminalJeepneys.terminal_id != main_id      # ← exclude MAIN
        )
        .group_by(TerminalJeepneys.terminal_id)
        .subquery()
    )
    
    rows = (
        db.session.query(TerminalJeepneys, Jeepney, Terminal)
        .join(
            subq,
            (TerminalJeepneys.terminal_id == subq.c.terminal_id) &
            (TerminalJeepneys.departure_time == subq.c.max_dep)
        )
        .join(Jeepney, TerminalJeepneys.jeepney_id == Jeepney.jeepney_id)
        .join(Terminal, TerminalJeepneys.terminal_id == Terminal.terminal_id)
        .filter(Terminal.terminal_id != main_id)  # extra guard
        .order_by(TerminalJeepneys.terminal_id.asc())
        .all()
    )


    result = []

    for tj, jeep, term in rows:

        # Skip jeeps NOT going to MAIN TERMINAL
        trip = (
            Trip.query
            .filter_by(
                jeepney_id=jeep.jeepney_id,
                status="En Route",
                destination_terminal_id=main_id
            )
            .order_by(Trip.departure_time.desc())
            .first()
        )

        if not trip:
            continue  # jeep is not currently heading to MAIN

        result.append({
            "jeepney_id": jeep.jeepney_id,
            "plate_number": jeep.plate_number,
            "terminal_id": term.terminal_id,
            "terminal_name": term.terminal_name,
            "capacity": jeep.capacity,
            "passengers": tj.current_passengers or 0
        })

    return jsonify(result[:4])

# ---------------- API: LIVE TRIPS FOR MAP ANIMATION ----------------
# ---------------- API: LIVE TRIPS FOR MAP ANIMATION ----------------
@app.route("/api/map/live-trips")
def api_map_live_trips():
    main_id = current_app.config.get("MAIN_TERMINAL_ID", MAIN_TERMINAL_ID)

    rows = (
        db.session.query(
            Trip.trip_id,
            Trip.jeepney_id,
            Trip.origin_terminal_id,
            Trip.destination_terminal_id,
            Trip.status,
            Jeepney.capacity,
            Seat.occupied_seats.label("passengers")
        )
        .join(Jeepney, Trip.jeepney_id == Jeepney.jeepney_id)
        .outerjoin(Seat, Seat.trip_id == Trip.trip_id)
        .filter(Trip.status == "En Route")
        .filter(
            (Trip.origin_terminal_id == main_id) |
            (Trip.destination_terminal_id == main_id)
        )
        .all()
    )

    result = []
    for row in rows:
        result.append({
            "trip_id": row.trip_id,
            "jeepney_id": row.jeepney_id,
            "origin_terminal_id": row.origin_terminal_id,
            "destination_terminal_id": row.destination_terminal_id,
            "status": row.status,
            "capacity": row.capacity,
            "passengers": row.passengers or 0,
        })

    # quick debug if you want:
    # print("LIVE TRIPS:", result)

    return jsonify(result)

@app.route("/api/map/completed-trips")
def api_map_completed_trips():
    trips = Trip.query.filter(Trip.status.in_(["Arrived", "Completed"])).all()
    return jsonify([
        {
            "trip_id": t.trip_id,
            "jeepney_id": t.jeepney_id,
            "origin_terminal_id": t.origin_terminal_id,
            "destination_terminal_id": t.destination_terminal_id
        }
        for t in trips
    ])
    
# ---------------- API: WHEN JEEP DEPARTS FROM AN ORIGIN TERMINAL ----------------
@app.route("/api/trips/depart", methods=["POST"])
def api_trip_depart():
    """
    Jeep departs from an ORIGIN terminal going to MAIN.
    - Marks latest TerminalJeepneys row at origin as 'Departed'
    - Creates Trip(status='En Route') + Seat summary
    """
    data = request.get_json() or {}

    jeepney_id = data.get("jeepney_id")
    origin_id = data.get("origin_terminal_id")
    destination_id = data.get("destination_terminal_id")
    passengers = data.get("passengers", 0)

    if not (jeepney_id and origin_id and destination_id):
        return jsonify({"error": "Missing fields"}), 400

    jeep = Jeepney.query.get_or_404(jeepney_id)
    cap = jeep.capacity

    # latest queue row sa ORIGIN
    tj = (
        TerminalJeepneys.query
        .filter_by(terminal_id=origin_id, jeepney_id=jeepney_id)
        .order_by(TerminalJeepneys.arrival_time.desc())
        .first()
    )
    if not tj:
        return jsonify({"error": "No queue row at origin"}), 404

    tj.status = "Departed"
    tj.departure_time = datetime.utcnow()
    tj.current_passengers = passengers

    trip = Trip(
        jeepney_id=jeepney_id,
        route_id=data.get("route_id", 1),
        origin_terminal_id=origin_id,
        destination_terminal_id=destination_id,
        departure_time=datetime.utcnow(),
        status="En Route",
    )
    db.session.add(trip)
    db.session.flush()

    seat = Seat(
        trip_id=trip.trip_id,
        total_seats=cap,
        occupied_seats=passengers,
        available_seats=max(cap - passengers, 0),
    )
    db.session.add(seat)

    jeep.status = "En Route"

    db.session.commit()

    return jsonify({"trip_id": trip.trip_id}), 201

@app.route("/api/trips/arrive", methods=["POST"])
def api_trip_arrive():
    """
    Called by the map when a jeep finishes travelling.
    - Marks last 'Departed' TerminalJeepneys row as 'Arrived'
    - Marks last 'En Route' Trip as 'Arrived'
    - Creates a NEW TerminalJeepneys row at destination with status 'Waiting'
    """
    data = request.get_json() or {}

    jeepney_id = data.get("jeepney_id")
    origin_id = data.get("origin_terminal_id")
    destination_id = data.get("destination_terminal_id")

    if not (jeepney_id and origin_id and destination_id):
        return jsonify({"error": "Missing fields"}), 400

    # last departed row (either from origin or from MAIN)
    tj = (
        TerminalJeepneys.query
        .filter_by(jeepney_id=jeepney_id, status="Departed")
        .order_by(TerminalJeepneys.departure_time.desc())
        .first()
    )
    if not tj:
        return jsonify({"error": "No departed record found"}), 404

    tj.status = "Arrived"
    tj.arrival_time = datetime.utcnow()
    arrived_passengers = tj.current_passengers or 0

    trip = (
        Trip.query
        .filter_by(jeepney_id=jeepney_id, status="En Route")
        .order_by(Trip.departure_time.desc())
        .first()
    )
    if trip:
        trip.status = "Arrived"
        trip.arrival_time = datetime.utcnow()

    new_record = TerminalJeepneys(
        terminal_id=destination_id,
        jeepney_id=jeepney_id,
        arrival_time=datetime.utcnow(),
        departure_time=None,
        status="Waiting",
        current_passengers=arrived_passengers
    )

    db.session.add(new_record)
    db.session.commit()

    return jsonify({
        "message": "Jeepney arrival recorded",
        "jeepney_id": jeepney_id,
        "from": origin_id,
        "to": destination_id,
        "arrived_passengers": arrived_passengers
    }), 200


# ---------------- MAIN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
        
               # Sample users
        if not User.query.filter_by(email='admin@gmail.com').first():
            admin = User(
                first_name='Admin',
                last_name='User',
                email='admin@gmail.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            viewer = User(
                first_name='Viewer',
                last_name='User',
                email='viewer@gmail.com',
                password_hash=generate_password_hash('viewer123'),
                role='viewer'
            )
            db.session.add_all([admin, viewer])
            db.session.commit()
            
        # check if a main terminal exists
        main = Terminal.query.filter_by(is_main=True).first()

        if not main:
            main = Terminal(
                terminal_name="Main Terminal",
                location="Main Hub, Batangas",
                is_main=True
            )
            db.session.add(main)
            db.session.commit()
        # SAVE the dynamic main terminal ID to config
        app.config["MAIN_TERMINAL_ID"] = main.terminal_id

    app.run(debug=True)

