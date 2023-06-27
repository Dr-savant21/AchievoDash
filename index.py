from flask import Flask, render_template, redirect, url_for, request, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import re
import mysql.connector
# from flask_login import current_user
from flask_login import login_user
from flask_login import current_user, LoginManager, UserMixin, login_required, logout_user
from datetime import datetime, timedelta  # Import the datetime class and timedelta
from flask import jsonify
from flask import request
from io import BytesIO
import os
import mimetypes
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates", static_folder="staticFolder")
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://israel:alxportfolioproject@localhost/alxportfolioproject'
app.secret_key = 'Izzywindz21@.'
db = SQLAlchemy(app)

connect = mysql.connector.connect(host='localhost', user='israel', password='alxportfolioproject', database='alxportfolioproject')

login_manager = LoginManager()
login_manager.init_app(app)

# Define the UserLoader callback function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"User(username='{self.username}', email='{self.email}')"
    
# Define a custom Jinja2 filter to truncate the description
def truncate_description(description, length):
    if description is None:
        return ''
    words = description.split()
    if len(words) <= length:
        return description
    truncated_words = words[:length]
    return ' '.join(truncated_words) + '...'

# Register the custom filter with the Flask app
app.jinja_env.filters['truncate_description'] = truncate_description

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
        if not password.strip():
            errors['password'] = ["password field can't be empty"]
        if 'email' not in errors and 'password' not in errors:
            user = User.query.filter_by(email=email, password=password).first()
            if user:
                login_user(user)
                session['user_id'] = user.id
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
        if not email.strip():
            errors['email'] = ["Email address field can't be empty"]
        elif not is_valid_email(email):
            errors['email'] = ["Invalid email address"]
        if not password.strip():
            errors['password'] = ["password field can't be empty"]
        elif not is_valid_password(password):
            errors['password'] = ["password must be more than characters long and must contain at least one uppercase letter, one lowercase letter, one number, and one special character"]
        if not cpassword.strip():
            errors['cpassword'] = ["confirm password field can't be empty"]
        elif cpassword != password:
            errors['cpassword'] = errors['password'] = ['passwords do not match']

        if not errors:
            user = User(username=username, email=email, password=password)
            try:
                db.session.add(user)
                db.session.commit()
                return redirect(url_for("login"))
            except IntegrityError:
                db.session.rollback()
                errors['email'] = ["Email address already exists"]

    return render_template("signup.html", errors=errors)

