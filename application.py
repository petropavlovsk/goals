from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import update
from sqlalchemy import Date, cast
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
import json
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from functools import wraps
import urllib.request

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Flask-SQLAlchemy
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///goals.db"
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)

#sets upp a class for the users table. enables comunication with the database with sql-alchemy.
class Users(db.Model): # defines the table so that python can talk to the database useing SQLAlchemy. in Classes you can have both methods and data. every row becomes an object.
    __tablename__ = 'users' #defines the table name
    id = db.Column(db.Integer, primary_key=True) #anger att det är en int som är primary key
    name = db.Column(db.Text, primary_key=True)
    boss = db.Column(db.Text)
    dep = db.Column(db.Text)
    hash = db.Column(db.Text)
    adm = db.Column(db.Text)
    email = db.Column(db.Text)
    reported = db.Column(db.Text)
    okeyed = db.Column(db.Text)
    okeyed2 = db.Column(db.Text)

    def __init__(self, name, boss, dep, hash, adm, email, reported, okeyed, okeyed2):
        self.name = name
        self.boss = boss
        self.dep = dep
        self.hash = hash
        self.adm = adm
        self.email = email
        self.reported = reported
        self.okeyed = okeyed
        self.okeyed2 = okeyed2

#sets upp a class for the tertial table. enables comunication with the database with sql-alchemy.
class Tertial(db.Model): # defines the table so that python can talk to the database useing SQLAlchemy. in Classes you can have both methods and data. every row becomes an object.
    __tablename__ = 'tertial' #defines the table name
    tertial_id = db.Column(db.Integer, primary_key=True)
    tertial_name = db.Column(db.Text)
    active_tertial = db.Column(db.Text)
    def __init__(self, tertial_name, active_tertial):
        self.tertial_name = tertial_name
        self.active_tertial = active_tertial

#sets upp a class for the dep (department) table. enables comunication with the database with sql-alchemy.  fills the drop-down-menues when you adds users.
class Deps(db.Model): # defines the table so that python can talk to the database useing SQLAlchemy. in Classes you can have both methods and data. every row becomes an object.
    __tablename__ = 'dep' #defines the table name
    dep_id = db.Column(db.Integer, primary_key=True)
    dep_name = db.Column(db.Text, primary_key=True)
    boss_id = db.Column(db.Integer)

    def __init__(self, dep_name, boss_id):
        self.dep_name = dep_name
        self.boss_id = boss_id

#sets upp a class for the boss table. enables comunication with the database with sql-alchemy. fills the drop-down-menues when you adds users.
class Boss(db.Model): # defines the table so that python can talk to the database useing SQLAlchemy. in Classes you can have both methods and data. every row becomes an object.
    __tablename__ = 'boss' #defines the table name
    boss_id = db.Column(db.Integer, primary_key=True) #anger att det är en int som är primary key
    boss_name = db.Column(db.Text)

    def __init__(self, boss_name):
        self.boss_name = boss_name

#sets upp a class for the goals table. enables comunication with the database with sql-alchemy.
class Goals(db.Model): # defines the table so that python can talk to the database useing SQLAlchemy. in Classes you can have both methods and data. every row becomes an object.
    __tablename__ = 'goals' #defines the table name
    goal_id = db.Column(db.Integer, primary_key=True)
    goal_name = db.Column(db.Text)
    dep_name = db.Column(db.Text)
    goal_level = db.Column(db.Text)

    def __init__(self, goal_name, dep_name, goal_level):
        self.goal_name = goal_name
        self.dep_name = dep_name
        self.goal_level = goal_level

#sets upp a class for the activities table. enables comunication with the database with sql-alchemy.
class Activities(db.Model): # defines the table so that python can talk to the database useing SQLAlchemy. in Classes you can have both methods and data. every row becomes an object.
    __tablename__ = 'activities' #defines the table name
    activity_id = db.Column(db.Integer, primary_key=True) #anger att det är en int som är primary key
    activity_name = db.Column(db.Text)
    goal_name = db.Column(db.Text)
    dep_name = db.Column(db.Text)
    date = db.Column(db.DateTime)
    done = db.Column(db.Text)
    reported = db.Column(db.Text)
    late = db.Column(db.Text)

    def __init__(self, activity_name, goal_name, dep_name, date, done, reported, late):
        self.activity_name = activity_name
        self.goal_name = goal_name
        self.dep_name = dep_name
        self.date = date
        self.done = done
        self.reported = reported
        self.late = late

