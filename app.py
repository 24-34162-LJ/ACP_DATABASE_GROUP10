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
from sqlalchemy import func, or_, and_  
from functools import wraps

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

def set_form_choices(form, model):
    """Fill SelectField choices depending on the model name."""
    if model == "routes":
        terminals = Terminal.query.all()
        term_choices = [(t.terminal_id, t.terminal_name) for t in terminals]
        form.start_terminal_id.choices = term_choices
        form.end_terminal_id.choices = term_choices

    elif model == "trips":
        jeepneys = Jeepney.query.all()
        routes = Route.query.all()
        terminals = Terminal.query.all()

        form.jeepney_id.choices = [(j.jeepney_id, j.plate_number) for j in jeepneys]
        form.route_id.choices = [(r.route_id, r.route_name) for r in routes]
        term_choices = [(t.terminal_id, t.terminal_name) for t in terminals]
        form.origin_terminal_id.choices = term_choices
        form.destination_terminal_id.choices = term_choices

    elif model == "seats":
        trips = Trip.query.all()
        form.trip_id.choices = [(t.trip_id, f"Trip {t.trip_id}") for t in trips]

    elif model == "terminaljeeps":
        terminals = Terminal.query.all()
        jeepneys = Jeepney.query.all()
        form.terminal_id.choices = [(t.terminal_id, t.terminal_name) for t in terminals]
        form.jeepney_id.choices = [(j.jeepney_id, j.plate_number) for j in jeepneys]

    elif model == "userfavorites":
        users = User.query.all()
        terminals = Terminal.query.all()
        routes = Route.query.all()
        form.user_id.choices = [(u.user_id, f"{u.first_name} {u.last_name}") for u in users]
        form.terminal_id.choices = [(t.terminal_id, t.terminal_name) for t in terminals]
        form.route_id.choices = [(r.route_id, r.route_name) for r in routes]

    elif model == "notifications":
        users = User.query.all()
        trips = Trip.query.all()
        form.user_id.choices = [(u.user_id, f"{u.first_name} {u.last_name}") for u in users]
        form.trip_id.choices = [(t.trip_id, f"Trip {t.trip_id}") for t in trips]

    elif model == "auditlogs":
        users = User.query.all()
        form.user_id.choices = [(u.user_id, f"{u.first_name} {u.last_name}") for u in users]
    
    elif model == "jeepneys":
    # 🔥 THIS is what fills the terminal dropdown
        form.terminal_id.choices = [
            (t.terminal_id, t.terminal_name) for t in Terminal.query.all()
    ]
        
def create_notification(user_id, trip_id, type_nof, message):
    """
    Low-level helper to insert a notification row.
    """
    notif = Notification(
        user_id=user_id,
        trip_id=trip_id,
        type_nof=type_nof,   # 'Arrival', 'Departure', 'FullCapacity', 'System'
        message=message
    )
    db.session.add(notif)


def notify_trip_event(trip, type_nof, custom_message=None):
    """
    Send a notification to users who have this route/origin/destination as favorite.
    - trip: Trip object
    - type_nof: 'Arrival' | 'Departure' | 'FullCapacity'
    """

    # Which users are "subscribed"?
    # Rule: any Userfavorite that matches this trip's route OR terminals.
    favs = (
        Userfavorite.query
        .filter(
            or_(
                Userfavorite.route_id == trip.route_id,
                Userfavorite.terminal_id == trip.origin_terminal_id,
                Userfavorite.terminal_id == trip.destination_terminal_id,
            )
        )
        .all()
    )

    if not favs:
        return  # no subscribers; nothing to do

    user_ids = {f.user_id for f in favs}

    jeep = Jeepney.query.get(trip.jeepney_id)
    origin = Terminal.query.get(trip.origin_terminal_id)
    dest = Terminal.query.get(trip.destination_terminal_id)

    default_msg = ""
    if type_nof == "Departure":
        default_msg = (
            f"Jeep {jeep.plate_number} has departed from "
            f"{origin.terminal_name} to {dest.terminal_name}."
        )
    elif type_nof == "Arrival":
        default_msg = (
            f"Jeep {jeep.plate_number} has arrived at "
            f"{dest.terminal_name} from {origin.terminal_name}."
        )
    elif type_nof == "FullCapacity":
        default_msg = (
            f"Jeep {jeep.plate_number} on route {origin.terminal_name} → "
            f"{dest.terminal_name} is now at full capacity."
        )
    else:
        default_msg = "Trip update."

    message = custom_message or default_msg

    for uid in user_ids:
        create_notification(
            user_id=uid,
            trip_id=trip.trip_id,
            type_nof=type_nof,
            message=message
        )
        