@app.route("/dashboard")
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    # Retrieve the list of the last three projects for the logged-in user
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.id.desc()).limit(3).all()
    # Retrieve the list of the last two goals for the logged-in user
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.id.desc()).limit(2).all()
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    username = current_user.username  # Fetch the username
    # Get the total number of tasks
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()

    # Fetch the last three tasks for each status
    completed_task_list = Task.query.filter_by(user_id=current_user.id, taskstatus='completed').order_by(Task.created_at.desc()).limit(3).all()
    ongoing_task_list = Task.query.filter_by(user_id=current_user.id, taskstatus='ongoing').order_by(Task.created_at.desc()).limit(3).all()
    onhold_task_list = Task.query.filter_by(user_id=current_user.id, taskstatus='on-hold').order_by(Task.created_at.desc()).limit(3).all()
    pending_task_list = Task.query.filter_by(user_id=current_user.id, taskstatus='pending').order_by(Task.created_at.desc()).limit(3).all()
    review_task_list = Task.query.filter_by(user_id=current_user.id, taskstatus='review').order_by(Task.created_at.desc()).limit(3).all()

        # Calculate the progress for each project
    project_data = []
    for project in projects:
        tasks = Task.query.filter_by(project_id=project.id).all()
        # Calculate other project information
        total_tasks = Task.query.filter_by(project_id=project.id).count()
        # Calculate the number of completed tasks
        complete_tasks = sum(1 for task in tasks if task.taskstatus == 'completed')
        progress_percentage = (complete_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        project_info = {
            'project': project,
            'progress_percentage': progress_percentage,
            'completed_tasks': complete_tasks,
            'total_tasks': total_tasks
        }
        project_data.append(project_info)

    return render_template("dashboard.html", 
                           projects=projects, 
                           username=username, 
                           goals=goals, 
                           total_tasks=total_tasks, 
                           completed_tasks=completed_task_list, 
                           ongoing_tasks=ongoing_task_list, 
                           onhold_tasks=onhold_task_list, 
                           pending_tasks=pending_task_list, 
                           review_tasks=review_task_list, 
                           project_data=project_data,
                           tasks=tasks
                           )


@app.route("/logout")
@login_required
def logout():
    logout_user()
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

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    priority = db.Column(db.String(10))
    file_data = db.Column(db.LargeBinary)
    creator_username=db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define a relationship with the User table
    user = db.relationship('User', backref=db.backref('projects', lazy=True))

    def __init__(self, title, description, priority, start_date, end_date, file_data, user_id, creator_username):
        self.title = title
        self.description = description
        self.priority = priority
        self.start_date = start_date
        self.end_date = end_date
        self.file_data = file_data
        self.user_id = user_id
        self.creator_username = creator_username

@app.route('/add_project', methods=['POST'])
@login_required
def add_project():
    # Retrieve form data
    title = request.form.get('projectTitle')
    description = request.form.get('message-text')
    start_date_str = request.form.get('projectStart')
    end_date_str = request.form.get('projectEnd')
    
    file = request.files.get('files')  # Retrieve the uploaded file

     # Initialize file_data with a default value
    file_data = None

    # Save the file to the desired location
    if file:
        file_data = file.read()  # Read the file data

    # Convert the datetime strings to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')

    # Store the creator_username
    creator_username = current_user.username

    # Create a new project object
    project = Project(title=title, 
                      description=description, 
                      start_date=start_date, 
                      end_date=end_date,              
                      user_id=current_user.id,  # Set the user ID
                      priority=request.form.get('projectPriority'),
                      file_data=file_data,
                      creator_username=creator_username
                    )
    
    # Add the project to the database
    db.session.add(project)
    db.session.commit()


    # Redirect to the referring page
    return redirect(request.referrer or url_for('projectdetails'))

@app.route("/projects")
def projects():

    # Retrieve the list of projects for the logged-in user
    user_projects = Project.query.filter_by(user_id=current_user.id).all()

     # Calculate the time difference for each project
    for project in user_projects:
        if project.end_date is not None:
            duration = project.end_date - datetime.now()
            days = duration.days
            hours = duration.seconds // 3600
            minutes = (duration.seconds // 60) % 60
            seconds = duration.seconds % 60

            if days > 0:
                project.time_remaining = f"{days} day{'s' if days > 1 else ''}"
            elif hours > 0:
                project.time_remaining = f"{hours} hour{'s' if hours > 1 else ''}"
            elif minutes > 0:
                project.time_remaining = f"{minutes} minute{'s' if minutes > 1 else ''}"
            else:
                project.time_remaining = f"{seconds} second{'s' if seconds > 1 else ''}"

    # Calculate the progress for each project
    project_data = []
    for project in user_projects:
        tasks = Task.query.filter_by(project_id=project.id).all()
        # Calculate other project information
        total_tasks = Task.query.filter_by(project_id=project.id).count()
        # Calculate the number of completed tasks
        completed_tasks = sum(1 for task in tasks if task.taskstatus == 'completed')
        progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        project_info = {
            'project': project,
            'progress_percentage': progress_percentage,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks
        }
        project_data.append(project_info)


    return render_template("projects.html", projects=user_projects, project_data=project_data)

@app.route("/task")
def task():
    # Retrieve the list of task for the logged-in user
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    # Retrieve the list of project for the logged-in user
    projects = Project.query.filter_by(user_id=current_user.id).all()

    return render_template("projectTask.html", tasks=user_tasks, projects=projects)

@app.route("/calendar")
def calendar():
    return render_template("projectCalendar.html")

@app.route("/team")
def team():
    return render_template("teamMembers.html")

@app.route("/profile")
def profile():
    if current_user.is_authenticated:
        # Retrieve the list of projects for the logged-in user
        userprofiles = Userprofile.query.filter_by(user_id=current_user.id).first()
        if userprofiles:
            user_email = current_user.email
            user_created_at =current_user.created_at
            return render_template("profile.html", userprofile=userprofiles, user_email=user_email, user_created_at=user_created_at)
        userprofile = Userprofile( 
            firstname=None, 
            description=None, 
            lastname=None, 
            job=None, 
            address=None, 
            file_data=None, 
            user_id=current_user.id, 
            phonenumber=None, 
            gender=None, 
            country=None, 
            state=None, 
            city=None, 
            maritalstatus=None, 
            religion=None, 
            emergencyprimaryname=None, 
            emergencyprimaryrelationship=None, 
            emergencyprimaryemail=None, 
            emergencyprimarynumber=None, 
            emergencyprimarynationality=None, 
            emergencyprimaryreligion=None, 
            emergencysecondaryname=None, 
            emergencysecondaryrelationship=None, 
            emergencysecondaryemail=None, 
            emergencysecondarynumber=None, 
            emergencysecondarynationality=None, 
            emergencysecondaryreligion=None
        )

        db.session.add(userprofile)
        db.session.commit()
        
        return render_template("profile.html", userprofile=userprofiles)
    
    user_email = current_user.email
    user_created_at =current_user.created_at

    return render_template("profile.html", userprofile=userprofiles, user_email=user_email, user_created_at=user_created_at)

@app.route("/goal")
def goal():
    # Retrieve the list of goals for the logged-in user
    user_goals = Goal.query.filter_by(user_id=current_user.id).all()

    return render_template("goal.html", goals=user_goals)

@app.route("/teamdetail")
def teamdetails():
    return render_template("teamdetails.html")

@app.route("/task/<int:task_id>")
def taskdetails(task_id):
    task = Task.query.get_or_404(task_id)
    created_at = task.created_at
    file_items = FileItem.query.all()  # Retrieve the list of file items from the database

    # Calculate the time difference for the project
    if task.end_date is not None:
        duration = task.end_date - datetime.now()
        days = duration.days
        hours = duration.seconds // 3600
        minutes = (duration.seconds // 60) % 60
        seconds = duration.seconds % 60

        if days > 0:
            time_remaining = f"{days} day{'s' if days > 1 else ''}"
        elif hours > 0:
            time_remaining = f"{hours} hour{'s' if hours > 1 else ''}"
        elif minutes > 0:
            time_remaining = f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            time_remaining = f"{seconds} second{'s' if seconds > 1 else ''}"

        username = current_user.username

        return render_template("taskdetails.html", task=task, time_remaining=time_remaining, created_at=created_at, file_items=file_items)
    
    return render_template("taskdetails.html", task=task, created_at=created_at, file_items=file_items)

@app.route("/project/<int:project_id>")
def projectdetails(project_id):
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id).all()
    created_at = project.created_at
    projectfile_items = ProjectFileItem.query.filter_by(project_id=project_id).all()  # Retrieve the list of file items from the database

    # Get the total number of tasks
    total_tasks = Task.query.filter_by(project_id=project_id).count()

    # Calculate the number of completed tasks
    completed_tasks = sum(1 for task in tasks if task.taskstatus == 'completed')
    
    # Calculate the progress percentage
    total_tasks = len(tasks)
    progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    # Calculate the time difference for the project
    if project.end_date is not None:
        duration = project.end_date - datetime.now()
        days = duration.days
        hours = duration.seconds // 3600
        minutes = (duration.seconds // 60) % 60
        seconds = duration.seconds % 60

        if days > 0:
            time_remaining = f"{days} day{'s' if days > 1 else ''}"
        elif hours > 0:
            time_remaining = f"{hours} hour{'s' if hours > 1 else ''}"
        elif minutes > 0:
            time_remaining = f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            time_remaining = f"{seconds} second{'s' if seconds > 1 else ''}"

        return render_template("projectdetails.html", project=project, time_remaining=time_remaining, tasks=tasks, created_at=created_at, projectfile_items=projectfile_items, progress_percentage=progress_percentage, total_tasks=total_tasks, completed_tasks=completed_tasks)
    
    return render_template("projectdetails.html", project=project, tasks=tasks, created_at=created_at, projectfile_items=projectfile_items, progress_percentage=progress_percentage, total_tasks=total_tasks, completed_tasks=completed_tasks)

@app.route("/edit_project/<int:project_id>", methods=["GET", "POST"])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if not project:
        # Handle project not found
        flash("Project not found", "error")
        return redirect(url_for("projects"))

    if request.method == "POST":
        # Retrieve the form data
        title = request.form.get("projectTitle")
        description = request.form.get("message-text")
        priority=request.form.get('projectPriority')
        start_date = datetime.strptime(request.form.get("projectStart"), "%Y-%m-%dT%H:%M")
        end_date = datetime.strptime(request.form.get("projectEnd"), "%Y-%m-%dT%H:%M")
        # Update the project details
        project.title = title
        project.description = description
        project.start_date = start_date
        project.end_date = end_date
        project.priority= priority
        # Update other project attributes as needed

        db.session.commit()
        # Handle successful project update
        flash("Project updated successfully", "success")
        return redirect(url_for("projects"))

    return render_template("projects.html", project=project)

@app.route("/delete_project/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    # Retrieve the project with the given project_id from the database
    project = Project.query.get(project_id)
    if not project:
        # Handle project not found
        flash("Project not found", "error")
        return redirect(url_for("projects"))

    # Delete the project from the database
    db.session.delete(project)
    db.session.commit()

    # Handle successful deletion
    flash("Project deleted successfully", "success")
    return redirect(url_for("projects"))

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    target_achievement = db.Column(db.String(100))
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define a relationship with the User table
    user = db.relationship('User', backref=db.backref('goals', lazy=True))

    def __init__(self, subject, description, target_achievement, start_date, end_date, status, user_id):
        self.subject = subject
        self.description = description
        self.target_achievement = target_achievement
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.user_id = user_id

@app.route('/add_goal', methods=['POST'])
@login_required
def add_goal():
    # Retrieve form data
    subject = request.form.get('goalSubject')
    target_achievement = request.form.get('target')
    description = request.form.get('message-text')
    start_date_str = request.form.get('goalStart')
    end_date_str = request.form.get('goalEnd')
    status = request.form.get('goalstatus')

    # Convert the datetime strings to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')

    # Create a new goal object
    goal = Goal(subject=subject, 
                      description=description, 
                      start_date=start_date, 
                      end_date=end_date,
                      user_id=current_user.id,  # Set the user ID
                      target_achievement=target_achievement,
                      status=status
                    )
    
    # Add the goal to the database
    db.session.add(goal)
    db.session.commit()

    # Redirect to the referring page
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/edit_goal/<int:goal_id>', methods=['GET','POST'])
@login_required
def edit_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if not goal:
        # Handle goal not found
        flash("Goal not found", "error")
        return redirect(url_for("goal"))

    if request.method == "POST":
    # Retrieve form data
        subject = request.form.get('goalSubject')
        target_achievement = request.form.get('target')
        description = request.form.get('message-text')
        status = request.form.get('goalstatus')
        start_date = datetime.strptime(request.form.get("goalStart"), "%Y-%m-%dT%H:%M")
        end_date = datetime.strptime(request.form.get("goalEnd"), "%Y-%m-%dT%H:%M")

        goal.subject = subject
        goal.description = description
        goal.start_date = start_date
        goal.end_date = end_date
        goal.status= status
        goal.target_achievement= target_achievement

        db.session.commit()
        # Handle successful goal update
        flash("Goal updated successfully", "success")
        return redirect(url_for("goal"))

    return render_template("projects.html", goal=goal)

@app.route("/delete_goal/<int:goal_id>", methods=["POST"])
def delete_goal(goal_id):
    # Retrieve the goal with the given goal_id from the database
    goal = Goal.query.get(goal_id)
    if not goal:
        # Handle goal not found
        flash("Goal not found", "error")
        return redirect(url_for("goal"))

    # Delete the goal from the database
    db.session.delete(goal)
    db.session.commit()

    # Handle successful deletion
    flash("Goal deleted successfully", "success")
    return redirect(url_for("goal"))

@app.route("/total_projects")
@login_required
def total_projects():
    user_id = current_user.id
    total_projects = Project.query.filter_by(user_id=user_id).count()
    return jsonify({"total_projects": total_projects})

@app.route("/edit_project_id/<int:project_id>", methods=["GET", "POST"])
@login_required
def edit_project_id(project_id):
    project = Project.query.get_or_404(project_id)
    if not project:
        # Handle project not found
        flash("Project not found", "error")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('projects'))

    if request.method == "POST":
        # Retrieve the form data
        title = request.form.get("projectTitle")
        description = request.form.get("message-text")

        project.title = title
        project.description = description

        db.session.commit()
        # Handle successful project update
        flash("Project updated successfully", "success")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('projects'))

    return render_template("projectdetails.html", project=project)

@app.route("/edit_project_details/<int:project_id>", methods=["GET", "POST"])
@login_required
def edit_project_details(project_id):
    project = Project.query.get_or_404(project_id)
    if not project:
        # Handle project not found
        flash("Project not found", "error")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('projects'))

    if request.method == "POST":
        # Retrieve the form data
        priority=request.form.get('projectPriority')
        start_date = datetime.strptime(request.form.get("projectStart"), "%Y-%m-%dT%H:%M")
        end_date = datetime.strptime(request.form.get("projectEnd"), "%Y-%m-%dT%H:%M")
        
        project.start_date = start_date
        project.end_date = end_date
        project.priority= priority

        db.session.commit()
        # Handle successful project update
        flash("Project updated successfully", "success")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('projects'))

    return render_template("projectdetails.html", project=project)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    # Define a relationship with the project table
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))
    task_title = db.Column(db.String(255))
    project_title = db.Column(db.String(50))
    description = db.Column(db.Text)
    task_priority = db.Column(db.String(50))
    taskstatus = db.Column(db.String(20))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator_username = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define a relationship with the User table
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

    def __init__(self, project_id, description, task_title, start_date, end_date, task_priority, user_id, project_title, taskstatus, creator_username):
        self.project_id = project_id
        self.description = description
        self.task_title = task_title
        self.start_date = start_date
        self.end_date = end_date
        self.task_priority = task_priority
        self.user_id = user_id
        self.project_title=project_title
        self.taskstatus=taskstatus
        self.creator_username=creator_username

