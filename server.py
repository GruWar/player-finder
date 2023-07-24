from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, current_user, login_required, logout_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# variable init
app = Flask(__name__)
app.config['SECRET_KEY'] = 'h5ds2864t61fb46h4r61gb13n5'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///PlayerFinder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CREATE TABLE IN DB
# UserMixin,
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))


# with app.app_context():
#     db.create_all()


# routing
@app.route("/")
def home():
    return render_template("index.html", logged_in=current_user.is_authenticated)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("contributions"))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hash_and_salted_password = generate_password_hash(
            request.form.get("password"),
            method="pbkdf2",
            salt_length=8,
        )

        new_user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=hash_and_salted_password,
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("contributions"))
    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route("/home")
@login_required
def contributions():
    return render_template("home.html", logged_in=current_user.is_authenticated)


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# run app
if __name__ == "__main__":
    app.run(debug=True)