def create_audit_log(action, table_name, record_id, description=None, user_id=None):
    """
    Create a simple audit log entry.
    - action: 'INSERT', 'UPDATE', or 'DELETE'
    - table_name: string (e.g. 'users', 'jeepneys')
    - record_id: primary key of the affected record
    - description: optional message
    - user_id: if None, use current logged in user (session['user_id'])
    """
    if user_id is None:
        user_id = session.get("user_id")

    # if no user (e.g. system startup), skip
    if not user_id:
        return

    log = Auditlog(
        user_id=user_id,
        table_name=table_name,
        record_id=record_id,
        action=action,
        description=description
    )
    db.session.add(log)

# ---------------- BASIC PAGES ----------------
@app.route('/home')
def home():
    return render_template("index.html")

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to use this feature.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


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

@app.route("/search", methods=["GET"])
def search():
    route_query = request.args.get("route", "", type=str).strip()
    location_query = request.args.get("location", "", type=str).strip()

    # --- ROUTE SEARCH ---
    routes = []
    if route_query:
        # search by route name (ex: "Lipa", "Tanauan", "Main to Lipa")
        routes = (
            Route.query
            .filter(Route.route_name.ilike(f"%{route_query}%"))
            .all()
        )

    # --- TERMINAL FILTER BY LOCATION ---
    terminals = []
    if location_query:
        # ex: "Batangas", "Lipa", "Sto. Tomas"
        terminals = (
            Terminal.query
            .filter(Terminal.location.ilike(f"%{location_query}%"))
            .all()
        )

    return render_template(
        "search.html",
        route_query=route_query,
        location_query=location_query,
        routes=routes,
        terminals=terminals,
    )

@app.route("/addterminal", methods=['GET', 'POST'])
def Add():
    form = AddTerminal()

    if form.validate_on_submit():
        terminal_name = form.terminal_name.data
        location = form.location.data
        route_name = form.route_name.data
        est_time = form.estimated_time_minutes.data

        # 1) Create terminal
        terminal = Terminal(
            terminal_name=terminal_name,
            location=location
        )
        db.session.add(terminal)
        db.session.flush()   # so terminal.terminal_id is available

        # 2) Decide start & end terminal for the route
        main_id = current_app.config["MAIN_TERMINAL_ID"]

        # 3) Fallback default if user left estimated_time empty
        if est_time is None:
            est_time = 0   # or 15, or whatever you want as default

        # 4) Create route row
        route = Route(
            route_name=route_name,
            start_terminal_id=main_id,
            end_terminal_id=terminal.terminal_id,
            estimated_time_minutes=est_time
        )
        db.session.add(route)
        db.session.flush()
        
        create_audit_log(
            action="INSERT",
            table_name="terminals",
            record_id=terminal.terminal_id,
            description=f"Added terminal '{terminal.terminal_name}' at '{terminal.location}'."
        )
        create_audit_log(
            action="INSERT",
            table_name="routes",
            record_id=route.route_id,
            description=f"Added route '{route.route_name}' from MAIN({main_id}) to terminal {terminal.terminal_id}."
        )

        # 5) Save everything
        db.session.commit()

        flash("Terminal and route added to database", "success")
        return redirect(url_for("operator"))

    return render_template("terminal.html", form=form)