@app.route('/create_task', methods=['POST'])
@login_required
def create_task():
    # Retrieve form data
    project_id = int(request.form['projectTitle'])
    project = Project.query.get(project_id)
    project_title = project.title if project else None
    task_title = request.form['target']
    description = request.form['message-text']
    start_date_str = request.form['taskStart']
    end_date_str = request.form['taskEnd']
    task_priority = request.form['taskpriority']
    taskstatus = request.form['taskstatus']

    # Convert the datetime strings to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')

    creator_username = current_user.username

    task = Task(
        project_id=project_id,
        task_title=task_title,
        description=description,
        task_priority=task_priority,
        start_date=start_date, 
        end_date=end_date,
        user_id=current_user.id,  # Set the user ID
        project_title=project_title, 
        taskstatus=taskstatus,
        creator_username=creator_username
    ) 
    db.session.add(task)
    db.session.commit()

    # Redirect to the referring page
    return redirect(request.referrer or url_for('taskdetails'))

@app.route("/edittaskt_id/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task_id(task_id):
    task = Task.query.get_or_404(task_id)
    if not task:
        # Handle project not found
        flash("Task not found", "error")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('task'))

    if request.method == "POST":
        # Retrieve the form data
        title = request.form.get("target")
        description = request.form.get("message-text")

        task.title = title
        task.description = description

        db.session.commit()
        # Handle successful project update
        flash("Task updated successfully", "success")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('task'))

    return render_template("taskdetails.html", task=task)