#this function demands a loged in status when functions with the @login_required is called
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


#this function demands a administrator  status when functions with the @login_adm_required is called
def login_adm_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if session.get("adm") is None:
            alert = "Det krävs administratörsrättigheter för denna åtgärd!"
            return apology(alert)
        return f(*args, **kwargs)
    return decorated_function


#for use when testing and developing new functions
def apology(message, code=400):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", active_tertial = session["active_tertial"], active_user =session["user_name"], top=code, bottom=escape(message)), code


#runs when the index-page is called. shows which users has reporterd their activities and which users that have a ok from their boss.
#it also shows every departments outstanding activities and the activities that has already been completet. activites that is not completed and is past its expirationdate is set to red.
@app.route("/")
@login_required #calls the loged in function to make sure that there is a logged in user
def index(): #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)

    #todays date
    now = datetime.now().date()

    #makes the activities past its expiration date red by assigning text-danger to the late value. text-danger is a bootstrap-thing
    activities = Activities.query.all()
    for item in activities:
        item.date = item.date.date()
        if item.date < now:
            setattr(item, 'late', "text-danger") #row, column to change, new input
            db.session.commit() #saves tha new info to the database using SQLAlchemy
        else:
            setattr(item, 'late', "No") #row, column to change, new input
            db.session.commit() #saves tha new info to the database using SQLAlchemy

    #lists every user
    users=Users.query.order_by('boss').all()
    #lists activities not yet completed
    toDo=Activities.query.filter(Activities.done == "No").order_by('dep_name').all()
    #lists completed activities
    done=Activities.query.filter(Activities.done == "checked").order_by('dep_name').all()

    return render_template("index.html", active_tertial = session["active_tertial"], active_user = session["user_name"], users = users, toDo=toDo, done=done, now=now)


#when the user clicks log in or when he och she tries to visit another page without being logged in, this function asks for a username and password and checks the credentions with the users database
@app.route("/login", methods=["GET", "POST"])
def login():  #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # query database for username
        rows = Users.query.filter_by(name=request.form.get("username")).first()

        # ensure username exists and password is correct
        if not pwd_context.verify(request.form.get("password"), rows.hash):  #uses the passLib for password hash support
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows.id
        if rows.adm == "Yes":
            session["adm"] = rows.adm

        #stores user name in session
        session["user_name"] = rows.name

        #remember active tertial
        session["active_tertial"] = Tertial.query.filter(Tertial.active_tertial == "checked").first()

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:

        return render_template("login.html") #opens the html-template


@app.route("/logout")
def logout():  #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/report_goals", methods=["GET", "POST"])
@login_required #calls the loged in function to make sure that there is a logged in user
def report_goals(): #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)
    #not yet active - a future function
    return render_template("report_goals.html", active_tertial = session["active_tertial"], active_user = session["user_name"])