@app.route("/add/<model>", methods=["GET", "POST"])
def add_record(model):
    model = model.lower()
    ModelClass = MODEL_MAP[model]
    FormClass = FORM_MAP[model]

    form = FormClass()

    # important: set choices BEFORE validate_on_submit
    set_form_choices(form, model)

    if form.validate_on_submit():
        # special case for jeepneys because we also create TerminalJeepneys
        if model == "jeepneys":
            item = Jeepney(
                plate_number=form.plate_number.data,
                capacity=form.capacity.data,
                status="Available"
            )
            db.session.add(item)
            db.session.flush()  # get jeepney_id

            # also attach to selected terminal
            tj = TerminalJeepneys(
                terminal_id=form.terminal_id.data,
                jeepney_id=item.jeepney_id,
                arrival_time=datetime.utcnow(),
                status="Waiting",
                current_passengers=0
            )
            db.session.add(tj)
            db.session.flush()

            # 🔹 AUDIT LOG
            create_audit_log(
                action="INSERT",
                table_name="jeepneys",
                record_id=item.jeepney_id,
                description=f"Added jeepney {item.plate_number} with capacity {item.capacity}."
            )
            create_audit_log(
                action="INSERT",
                table_name="terminaljeeps",
                record_id=tj.terminal_jeep_id,
                description=f"Assigned jeepney {item.plate_number} to terminal_id={tj.terminal_id}."
            )

            db.session.commit()
            return redirect(url_for("view"))

        # TODO: if you add generic create for other models, you can also
        # call create_audit_log() there

    return render_template("add.html", form=form, model=model, action="add")

@app.route("/favorites/add", methods=["POST"])
def add_favorite():
    """
    Add a favorite terminal or route for the current user.
    Accepts form or JSON:
      - terminal_id (optional)
      - route_id (optional)
      - label (optional)
    At least one of terminal_id or route_id must be present.
    """
    user_id = session.get("user_id")

    # support both JSON and normal form without errors
    data = request.get_json(silent=True) or request.form

    terminal_id = data.get("terminal_id")
    route_id = data.get("route_id")
    label = (data.get("label") or "").strip()

    terminal_id = int(terminal_id) if terminal_id else None
    route_id = int(route_id) if route_id else None

    if not terminal_id and not route_id:
        return jsonify({"error": "terminal_id or route_id is required"}), 400

    # avoid duplicate favorites per user / terminal / route
    existing = Userfavorite.query.filter_by(
        user_id=user_id,
        terminal_id=terminal_id,
        route_id=route_id
    ).first()

    if existing:
        # if already exists, just update the label (optional)
        if label:
            existing.label = label
            db.session.commit()
        return jsonify({"message": "Already in favorites"}), 200

    fav = Userfavorite(
        user_id=user_id,
        terminal_id=terminal_id,
        route_id=route_id,
        label=label  # important: satisfies NOT NULL
    )
    db.session.add(fav)
    db.session.flush()
    
    create_audit_log(
        action="INSERT",
        table_name="userfavorites",
        record_id=fav.favorite_id,
        description=f"Added favorite (terminal_id={terminal_id}, route_id={route_id})."
    )

    db.session.commit()

    return jsonify({"message": "Added to favorites"}), 201

@app.route('/delete/<string:model>/<int:id>', methods=['POST'])
def delete_record(model, id):
    model_class = MODEL_MAP.get(model)
    if model_class is None:
        abort(404)

    obj = model_class.query.get_or_404(id)
    
    create_audit_log(
        action="DELETE",
        table_name=model,
        record_id=id,
        description=f"Deleted {model} record with id={id}."
    )

    db.session.delete(obj)
    db.session.commit()
    flash(f'{model.capitalize()} record deleted successfully', "success")
    return redirect(url_for('view'))

@app.route("/favorites/remove", methods=["POST"])
def remove_favorite():
    user_id = session.get("user_id")

    # ✅ Safely support both JSON & form
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form

    terminal_id = data.get("terminal_id")
    route_id = data.get("route_id")

    terminal_id = int(terminal_id) if terminal_id else None
    route_id = int(route_id) if route_id else None

    fav = Userfavorite.query.filter_by(
        user_id=user_id,
        terminal_id=terminal_id,
        route_id=route_id
    ).first()

    if not fav:
        if request.is_json:
            return jsonify({"error": "Favorite not found"}), 404
        flash("Favorite not found.", "danger")
        return redirect(url_for("favorites_page"))

    db.session.delete(fav)
    
    create_audit_log(
        action="DELETE",
        table_name="userfavorites",
        record_id=fav.favorite_id,
        description=f"Removed favorite (terminal_id={fav.terminal_id}, route_id={fav.route_id})."
    )
    
    db.session.commit()

    if request.is_json:
        return jsonify({"message": "Removed from favorites"}), 200

    flash("Removed from favorites.", "info")
    return redirect(url_for("favorites_page"))


