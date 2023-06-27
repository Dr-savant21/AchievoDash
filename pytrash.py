from flask import Flask, render_template, redirect, url_for, request;
import mysql.connector;
import re

app = Flask (__name__, template_folder="templates", static_folder="staticFolder") 

connect = mysql.connector.connect(host='localhost',user='israel',password='alxportfolioproject',database='alxportfolioproject')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    errors = {}
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password'] 
        if not email.strip():
            errors['email'] = ["Email address field can't be empty"]
        else:
            email = request.form['email']
        if not password.strip():
            errors['password'] = ["password field can't be empty"]
        if 'email' not in errors and 'password' not in errors:
            cur = connect.cursor()
            cur.execute("SELECT * FROM user WHERE email = %s AND password = %s", (email, password))
            user_info = cur.fetchone()  # Fetch a single row from the query result
            connect.commit()
            if user_info:
                return redirect(url_for('dashboard'))
            else:
                errors['email'] = ["Invalid email or password"]
    return render_template("login.html", errors=errors)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    errors = {}
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cpassword = request.form['confirm_password']
        if not username.strip():
            errors['username'] = ["Username field can't be empty"]
        elif not is_valid_username(username):
            errors['username'] = ["Invalid username"]
        else:
            name = request.form['username']
        if not email.strip():
            errors['email'] = ["Email address field can't be empty"]
        elif not is_valid_email(email):
            errors['email'] = ["Invalid email address"]
        else:
            email = request.form['email']
        if not password.strip():
            errors['password'] = ["password field can't be empty"]
        elif not is_valid_password(password):
            errors['password'] = ["password must be more than characters long and must contain atleast one uppercase letter, one lowercase letter, one number and one special character"]
        else:
            password = request.form['password']
        if not cpassword.strip():
            errors['cpassword'] = ["confirm password field can't be empty"]
        else:
            if cpassword != password:
                errors['cpassword'] = errors['password'] = ['passwords do not match']
            else:
                if 'username' in errors or 'email' in errors or 'password' in errors or 'cpassword' in errors:
                    errors['username'] = ['errors in form']
                else:
                    cur = connect.cursor()
                    cur.execute('INSERT INTO user (username, email, password) VALUES(%s, %s, %s)', (name, email, password))
                    connect.commit()
                    return redirect(url_for("login"))
    return render_template("signup.html", errors=errors)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    return redirect(url_for('login'))

email_pattern = r'^[\w.-]+@[a-zA-Z_-]+?\.[a-zA-Z]{2,3}$'

def is_valid_email(email):
    return re.match(email_pattern, email) is not None

username_pattern = r'^[a-zA-Z0-9!@#$%^&*()_+=\-{}\[\]:";\'<>?,./|`~]*$'

def is_valid_username(username):
    return re.match(username_pattern, username) is not None

password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

def is_valid_password(password):
    return re.match(password_pattern, password) is not None

# @app.route()

    
if __name__ == "__main__":
    app.run(debug=True)