@app.route("/report_activities", methods=["GET", "POST"])
@login_required #calls the loged in function to make sure that there is a logged in user
def report_activities(): #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)

    #if a send-button is clicked, the function calls diferent commands depending on which button is clicked.
    #it could save if a activity is marked as completed, send in the tertials report and mark the status for boss ok.
    #if the function is not called with a post-request the pages report-activities renders
    if request.method== "POST":

        #uppdates the database with the done checkbox and removes the red from late-activities.
        #when the year is over, every activity should be checked.
        if request.form['action'] == "save":

            #identifyes the loged in users department
            user = Users.query.filter_by(id=session["user_id"]).first()
            userDep = user.dep

            #identifyes the activities connected to the users department
            activities = Activities.query.filter_by(dep_name = userDep)

            #for every row in the activities database connected to the department for the logged in user
            #this is nessesery because python needs to know the name of the form to call to get the checked in info
            for item in activities:

                #marks the activity as checked if the checkbox in checked
                done = request.form[str(item.activity_id)]

                #stores the row från activities database corresponding to the row-iteration
                activity=Activities.query.filter_by(activity_id = item.activity_id).first()

                #marks the activity as done in the activities database
                setattr(activity, 'done', done) #row, column to change, new input
                db.session.commit() #saves tha new info to the database using SQLAlchemy

                #removes the text-danger that makes the text red from the late activities when the checkbox for done is checked
                #the red wont reapear it the checkbox is uncheked until the index-page is loaded again
                if request.form[str(item.activity_id)] == "checked":
                    setattr(activity, 'late', "No") #row, column to change, new input
                    db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("report_activities"))

        #when the users is satisfied that he or she has checked every completed activity, the users sends in the report for that period. the users boss can later ok the report for that terital.
        #sets the reported status for the activities to Yes and the reported status for the user to btn-success. with the help of boot-strap the button turns from red to green
        if request.form['action'] == "send":

            #identifyes the loged in users department
            user = Users.query.filter_by(id=session["user_id"]).first()
            userDep = user.dep

            #identifyes the activities connected to the users department
            activities = Activities.query.filter_by(dep_name = userDep)

            #for every row in the activities database connected to the department for the logged in user
            #this is nessesery because python needs to know the name of the form to call to get required info
            for item in activities:

                #stores the row från activities database corresponding to the row-iteration
                activity=Activities.query.filter_by(activity_id = item.activity_id).first()

                #assigns the value "Yes" to the reported keyword for activities . makes the checkbox stay checked.
                setattr(activity, 'reported', "Yes") #row, column to change, new input
                db.session.commit() #saves tha new info to the database using SQLAlchemy

            #assigns the value "btn-successes" to the reported keyword for users . makes the button go green.
            setattr(user, 'reported', "btn-success")  #row, column to change, new input
            db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("report_activities"))


        #when the users has reported his or hers tertial the boss can later ok the report. controlls the right row of buttons on the indexpage.
        #sets the okeyed from boss status to checked and btn-success for the checked users.
        if request.form['action'] == "save2":

            #identifyes the loged in users department
            user = Users.query.filter_by(id=session["user_id"]).first()

            #defines which users that the current user is boss for
            emps = Users.query.filter_by(boss=user.name).all()

            #for every row in the users database where the logged in user is the boss
            #this is nessesery because python needs to know the name of the form to call to get the checked in info
            for item in emps:
                #the ok part is needed for the iteration from the form to work
                ok = "OK_"
                ID = str(item.id)
                okID = ok + ID
                okeyed = request.form[okID]

                #stores the row från activities database corresponding to the row-iteration
                emp=Users.query.filter_by(id = str(item.id)).first()

                setattr(emp, 'okeyed', okeyed) #row, column to change, new input
                #saves tha new info to the database
                db.session.commit()

                #the okeyed2 column serves too chenge color on the button on the index page
                if okeyed == "checked":
                    setattr(emp, 'okeyed2', "btn-success") #row, column to change, new input. btn-success and btn-danger sets the button to green and red using bootstrap
                    db.session.commit() #saves tha new info to the database using SQLAlchemy

                else:
                    setattr(emp, 'okeyed2', "btn-danger") #row, column to change, new input. btn-success and btn-danger sets the button to green and red using bootstrap
                    db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("report_activities"))

        #if one of the colored buttons is clicked, the boss can see which activities the user he or she is boss over has reported as done
        else:
            empID = request.form['action']
            user = Users.query.filter_by(id=empID).first()
            empDep = user.dep

            #stores the row från activities database corresponding to the row-iteration
            activities=Activities.query.filter_by(dep_name = empDep).all()

            return render_template("show_activities.html", active_tertial = session["active_tertial"], active_user = session["user_name"], activities=activities, user=user)

    #if the post-function not is clicked, the page renders with the needed information passed in with jinja
    else:

        #searches for the logged in user and store the department name in a variable called userDep and the reported status to att variable called reported
        user = Users.query.filter_by(id=session["user_id"]).first()
        userName = user.name
        userDep = user.dep
        reported = user.reported

        #finds the goals and activities and employes for the logged in user
        #goalsByDep = Goals.query.filter(Goals.dep_name==userDep)
        activitiesByDep = Activities.query.order_by(Activities.goal_name).filter(Activities.dep_name==userDep)
        emps = Users.query.filter_by(boss=userName).all()

        return render_template("report_activities.html", activities = activitiesByDep, active_tertial = session["active_tertial"], active_user = session["user_name"], reported = reported, emps=emps) # goals = goalsByDep, allGoals = goals



