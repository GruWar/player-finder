from flask import Flask, render_template

# variable init
app = Flask(__name__)


# routing
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


# run app
if __name__ == "__main__":
    app.run(debug=True)