@app.route("/edit_task_details/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task_details(task_id):
    task = Task.query.get_or_404(task_id)
    if not task:
        # Handle project not found
        flash("Task not found", "error")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('task'))
    if request.method == "POST": 
        # Retrieve the form data
        priority=request.form.get('taskPriority')
        status=request.form.get('taskstatus')
        start_date = datetime.strptime(request.form.get("taskStart"), "%Y-%m-%dT%H:%M")
        end_date = datetime.strptime(request.form.get("taskEnd"), "%Y-%m-%dT%H:%M")
        project_id = int(request.form['projectTitle'])
        project = Project.query.get(project_id)
        project_title = project.title if project else None
        
        task.start_date = start_date
        task.end_date = end_date
        task.priority= priority
        task.taskstatus= status
        task.project_id= project_id
        task.project_title= project_title

        db.session.commit()
        # Handle successful project update
        flash("Task updated successfully", "success")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('task'))

    # projects = Project.query.all, projects=projects()
    return render_template("taskdetails.html", task=task)

@app.route("/delete_task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    # Retrieve the task with the given task_id from the database
    task = Task.query.get(task_id)
    if not task:
        # Handle task not found
        flash("Task not found", "error")
        return redirect(url_for("task"))

    # Delete the task from the database
    db.session.delete(task)
    db.session.commit()

    # Handle successful deletion
    flash("Task deleted successfully", "success")
    return redirect(url_for("task"))

class Userprofile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=True)
    lastname = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    file_data = db.Column(db.LargeBinary, nullable=True)
    address=db.Column(db.String(50), nullable=True)
    phonenumber=db.Column(db.Integer, nullable=True)
    gender=db.Column(db.String(50), nullable=True)
    country=db.Column(db.String(50), nullable=True)
    state=db.Column(db.String(50), nullable=True)
    city=db.Column(db.String(50), nullable=True)
    maritalstatus=db.Column(db.String(50), nullable=True)
    religion=db.Column(db.String(50), nullable=True)
    emergencyprimaryname=db.Column(db.String(50), nullable=True)
    emergencyprimaryrelationship =db.Column(db.String(50), nullable=True)
    emergencyprimaryemail=db.Column(db.String(100), nullable=True)
    emergencyprimarynumber=db.Column(db.Integer, nullable=True)
    emergencyprimarynationality=db.Column(db.String(50), nullable=True)
    emergencyprimaryreligion=db.Column(db.String(50), nullable=True)
    emergencysecondaryname=db.Column(db.String(50), nullable=True)
    emergencysecondaryrelationship=db.Column(db.String(50), nullable=True)
    emergencysecondaryemail=db.Column(db.String(50), nullable=True)
    emergencysecondarynumber=db.Column(db.Integer, nullable=True)
    emergencysecondarynationality=db.Column(db.String(50), nullable=True)
    emergencysecondaryreligion=db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define a relationship with the User table
    user = db.relationship('User', backref=db.backref('userprofile', lazy=True))

    def __init__(self, firstname, description, lastname, job, address, file_data, user_id, phonenumber, gender, country, state, city, maritalstatus, religion, emergencyprimaryname, emergencyprimaryrelationship, emergencyprimaryemail, emergencyprimarynumber, emergencyprimarynationality, emergencyprimaryreligion, emergencysecondaryname, emergencysecondaryrelationship, emergencysecondaryemail, emergencysecondarynumber, emergencysecondarynationality, emergencysecondaryreligion):
        self.firstname = firstname
        self.description = description
        self.lastname = lastname
        self.job = job
        self.address = address
        self.file_data = file_data
        self.user_id = user_id
        self.phonenumber = phonenumber
        self.gender = gender
        self.country = country
        self.state = state
        self.city = city
        self.maritalstatus = maritalstatus
        self.religion = religion
        self.emergencyprimaryname = emergencyprimaryname
        self.emergencyprimaryrelationship=emergencyprimaryrelationship
        self.emergencyprimaryemail = emergencyprimaryemail
        self.emergencyprimarynumber = emergencyprimarynumber
        self.emergencyprimarynationality = emergencyprimarynationality
        self.emergencyprimaryreligion = emergencyprimaryreligion
        self.emergencysecondaryname = emergencysecondaryname
        self.emergencysecondaryrelationship = emergencysecondaryrelationship
        self.emergencysecondaryemail = emergencysecondaryemail
        self.emergencysecondarynumber = emergencysecondarynumber
        self.emergencysecondarynationality = emergencysecondarynationality
        self.emergencysecondaryreligion = emergencysecondaryreligion