@app.route("/show_activities", methods=["GET", "POST"])
@login_required #calls the loged in function to make sure that there is a logged in user
def show_activities(): #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)

    #this function is called when a boss clicks one of his och hers employees rapported button. the activities, the date and whether the activity is marked as done shows.
    return render_template("show_activities.html", active_tertial = session["active_tertial"], active_user = session["user_name"], test="test")


@app.route("/statistics", methods=["GET", "POST"])
@login_required #calls the loged in function to make sure that there is a logged in user
def statistics(): #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)

    #not implemented yet
    return render_template("statistics.html", active_tertial = session["active_tertial"], active_user = session["user_name"])


@app.route("/change_goals", methods=["GET", "POST"])
@login_required #calls the loged in function to make sure that there is a logged in user
def change_goals():  #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)

    if request.method== "POST":

        #3 alternatives for action, change, delete or add.

        #uppdates the database if something is changed in the form
        if request.form['action'] == "change":

            #identifyes the loged in users department
            user = Users.query.filter_by(id=session["user_id"]).first()
            userDep = user.dep

            #identifyes the goals connected to the users department
            goals = Goals.query.filter_by(dep_name = userDep)

            #for every row in the goals database connected to the department for the logged in user
            #this is nessesery because python needs to know the name of the form to call to get the checked in info
            for item in goals:

                #gets the old or uppdated info from the form. the second one uses id to keep them separated
                new_goal = request.form[item.goal_name]
                new_goal_level = request.form[str(item.goal_id)]

                #stores the row från goals database corresponding to the row-iteration
                goal=Goals.query.filter_by(goal_name = item.goal_name).first()

                #assigns the value of the new or old input to the goal_name keyword for the identifyed goal
                setattr(goal, 'goal_name', new_goal) #row, column to change, new input
                db.session.commit()

                #assigns the value of the new or old input to the goal_level keyword for the identifyed goal
                setattr(goal, 'goal_level', new_goal_level) #row, column to change, new input
                db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("change_goals"))


        #deletes the row if i checkbox is checked
        elif request.form['action'] == "delete":

            #identifyes the loged in users department
            user = Users.query.filter_by(id=session["user_id"]).first()
            userDep = user.dep

            #identifyes the goals connected to the users department
            goals = Goals.query.filter_by(dep_name = userDep)

            #for every row in the goals database connected to the department for the logged in user
            #this is nessesery because python needs to know the name of the form to call to get the checked in info
            for item in goals:

                #creates a variable with the value Yes if the checkbox in the form is checked. there is a hidden type after to make sure that there is always something returning från the request.form call
                delete = "DELETE_"
                value = str(item.goal_id)
                delete_value = delete+value
                check_box = request.form[delete_value]

                if str(check_box) == "YES":

                    #stores the row från goals database corresponding to the row-iteration
                    goal=Goals.query.filter_by(goal_name = item.goal_name).first()
                    db.session.delete(goal) #Deletes the row
                    db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("change_goals"))

        #adds a goal to the database
        else:

            #searches for the logged in user and store the department name in a variable called userDep
            user = Users.query.filter_by(id=session["user_id"]).first()
            userDep = user.dep

            #stores valus from the form in variables
            goal_name = request.form["goal_name"]
            dep_name = userDep
            goal_level = request.form["goal_level"]

            #the goals can an should be stored multiple times
            #stores register-form-input in a variable named user and stores that in the users database
            goal = Goals(goal_name, dep_name, goal_level)
            db.session.add(goal)
            db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("change_goals"))

    #if the page is called with the GET, the pages renders with the nessesery information
    else:

        #searches for the logged in user and store the department name in a variable called userDep
        user = Users.query.filter_by(id=session["user_id"]).first()
        userDep = user.dep

        #finds the goals for the logged in user
        goalsByDep = Goals.query.filter(Goals.dep_name==userDep)

        #finds all goals in the database
        goals = Goals.query.order_by(Goals.goal_name).all()

        return render_template("change_goals.html", goals = goalsByDep, allGoals = goals, active_tertial = session["active_tertial"], active_user = session["user_name"]) #the template renders with the needed information passed so that the template can show the information using jinja.