@app.route('/edit/<string:model>/<int:id>', methods=['GET', 'POST'])
def update_record(model, id):
    model_class = MODEL_MAP.get(model)
    form_class = FORM_MAP.get(model)

    if model_class is None or form_class is None:
        abort(404)

    obj = model_class.query.get_or_404(id)

    # Bind form to object
    form = form_class(obj=obj)

    # ---------- FILL CHOICES FOR SELECT FIELDS ----------
    if model == "routes":
        terminals = Terminal.query.all()
        form.start_terminal_id.choices = [(t.terminal_id, t.terminal_name) for t in terminals]
        form.end_terminal_id.choices = [(t.terminal_id, t.terminal_name) for t in terminals]

    elif model == "trips":
        form.jeepney_id.choices = [(j.jeepney_id, j.plate_number) for j in Jeepney.query.all()]
        form.route_id.choices = [(r.route_id, r.route_name) for r in Route.query.all()]
        terminals = Terminal.query.all()
        form.origin_terminal_id.choices = [(t.terminal_id, t.terminal_name) for t in terminals]
        form.destination_terminal_id.choices = [(t.terminal_id, t.terminal_name) for t in terminals]

    elif model == "seats":
        form.trip_id.choices = [(t.trip_id, f"Trip {t.trip_id}") for t in Trip.query.all()]

    elif model == "terminaljeeps":
        form.terminal_id.choices = [(t.terminal_id, t.terminal_name) for t in Terminal.query.all()]
        form.jeepney_id.choices = [(j.jeepney_id, j.plate_number) for j in Jeepney.query.all()]

    elif model == "userfavorites":
        form.user_id.choices = [(u.user_id, f"{u.first_name} {u.last_name}") for u in User.query.all()]
        form.terminal_id.choices = [(t.terminal_id, t.terminal_name) for t in Terminal.query.all()]
        form.route_id.choices = [(r.route_id, r.route_name) for r in Route.query.all()]

    elif model == "notifications":
        form.user_id.choices = [(u.user_id, f"{u.first_name} {u.last_name}") for u in User.query.all()]
        form.trip_id.choices = [(t.trip_id, f"Trip {t.trip_id}") for t in Trip.query.all()]

    elif model == "auditlogs":
        form.user_id.choices = [(u.user_id, f"{u.first_name} {u.last_name}") for u in User.query.all()]
        
    elif model == "jeepneys":
        # IMPORTANT — Jeepney terminal dropdown
        form.terminal_id.choices = [(t.terminal_id, t.terminal_name) for t in Terminal.query.all()]


    # ---------- POST: Saving Changes ----------
    if form.validate_on_submit():

        # ---- SPECIAL CASE: USERS (password hashing & handling) ----
        if model == "users":
            obj.first_name = form.first_name.data
            obj.last_name = form.last_name.data
            obj.email = form.email.data
            obj.role = form.role.data
            obj.level = form.level.data
            obj.xp_points = form.xp_points.data

            # If password was entered, update the hash
            if form.password.data:
                obj.password_hash = generate_password_hash(form.password.data)

        else:
            # Normal case
            form.populate_obj(obj)
        
        pk_value = getattr(obj, f"{model[:-1]}_id", id)  # e.g. user_id, terminal_id
        create_audit_log(
            action="UPDATE",
            table_name=model,
            record_id=pk_value,
            description=f"Updated {model} record with id={pk_value}."
        )

        db.session.commit()
        flash(f"{model.capitalize()} updated successfully!", "success")
        return redirect(url_for('view'))

    return render_template("add.html", form=form, model=model, action="edit")

