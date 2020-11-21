from flask import Flask, render_template

app = Flask(__name__, static_url_path="")


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET"])
def register():
    return render_template("registration.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)