@app.route("/change_activities", methods=["GET", "POST"])
@login_required #calls the loged in function to make sure that there is a logged in user
def change_activities(): #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)

    if request.method== "POST":

        #3 alternatives for action, change, delete or add.

        #updates the database if something is changed in the form
        if request.form['action'] == "change":

            #identifyes the loged in users department
            user = Users.query.filter_by(id=session["user_id"]).first()
            userDep = user.dep

            #identifyes the activities connected to the users department
            activities = Activities.query.filter_by(dep_name = userDep)

            #for every row in the activities database connected to the department for the logged in user
            #this is nessesery because python needs to know the name of the form to call to get the checked in info
            for item in activities:

                #stores whatever is printed in the name field in the form. if the user hasnt changed anythin the same info as before is saved in again in the database.
                new_activity = request.form[item.activity_name]

                #stores whatever is printed in the date field in the form. if the user hasnt changed anythin the same info as before is saved in again in the database.
                #corrects the format for date and stores in the expiration_date variable
                new_date = request.form[str(item.date.date())]
                y, m, d = new_date.split('-')
                expiration_date = datetime(int(y), int(m), int(d))

                #stores the row från activities database corresponding to the row-iteration. CAN I REMOVE THIS?
                activity=Activities.query.filter_by(activity_name = item.activity_name).first()

                #assigns the value of the new or old input to the activity_name keyword for the identifyed goal
                setattr(activity, 'activity_name', new_activity) #row, column to change, new input
                db.session.commit() #saves tha new info to the database using SQLAlchemy

                #assigns the value of the new or old input to the goal_level keyword for the identifyed goal
                setattr(activity, 'date', expiration_date) #row, column to change, new input
                db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("change_activities"))


        #deletes the row if i checkbox is checked and the delete-button is clicked.
        elif request.form['action'] == "delete":
            #identifyes the loged in users department
            user = Users.query.filter_by(id=session["user_id"]).first()
            userDep = user.dep

            #identifyes the activities connected to the users department
            activities = Activities.query.filter_by(dep_name = userDep)

            #for every row in the activities database connected to the department for the logged in user
            #this is nessesery because python needs to know the name of the form to call to get the checked in info
            for item in activities:

                #creates a variable with the value Yes if the checkbox in the form is checked. there is a hidden type after to make sure that there is always something returning från the request.form call. the value then is no
                delete = "DELETE_"
                value = str(item.activity_id)
                delete_value = delete+value
                check_box = request.form[delete_value]

                #if the delete-checkbox is clicked - delete the activity from the database.
                if str(check_box) == "YES":

                    #stores the row från activities database corresponding to the row-iteration
                    activity=Activities.query.filter_by(activity_name = item.activity_name).first()

                    db.session.delete(activity) #Deletes the stored row
                    db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("change_activities"))


        #adds a activity to the database
        else:
            #stores the user department in a variable so that new goals automaticly gets that department name
            user = Users.query.filter_by(id=session["user_id"]).first()
            userDep = user.dep

            #stores valus from the form in variables
            activity_name = request.form["activity_name"]
            goal_name = request.form["goal_name"]
            dep_name = userDep
            done = "No"
            reported = "btn-danger" #btn-success and btn-danger sets the button to green and red using bootstrap
            late = "black"

            #fixes the date-input to work with the datetime format in the database
            new_date = request.form["date"]
            y, m, d = new_date.split('-')
            expiration_date = datetime(int(y), int(m), int(d))

            #the goals can an should be stored multiple times
            #stores register-form-input in a variable named user and stores that in the users database
            activity = Activities(activity_name, goal_name, dep_name, expiration_date, done, reported, late)
            db.session.add(activity)
            db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("change_activities"))

    #if the function is called without POST, render the page with the required info
    else:

        #fills to list from departments and goals for the drop-down-menues
        goals = Goals.query.order_by(Goals.goal_name).all()

        #searches for the logged in user and store the department name in a variable called userDep
        user = Users.query.filter_by(id=session["user_id"]).first()
        userDep = user.dep

        #finds the goals and activities for the logged in user
        goalsByDep = Goals.query.filter(Goals.dep_name==userDep)
        activitiesByDep = Activities.query.order_by(Activities.goal_name).filter(Activities.dep_name==userDep)

        #finds all goals in the database
        goals = Goals.query.order_by(Goals.goal_name).all()

        return render_template("change_activities.html", goals = goalsByDep, allGoals = goals, activities = activitiesByDep, active_tertial = session["active_tertial"], active_user = session["user_name"]) #the template renders with the needed information passed so that the template can show the information using jinja.