@app.route("/favorites/update/<int:favorite_id>", methods=["POST"])
@login_required
def update_favorite_label(favorite_id):
    """Update the label (note) of an existing favorite."""
    user_id = session.get("user_id")
    fav = Userfavorite.query.filter_by(
        favorite_id=favorite_id,
        user_id=user_id
    ).first_or_404()

    label = (request.form.get("label") or "").strip()
    fav.label = label  # ok even if empty string
    db.session.commit()

    flash("Favorite label updated.", "success")
    return redirect(url_for("favorites_page"))

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/favorites")
@login_required
def favorites_page():
    user_id = session.get("user_id")

    favs = (
        Userfavorite.query
        .filter_by(user_id=user_id)
        .order_by(Userfavorite.date_created.desc())
        .all()
    )

    return render_template("favorites.html", favorites=favs)

@app.route("/notifications-page")
def notifications_page():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view notifications.", "warning")
        return redirect(url_for("login"))

    # 🔹 KUNIN lahat ng favorite TERMINALS ng user
    fav_terminals = (
        Userfavorite.query
        .filter_by(user_id=user_id)
        .filter(Userfavorite.terminal_id.isnot(None))
        .all()
    )
    fav_terminal_ids = {f.terminal_id for f in fav_terminals}

    # Kung wala siyang favorite terminal, wala tayong ipapakitang notif
    if not fav_terminal_ids:
        notifications = []
        return render_template(
            "notifications.html",
            notifications=notifications,
            fav_terminal_ids=fav_terminal_ids
        )

    # 🔹 KUNIN notifications na:
    # - para sa current user, AT
    # - ang trip nila may origin o destination na pasok sa favorite terminals
    notifications = (
        db.session.query(Notification)
        .join(Trip, Notification.trip_id == Trip.trip_id)
        .filter(Notification.user_id == user_id)
        .filter(
            or_(
                Trip.origin_terminal_id.in_(fav_terminal_ids),
                Trip.destination_terminal_id.in_(fav_terminal_ids),
            )
        )
        .order_by(Notification.date_sent.desc())
        .all()
    )

    return render_template(
        "notifications.html",
        notifications=notifications,
        fav_terminal_ids=fav_terminal_ids
    )

@app.route("/auditlogs")   # only admin can view logs
def auditlogs_page():
    # Filters from query string
    user_id = request.args.get("user_id", type=int)
    table_name = request.args.get("table_name", type=str)
    action = request.args.get("action", type=str)
    date_from = request.args.get("date_from", type=str)
    date_to = request.args.get("date_to", type=str)

    q = Auditlog.query.join(User, Auditlog.user_id == User.user_id)

    if user_id:
        q = q.filter(Auditlog.user_id == user_id)
    if table_name:
        q = q.filter(Auditlog.table_name == table_name)
    if action:
        q = q.filter(Auditlog.action == action)
    if date_from:
        q = q.filter(Auditlog.timestamp >= date_from)
    if date_to:
        # include whole day
        q = q.filter(Auditlog.timestamp <= f"{date_to} 23:59:59")

    logs = q.order_by(Auditlog.timestamp.desc()).limit(300).all()

    users = User.query.order_by(User.first_name.asc()).all()
    table_names = [row[0] for row in db.session.query(Auditlog.table_name).distinct().all()]
    actions = ['INSERT', 'UPDATE', 'DELETE']

    return render_template(
        "auditlogs.html",
        logs=logs,
        users=users,
        table_names=table_names,
        actions=actions,
        filters={
            "user_id": user_id,
            "table_name": table_name,
            "action": action,
            "date_from": date_from,
            "date_to": date_to,
        }
    )

# ---------------- MAP + MAIN TERMINAL PAGES ----------------
#from flask import current_app

