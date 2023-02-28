from flask import (Flask, render_template, redirect, url_for, request)
from flask_mysqldb import MySQL

app = Flask(__name__)

# Credentials to connect with mySQL DB of CDT UPAT
app.config['MYSQL_HOST'] = 'eu15.tmd.cloud'
app.config['MYSQL_USER'] = 'consume5_twinERGY'
app.config['MYSQL_PASSWORD'] = 'w*}S2x1pKMM='
app.config['MYSQL_DB'] = 'consume5_twinERGY'

mysql = MySQL(app)


@app.route("/")
@app.route("/index/")
def rout():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5002)