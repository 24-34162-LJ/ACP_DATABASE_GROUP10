from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm
from models import db, User, Terminals

app = Flask(__name__) # to connect the app.py to the models.py

app.config['SECRET_KEY'] = 'lj123' # for security purposes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db' # this create a database /save the data
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # this to remove unessary tracking

app.config['WTF_CSRF_ENABLED'] = False
db.init_app(app)


@app.route('/home')
def home():
  return render_template("index.html")

@app.route('/view')
def view():
    users = User.query.all()
    terminals = Terminals.query.all()
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

        user = User.query.filter_by(user_email=email).first()

        if user and check_password_hash(user.user_password, password):

            session['user_id'] = user.user_id
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name
            session['role'] = user.user_role

            flash('Login successful!', 'success')

            # Redirect based on role
            if session['role'] == 'Commuter':
                return redirect(url_for("commuter"))
            elif session['role'] == 'Vehicle Operator':
                return redirect(url_for("operator"))
            elif session['role'] == 'Admin':
                return redirect(url_for('admin'))

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

        existing_email = User.query.filter_by(user_email=email).first()
        if existing_email:
            flash("Email already registered. Try another.", "danger")
            return redirect(url_for("sign"))

        hashed_pw = generate_password_hash(password)

        # inilization
        user = User(
            first_name=first_name,
            last_name=last_name,
            user_role=role,
            user_email=email,
            user_password=hashed_pw
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

        if not Terminals.query.first():
            t1 = Terminals(
                terminal_name="SM Lipa Terminal",
                location="SM Lipa, Batangas"
            )
            t2 = Terminals(
                terminal_name="Robinsons Lipa Terminal",
                location="Robinsons Lipa, Batangas"
            )
            db.session.add_all([t1, t2])
            db.session.commit()
            print("Sample terminals added.")
    app.run(debug=True)

