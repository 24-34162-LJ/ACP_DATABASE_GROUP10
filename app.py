from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm
from models import db, User


app = Flask(__name__) # to connect the app.py to the models.py

app.config['SECRET_KEY'] = 'lj123' # for security purposes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db' # this create a database /save the data
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # this to remove unessary tracking

app.config['WTF_CSRF_ENABLED'] = False
db.init_app(app)

@app.route('/home')
def home():
  return render_template("index.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
  form = LoginForm()
  return render_template("login.html", form=form)



@app.route('/sign', methods=['GET', 'POST'])
def sign():
    form = RegisterForm()

    if request.method == 'POST':
        # DEBUG: print what was sent and what errors WTForms sees
        print("FORM DATA:", form.data)
        print("FORM ERRORS:", form.errors)

    if form.validate_on_submit():
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

        user = User(
            first_name=first_name,
            last_name=last_name,
            user_role=role,
            user_email=email,
            user_password=hashed_pw
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! You may now log in.", "success")
        return redirect(url_for("login"))

    return render_template("sign.html", form=form)

@app.route("/")
def index():
  return redirect(url_for("home"))

if __name__ == "__main__":
  # this create first all the table in out database it is a content manager
  with app.app_context():
    db.create_all()

  app.run(debug=True)