@app.route("/userprofile_details/<int:userprofile_id>", methods=["GET", "POST"])
@login_required
def userprofile_details(userprofile_id):
    userprofile = Userprofile.query.get_or_404(userprofile_id)
    if not userprofile:
        # Handle project not found
        flash("Project not found", "error")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('profile'))

    if request.method == "POST":
        # Retrieve the form data
        firstname=request.form.get('firstname')
        lastname=request.form.get('lastname')
        description=request.form.get('shortdescription')
        job=request.form.get('job')
        address=request.form.get('address')
        phonenumber=request.form.get('phonenumber')
        gender=request.form.get('gender')
        
        userprofile.firstname = firstname
        userprofile.lastname = lastname
        userprofile.description = description
        userprofile.job = job
        userprofile.address = address
        userprofile.phonenumber = phonenumber
        userprofile.gender = gender

        db.session.commit()
        # Handle successful project update
        flash("Project updated successfully", "success")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('profile'))

    return render_template("profile.html", userprofile=userprofile)

@app.route("/userprofilepersonal_details/<int:userprofile_id>", methods=["GET", "POST"])
@login_required
def userprofilepersonal_details(userprofile_id):
    userprofile = Userprofile.query.get_or_404(userprofile_id)
    if not userprofile:
        # Handle project not found
        flash("Project not found", "error")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('profile'))

    if request.method == "POST":
        # Retrieve the form data
        country=request.form.get('country')
        state=request.form.get('state')
        city=request.form.get('city')
        maritalstatus=request.form.get('maritalstatus')
        religion=request.form.get('religion')
        
        userprofile.country = country
        userprofile.state = state
        userprofile.city = city
        userprofile.maritalstatus = maritalstatus
        userprofile.religion = religion

        db.session.commit()
        # Handle successful project update
        flash("Project updated successfully", "success")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('profile'))

    return render_template("profile.html", userprofile=userprofile)

