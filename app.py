from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lj123' # for security purposes

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
  app.run(debug=True)
  
  
  """
  
  for post and get use this for login
  @app.route('/login', methods=['POST', 'GET'])
  
  from flask import request
  - to know if we get get or post = request
  
  """
  
  """
  app = responsible for routing 
  
  """