#should be called admin or something
#here the someone with a administrator-password can can add new administrators, change tertial and reset the reporting-status for everyone.
@app.route("/add_user", methods=["GET", "POST"])
@login_adm_required #calls the loged in adm function to make sure that there is a logged in administrator
def add_user(): #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)

    #fills to lists from departments and boss databases for the drop-down-menues
    boss = Boss.query.order_by(Boss.boss_name).all()
    deps = Deps.query.order_by(Deps.dep_name).all()

    #if the function is called with a post-command, 3 different commands is called.
    # ad a new user. here it´s posible to add new admin-users.
    # set tertial
    # restore reported-status

    if request.method== "POST":

        #adds user, posible to add a user with admin
        if request.form['action'] == "add":

            #stores a hashed password to to a variable named hash
            hash = pwd_context.hash(request.form["password"])
            #stors every ofther value to variables
            boss = request.form["boss"]
            name = request.form["name"]
            dep = request.form["dep"]
            adm = request.form["adm"]
            email = request.form["email"]
            reported = "btn-danger" #btn-success and btn-danger sets the button to green and red using bootstrap
            okeyed = "btn-danger" #btn-success and btn-danger sets the button to green and red using bootstrap
            okeyed2 = "btn-danger" #btn-success and btn-danger sets the button to green and red using bootstrap

            #searches existing database for the name inputed in the form
            result = Users.query.filter_by(name=name).first()

            #if the name is not in the existing database, stores a user with the values above to the users database
            if not result:
                #stores register-form-input in a variable named user and stores that in the users database
                user = Users(name, boss, dep, hash, adm, email, reported, okeyed, okeyed2)
                db.session.add(user)
                db.session.commit() #saves tha new info to the database using SQLAlchemy

            #else notify the user that the name already exists
            else:
                return apology("the username is already in the database")

            return redirect(url_for("add_user"))


        #sets tertial
        if request.form['action'] == "set":

            tertial = Tertial.query.all()
            for item in tertial:
                active_tertial = request.form[item.tertial_name]

                #stores the row från activities database corresponding to the row-iteration
                tertial=Tertial.query.filter_by(tertial_name = item.tertial_name).first()

                #HÄR SKULLE JAG BEHÖVA LÄGGA IN EN FUNKTION DÄR ALLA RADER HETER SAMMA MEN DÄR DEN VÄLJER PÅ TERTIAL BEROENDE PÅ VÄRDET I FORMULÄRET ISTÄLLET FÖR ATT KUNNA HA RADIOKNAPPAR

                setattr(tertial, 'active_tertial', active_tertial)
                db.session.commit() #saves tha new info to the database using SQLAlchemy

            #remember active tertial. the value checked is also used to pre-check the correct box
            session["active_tertial"] = Tertial.query.filter(Tertial.active_tertial == "checked").first()
            return redirect(url_for("add_user"))


        #resets the reporting-status for everyone
        #sets the value for reported for all activities to No and all users okeyed to no
        else:
            if request.form["action"] == "reset":

                #stores the row från activities database corresponding to the row-iteration
                activities=Activities.query.all()
                for item in activities:
                    setattr(item, 'reported', "No")  #assigns the value (3) to the keyword (2) for the identifyed row(1)
                    db.session.commit() #saves tha new info to the database using SQLAlchemy

                #sets the reported status for all users to btn-danger (the button becomes red again)
                #stores the row från users database corresponding to the row-iteration
                users=Users.query.all()
                for item in users:
                    #assigns the value (3) to the keyword (2) for the identifyed row(1)
                    setattr(item, 'reported', "btn-danger")  #btn-success and btn-danger sets the button to green and red using bootstrap
                    db.session.commit() #saves tha new info to the database using SQLAlchemy

                #sets the reported status for all users to btn-danger (the button becomes red again)
                #stores the row från users database corresponding to the row-iteration
                users=Users.query.all()
                for item in users:
                    #assigns the value (3) to the keyword (2) for the identifyed row(1)
                    setattr(item, 'okeyed', "btn-danger")  #btn-success and btn-danger sets the button to green and red using bootstrap
                    db.session.commit() #saves tha new info to the database using SQLAlchemy

                #sets the reported status for all users to btn-danger (the button becomes red again)
                #stores the row från users database corresponding to the row-iteration
                users=Users.query.all()
                for item in users:
                    #assigns the value (3) to the keyword (2) for the identifyed row(1)
                    setattr(item, 'okeyed2', "btn-danger")  #btn-success and btn-danger sets the button to green and red using bootstrap
                    db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("add_user"))

    #if the function is called without POST, render the page with the required info
    else:
        tertial = Tertial.query.all()
        rows = Users.query.order_by(Users.name).all()
        return render_template("add_user.html", deps = deps, boss = boss, tertial = tertial, active_tertial = session["active_tertial"], active_user = session["user_name"])   #the template renders with the needed information passed so that the template can show the information using jinja.