@app.route("/userprofileemergency_details/<int:userprofile_id>", methods=["GET", "POST"])
@login_required
def userprofileemergency_details(userprofile_id):
    userprofile = Userprofile.query.get_or_404(userprofile_id)
    if not userprofile:
        # Handle project not found
        flash("Project not found", "error")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('profile'))

    if request.method == "POST":
        # Retrieve the form data
        emergencyprimaryname=request.form.get('emergencyprimaryname')
        emergencyprimaryrelationship=request.form.get('emergencyprimaryrelationship')
        emergencyprimaryemail=request.form.get('emergencyprimaryemail')
        emergencyprimarynumber=request.form.get('emergencyprimarynumber')
        emergencyprimarynationality=request.form.get('emergencyprimarynationality')
        emergencyprimaryreligion=request.form.get('emergencyprimaryreligion')
        emergencysecondaryname=request.form.get('emergencysecondaryname')
        emergencysecondaryrelationship=request.form.get('emergencysecondaryrelationship')
        emergencysecondaryemail=request.form.get('emergencysecondaryemail')
        emergencysecondarynumber=request.form.get('emergencysecondarynumber')
        emergencysecondarynationality=request.form.get('emergencysecondarynationality')
        emergencysecondaryreligion=request.form.get('emergencysecondaryreligion')
        
        userprofile.emergencyprimaryname = emergencyprimaryname
        userprofile.emergencyprimaryrelationship = emergencyprimaryrelationship
        userprofile.emergencyprimaryemail = emergencyprimaryemail
        userprofile.emergencyprimarynumber = emergencyprimarynumber
        userprofile.emergencyprimarynationality = emergencyprimarynationality
        userprofile.emergencyprimaryreligion = emergencyprimaryreligion
        userprofile.emergencysecondaryname = emergencysecondaryname
        userprofile.emergencysecondaryrelationship = emergencysecondaryrelationship
        userprofile.emergencysecondaryemail = emergencysecondaryemail
        userprofile.emergencysecondarynumber = emergencysecondarynumber
        userprofile.emergencysecondarynationality = emergencysecondarynationality
        userprofile.emergencysecondaryreligion = emergencysecondaryreligion

        db.session.commit()
        # Handle successful project update
        flash("Project updated successfully", "success")
        # Redirect to the referring page
        return redirect(request.referrer or url_for('profile'))

    return render_template("profile.html", userprofile=userprofile)

@app.route("/upload/<int:userprofile_id>", methods=['GET','POST'])
def upload_image(userprofile_id):
    if 'image' not in request.files:
        return 'No image uploaded', 400

    image_file = request.files['image']
    if image_file.filename == '':
        return 'No image selected', 400

    try:
        with image_file.stream as file_stream:
            image_data = file_stream.read()
            userprofile = Userprofile.query.get_or_404(userprofile_id)
            if userprofile:
                userprofile.file_data = image_data
            else:
                userprofile = Userprofile(userprofile_id, image_data=image_data)
            
            db.session.commit()
            return render_template("profile.html", userprofile=userprofile)
    except Exception as e:
        return 'Error occurred while uploading the image: {}'.format(str(e)), 500


@app.route('/image/<int:userprofile_id>', methods=['GET'])
def get_image(userprofile_id):
    userprofile = Userprofile.query.get_or_404(userprofile_id)
    if userprofile is not None and userprofile.file_data is not None:
        file_data = userprofile.file_data
        userprofile.file_data = f'image_{userprofile_id}'
        # Determine the file extension
        _, ext = os.path.splitext(userprofile.file_data)
        mime_type = mimetypes.guess_type(userprofile.file_data)[0] or 'application/octet-stream'
        return send_file(BytesIO(file_data), mimetype=mime_type)
    else:
        return 'Image not found', 404
    
class ProjectImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    imagefile_data = db.Column(db.LargeBinary, nullable=True)
    image_filename = db.Column(db.String(256), nullable=True)
    creator_username = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define a relationship with the Project table
    project = db.relationship('Project', backref=db.backref('project_images', lazy=True))

    # Define a relationship with the User table
    user = db.relationship('User', backref=db.backref('project_images', lazy=True))

    def __init__(self, user_id, project_id, imagefile_data, image_filename, creator_username):
        self.user_id = user_id
        self.project_id = project_id
        self.imagefile_data = imagefile_data
        self.image_filename = image_filename
        self.creator_username = creator_username
@app.route("/projectimageupload/<int:project_id>", methods=['GET','POST'])
def upload_projectimage(project_id):
    if 'project-img-file' not in request.files:
        return 'No image uploaded', 400

    projectimage_file = request.files['project-img-file']
    if projectimage_file.filename == '':
        return 'No image selected', 400

    try:
        with projectimage_file.stream as file_stream:
            image_data = file_stream.read()
            image_filename = secure_filename(projectimage_file.filename)
            creator_username = current_user.username
            projectimage= ProjectImage(
                imagefile_data=image_data,
                image_filename=image_filename,
                creator_username=creator_username,   
                user_id=current_user.id,  # Set the user ID
                project_id=project_id
            )
            db.session.add(projectimage)
            db.session.commit()
        # Redirect to the referring page
        return redirect(request.referrer or url_for('projectdetails'))
    except Exception as e:
        return 'Error occurred while uploading the image: {}'.format(str(e)), 500


