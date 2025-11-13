from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

@app.route('/home')
def home():
  return "hello"

@app.route("/")
def index():
  return redirect(url_for("home"))

if __name__ == "__main__":
  app.run(debug=True)