
@app.route("/favorites")
@login_required
def favorites_page():
    return render_template("favorites.html")