@app.route("/register", methods=["GET", "POST"])
def register(): #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)
    """Register user."""

    #fills to lists from departments and boss databases for the drop-down-menues
    boss = Boss.query.order_by(Boss.boss_name).all()
    deps = Deps.query.order_by(Deps.dep_name).all()

    #when the submit button is pressed
    if request.method== "POST":

        name = request.form["name"]
        boss = request.form["boss"]
        dep = request.form["dep"]
        email = request.form["email"]
        adm = None
        hash = pwd_context.hash(request.form["password"])
        reported = "btn-danger"
        okeyed = "btn-danger"
        okeyed2 = "btn-danger"

        #searches existing database for the name inputed in the form
        result = Users.query.filter_by(name=name).first()

        #if the name is not in the existing database, stor the inputed user in database
        if not result:
            #stores register-form-input in a variable named user and stores that in the users database
            user = Users(name, boss, dep, hash, adm, email, reported, okeyed, okeyed2)
            db.session.add(user)
            db.session.commit() #saves tha new info to the database using SQLAlchemy

        #else notify the user that the name already exists
        else:
            return apology("the username is already in the database")

        # query database for username
        user=Users.query.filter_by(name=request.form["name"]).first()

        #loggs in the registerd user
        #session["user_id"] = user.id
        return redirect(url_for("login"))

    #when the page loads
    else:
        return render_template("register.html", deps = deps, boss = boss)  #the template renders with the needed information passed so that the template can show the information using jinja.


@app.route("/passChange", methods=["GET", "POST"])
@login_required #calls the loged in function to make sure that there is a logged in user
def passChange(): #when this route is called, this function is automaticly called using flask (http://flask.pocoo.org/)
    """Change password."""

    if request.method== "POST":

        #checks if the old password is correct
        rows = Users.query.filter_by(id=session["user_id"]).first()
        if not pwd_context.verify(request.form.get("old_password"), rows.hash):
            return apology("invalid old password")

        #uppdates the user-table with the new database
        else:

            new_hash = pwd_context.hash(request.form["new_password"])
            #identify user for password change
            user=Users.query.filter_by(id=session["user_id"]).first()
            #assigns the value of the new hash to the hash keyword for the identifyed user
            setattr(user, 'hash', new_hash)
            db.session.commit() #saves tha new info to the database using SQLAlchemy

            return redirect(url_for("index"))

    else:
        return render_template("passChange.html", active_tertial = session["active_tertial"], active_user = session["user_name"])   #the template renders with the needed information passed so that the template can show the information using jinja.



