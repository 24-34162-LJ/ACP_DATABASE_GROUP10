from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, AddTerminal
from models import db, User, Terminal

app = Flask(__name__) # to connect the app.py to the models.py

app.config['SECRET_KEY'] = 'lj123' # for security purposes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jeep.db' # this create a database /save the data
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # this to remove unessary tracking

app.config['WTF_CSRF_ENABLED'] = False
db.init_app(app)


@app.route('/home')
def home():
  return render_template("index.html")

@app.route('/view')
def view():
    users = User.query.all()
    terminals = Terminal.query.all()
    return render_template("view_database.html", users=users, terminals=terminals)

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
      # get the sudmit data in the form
        first_name = form.first_name.data
        last_name  = form.last_name.data
        role       = form.role.data
        email      = form.email.data
        password   = form.password.data

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
            role=role,  # must be 'player' or 'operator'
        )

        db.session.add(user)  # temporary store
        db.session.commit() # add note: always use commit if not it will not save

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

@app.route("/commuter")
def commuter():
  return render_template("commuter.html")

@app.route("/operator")
def operator():
  return render_template("operator.html")


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


@app.route("/admin")
def admin():
  return render_template("admin.html")

@app.route("/seat")
def seat():
    return render_template("seat.html")

if __name__ == "__main__":
    with app.app_context():
        #db.drop_all()
        db.create_all()

        if not Terminal.query.first():
            t1 = Terminal(
                terminal_name="SM Lipa Terminal",
                location="SM Lipa, Batangas"
            )
            t2 = Terminal(
                terminal_name="Robinsons Lipa Terminal",
                location="Robinsons Lipa, Batangas"
            )
            db.session.add_all([t1, t2])
            db.session.commit()
            print("Sample terminals added.")

        if not User.query.filter_by(email='admin@gmail.com').first():
            admin = User(
                first_name='Admin',
                last_name='User',
                email='admin@gmail.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'  # or 'player'
            )
            viewer = User(
                first_name='Viewer',
                last_name='User',
                email='viewer@gmail.com',
                password_hash=generate_password_hash('viewer123'),
                role='viewer'  # since 'viewer' is not in Enum
            )
            db.session.add_all([admin, viewer])
            db.session.commit()

    app.run(debug=True)

