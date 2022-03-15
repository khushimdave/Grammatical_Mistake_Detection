from flask import Flask

app = Flask(_name_)

@app.route("/")
def home_view():
		return "<h1>Welcome to Geeks for Geeks</h1>"