@app.route('/projectimage/<int:project_image_id>', methods=['GET'])
def image_view(project_image_id):
    project_image = ProjectImage.query.get_or_404(project_image_id)
    if project_image is not None and project_image.imagefile_data is not None:
        file_data = project_image.imagefile_data
        project_image.file_data = f'image_{project_image_id}'
        # Determine the file extension
        _, ext = os.path.splitext(project_image.file_data)
        mime_type = mimetypes.guess_type(project_image.file_data)[0] or 'application/octet-stream'
        return send_file(BytesIO(file_data), mimetype=mime_type)
    else:
        return 'Image not found', 404

@app.route('/taskimage/delete/<int:project_image_id>', methods=['POST'])
def delete_image(project_image_id):
    project_image = ProjectImage.query.get_or_404(project_image_id)

    if project_image is not None:
        # Delete the image from the database
        db.session.delete(project_image)
        db.session.commit()
        return redirect(request.referrer or url_for('projectdetails'))
    return 'Image not found', 404
    
class TaskImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    imagefile_data = db.Column(db.LargeBinary, nullable=True)
    image_filename = db.Column(db.String(256), nullable=True)
    creator_username = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define a relationship with the Project table
    task = db.relationship('Task', backref=db.backref('task_images', lazy=True))

    # Define a relationship with the User table
    user = db.relationship('User', backref=db.backref('task_images', lazy=True))

    def __init__(self, user_id, task_id, imagefile_data, image_filename, creator_username):
        self.user_id = user_id
        self.task_id = task_id
        self.imagefile_data = imagefile_data
        self.image_filename = image_filename
        self.creator_username = creator_username
@app.route("/taskimageupload/<int:task_id>", methods=['GET','POST'])
def upload_taskimage(task_id):
    if 'task-img-file' not in request.files:
        return 'No image uploaded', 400

    taskimage_file = request.files['task-img-file']
    if taskimage_file.filename == '':
        return 'No image selected', 400

    try:
        with taskimage_file.stream as file_stream:
            image_data = file_stream.read()
            image_filename = secure_filename(taskimage_file.filename)
            creator_username = current_user.username
            taskimage= TaskImage(
                imagefile_data=image_data,
                image_filename=image_filename,
                creator_username=creator_username,   
                user_id=current_user.id,  # Set the user ID
                task_id=task_id
            )
            db.session.add(taskimage)
            db.session.commit()
        # Redirect to the referring page
        return redirect(request.referrer or url_for('taskdetails'))
    except Exception as e:
        return 'Error occurred while uploading the image: {}'.format(str(e)), 500


@app.route('/taskimage/<int:task_image_id>', methods=['GET'])
def taskimage_view(task_image_id):
    task_image = TaskImage.query.get_or_404(task_image_id)
    if task_image is not None and task_image.imagefile_data is not None:
        file_data = task_image.imagefile_data
        task_image.file_data = f'image_{task_image_id}'
        # Determine the file extension
        _, ext = os.path.splitext(task_image.file_data)
        mime_type = mimetypes.guess_type(task_image.file_data)[0] or 'application/octet-stream'
        return send_file(BytesIO(file_data), mimetype=mime_type)
    else:
        return 'Image not found', 404

@app.route('/image/delete/<int:task_image_id>', methods=['POST'])
def delete_image_task(task_image_id):
    task_image = TaskImage.query.get_or_404(task_image_id)

    if task_image is not None:
        # Delete the image from the database
        db.session.delete(task_image)
        db.session.commit()
        return redirect(request.referrer or url_for('taskdetails'))
    return 'Image not found', 404

class FileItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    filename = db.Column(db.String(256), nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_username = db.Column(db.String(50))
    file_type = db.Column(db.String(50), nullable=False)

    # Define a relationship with the Task table
    task = db.relationship('Task', backref=db.backref('file_items', lazy=True))

    # Define a relationship with the User table
    user = db.relationship('User', backref=db.backref('file_items', lazy=True))

    def __init__(self, user_id, task_id, filename, file_extension, file_data, file_size, creator_username, file_type):
        self.user_id = user_id
        self.task_id = task_id
        self.filename = filename
        self.file_extension = file_extension
        self.file_data = file_data
        self.file_size = file_size
        self.creator_username = creator_username
        self.file_type = file_type

@app.route("/taskfileupload/<int:task_id>", methods=['POST'])
def upload_taskfile(task_id):
    file = request.files['task-file']
    if file.filename == '':
        return 'No file selected', 400

    try:
        filename = secure_filename(file.filename)
        file_extension = os.path.splitext(filename)[1].lower()
        file_data = file.read()
        file_size = len(file_data)
        file.seek(0)  # Reset the file cursor

        # Determine the file type based on the file extension
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            file_type = 'image'
        elif file_extension in ['.doc', '.docx', '.txt']:
            file_type = 'document'
        elif file_extension in ['.pdf']:
            file_type = 'pdf'
        elif file_extension in ['.mp4', '.avi', '.mov', '.wmv']:
            file_type = 'video'
        else:
            file_type = 'other'

        file_item = FileItem(
            user_id=current_user.id,
            task_id=task_id,
            filename=filename,
            file_extension=file_extension,
            file_data=file_data,
            file_size=file_size,
            file_type=file_type,
            creator_username = current_user.username
        )
        db.session.add(file_item)
        db.session.commit()

        return redirect(request.referrer or url_for('taskdetails'))

    except Exception as e:
        return 'Error occurred while uploading the file: {}'.format(str(e)), 500

# @app.route('/image/<int:file_item_id>', methods=['GET'])
# def get_task_image(file_item_id):
#     file_item = FileItem.query.get_or_404(file_item_id)
#     if file_item is not None:
#         file_data = file_item.file_data
#         file_extension = file_item.file_extension[1:]  # Remove the leading dot from the extension
#         mime_type = mimetypes.guess_type(file_item.filename)[0] or 'application/octet-stream'
#         return send_file(BytesIO(file_data), mimetype=mime_type)

#     return 'Image not found', 404

@app.route('/file/download/<int:file_item_id>', methods=['GET'])
def download_file(file_item_id):
    file_item = FileItem.query.get_or_404(file_item_id)
    if file_item is not None:
        file_data = file_item.file_data
        filename= file_item.filename
        file_extension = file_item.file_extension[1:]  # Remove the leading dot from the extension
        mime_type = mimetypes.guess_type(file_item.filename)[0] or 'application/octet-stream'
        return send_file(BytesIO(file_data), mimetype=mime_type, as_attachment=True, download_name=filename)

    return 'File not found', 404


@app.route('/file/delete/<int:file_item_id>', methods=['POST'])
def delete_file(file_item_id):
    file_item = FileItem.query.get_or_404(file_item_id)
    if file_item is not None:
        # Delete the file from the database
        db.session.delete(file_item)
        db.session.commit()
        return redirect(request.referrer or url_for('taskdetails'))

    return 'File not found', 404

def convert_file_size(file_size):
    # Define the conversion units
    units = ['B', 'KB', 'MB', 'GB']

    # Calculate the file size in different units
    size = file_size
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    # Format the file size with two decimal places
    size = '{:.2f}'.format(size)

    # Return the formatted size with the corresponding unit
    return '{} {}'.format(size, units[unit_index])


# Make the convert_file_size function available in the template globals
app.jinja_env.globals.update(convert_file_size=convert_file_size)

class ProjectFileItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    filename = db.Column(db.String(256), nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_username = db.Column(db.String(50))
    file_type = db.Column(db.String(50), nullable=False)

    # Define a relationship with the Task table
    project = db.relationship('Project', backref=db.backref('projectfile_items', lazy=True))

    # Define a relationship with the User table
    user = db.relationship('User', backref=db.backref('projectfile_items', lazy=True))

    def __init__(self, user_id, project_id, filename, file_extension, file_data, file_size, creator_username, file_type):
        self.user_id = user_id
        self.project_id = project_id
        self.filename = filename
        self.file_extension = file_extension
        self.file_data = file_data
        self.file_size = file_size
        self.creator_username = creator_username
        self.file_type = file_type

@app.route("/projectfileupload/<int:project_id>", methods=['POST'])
def upload_projectfile(project_id):
    file = request.files['project-file']
    if file.filename == '':
        return 'No file selected', 400

    try:
        filename = secure_filename(file.filename)
        file_extension = os.path.splitext(filename)[1].lower()
        file_data = file.read()
        file_size = len(file_data)
        file.seek(0)  # Reset the file cursor

        # Determine the file type based on the file extension
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            file_type = 'image'
        elif file_extension in ['.doc', '.docx', '.txt']:
            file_type = 'document'
        elif file_extension in ['.pdf']:
            file_type = 'pdf'
        elif file_extension in ['.mp4', '.avi', '.mov', '.wmv']:
            file_type = 'video'
        else:
            file_type = 'other'

        projectfile_item = ProjectFileItem(
            user_id=current_user.id,
            project_id=project_id,
            filename=filename,
            file_extension=file_extension,
            file_data=file_data,
            file_size=file_size,
            file_type=file_type,
            creator_username = current_user.username
        )
        db.session.add(projectfile_item)
        db.session.commit()

        return redirect(request.referrer or url_for('projectdetails'))

    except Exception as e:
        return 'Error occurred while uploading the file: {}'.format(str(e)), 500

@app.route('/projectfile/download/<int:projectfile_item_id>', methods=['GET'])
def download_projectfile(projectfile_item_id):
    file_item = ProjectFileItem.query.get_or_404(projectfile_item_id)
    if file_item is not None:
        file_data = file_item.file_data
        filename= file_item.filename
        file_extension = file_item.file_extension[1:]  # Remove the leading dot from the extension
        mime_type = mimetypes.guess_type(file_item.filename)[0] or 'application/octet-stream'
        return send_file(BytesIO(file_data), mimetype=mime_type, as_attachment=True, download_name=filename)

    return 'File not found', 404


@app.route('/projectfile/delete/<int:projectfile_item_id>', methods=['POST'])
def delete_projectfile(projectfile_item_id):
    file_item = ProjectFileItem.query.get_or_404(projectfile_item_id)
    if file_item is not None:
        # Delete the file from the database
        db.session.delete(file_item)
        db.session.commit()
        return redirect(request.referrer or url_for('projectdetails'))

    return 'File not found', 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