@app.route("/map")
def map_view():
    main_id = current_app.config.get("MAIN_TERMINAL_ID", MAIN_TERMINAL_ID)

    # all non-main terminals (same as before)
    terminals = (
        Terminal.query
        .filter(Terminal.terminal_id != main_id)
        .order_by(Terminal.terminal_id.asc())
        .limit(4)
        .all()
    )

    # 🔹 routes that start at MAIN and end at each terminal
    routes = (
        Route.query
        .filter_by(start_terminal_id=main_id)
        .all()
    )

    # terminal_id → {route_id, route_name}
    routes_by_term = {}
    for r in routes:
        routes_by_term[r.end_terminal_id] = {
            "route_id": r.route_id,
            "route_name": r.route_name
        }

    return render_template(
        "map.html",
        terminals=terminals,
        main_terminal_id=main_id,
        routes_by_term=routes_by_term,   # <-- new
    )

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
    
    notify_trip_event(trip, "Departure")
    if passengers >= capacity:
        notify_trip_event(trip, "FullCapacity")
        
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
    List the latest jeep currently traveling TO the MAIN TERMINAL
    (one per origin terminal).
    """

    main_id = current_app.config.get("MAIN_TERMINAL_ID", MAIN_TERMINAL_ID)

    # Get all live trips heading to MAIN
    trips = (
        Trip.query
        .filter_by(status="En Route", destination_terminal_id=main_id)
        .order_by(Trip.departure_time.desc())
        .all()
    )

    latest = {}
    for t in trips:
        if t.origin_terminal_id not in latest:
            latest[t.origin_terminal_id] = t  # first is the newest

    result = []

    for origin_id, trip in latest.items():
        jeep = Jeepney.query.get(trip.jeepney_id)
        term = Terminal.query.get(origin_id)
        seat = Seat.query.filter_by(trip_id=trip.trip_id).first()

        result.append({
            "jeepney_id": jeep.jeepney_id,
            "plate_number": jeep.plate_number,
            "terminal_id": term.terminal_id,
            "terminal_name": term.terminal_name,
            "capacity": jeep.capacity,
            "passengers": seat.occupied_seats if seat else 0
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

@app.route("/api/favorites", methods=["POST"])
def api_add_favorite():
    data = request.get_json() or {}

    user_id = session.get("user_id")    # or from JWT / whatever you use
    terminal_id = data.get("terminal_id")
    route_id = data.get("route_id")
    # optional custom label from frontend
    raw_label = data.get("label")

    # Fallback label if none provided
    if not raw_label:
        # you can customize this any way you like
        # e.g., include terminal or route info
        raw_label = f"Favorite route {route_id} @ terminal {terminal_id}"

    fav = Userfavorite(
        user_id=user_id,
        terminal_id=terminal_id,
        route_id=route_id,
        label=raw_label,          
    )

    db.session.add(fav)
    db.session.commit()

    return jsonify({
        "ok": True,
        "favorite_id": fav.favorite_id,
        "label": fav.label,
    }), 201


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

    notify_trip_event(trip, "Departure")

    # Optional: Full capacity notification (if you want full-cap alerts here)
    if passengers >= cap:
        notify_trip_event(trip, "FullCapacity")
        
    create_audit_log(
        action="INSERT",
        table_name="trips",
        record_id=trip.trip_id,
        description=f"Jeep {jeepney_id} departed from terminal {origin_id} to MAIN({destination_id}) with {passengers} passengers."
    )

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
        notify_trip_event(trip, "Arrival")

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

# ---------------- API: SEARCH ROUTES ----------------
@app.route("/api/search/routes")
def api_search_routes():
    q = request.args.get("q", "", type=str).strip()
    if not q:
        return jsonify([])
    routes = (
        Route.query
        .filter(Route.route_name.ilike(f"%{q}%"))
        .all()
    )
    return jsonify([
        {
            "route_id": r.route_id,
            "route_name": r.route_name,
            "start_terminal": r.start_terminal.terminal_name,
            "end_terminal": r.end_terminal.terminal_name,
        }
        for r in routes
    ])

# ---------------- API: FILTER TERMINALS BY LOCATION ----------------
@app.route("/api/terminals/filter")
def api_filter_terminals():
    loc = request.args.get("location", "", type=str).strip()
    if not loc:
        return jsonify([])
    terminals = (
        Terminal.query
        .filter(Terminal.location.ilike(f"%{loc}%"))
        .all()
    )
    return jsonify([
        {
            "terminal_id": t.terminal_id,
            "terminal_name": t.terminal_name,
            "location": t.location,
            "is_main": t.is_main,
        }
        for t in terminals
    ])


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

