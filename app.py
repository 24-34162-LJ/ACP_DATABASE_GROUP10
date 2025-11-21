from flask import Flask, render_template, redirect, url_for, request
from models import db

app = Flask(__name__) # to connect the app.py to the models.py

app.config['SECRET_KEY'] = 'lj123' # for security purposes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db' # this create a database /save the data
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # this to remove unessary tracking

db.init_app(app)

@app.route('/home')
def home():
  return render_template("index.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
    return render_template("login.html")
  
@app.route('/sign', methods=['POST', 'GET'])
def sigin():
  return render_template("sign.html")
    
@app.route("/")
def index():
  return redirect(url_for("home"))

if __name__ == "__main__":
  # this create first all the table in out database it is a content manager
  with app.app_context():
    db.create_all()

  app.run(debug=True)
  
