import os
from flask import (
    Flask, flash, render_template, redirect, request, session, url_for )
from flask_pymongo import PyMongo 
from bson.objectid import ObjectId 
from werkzeug.security import generate_password_hash, check_password_hash
from flask_paginate import Pagination, get_page_args


# import env package so it can be seen on Heroku. Otherwise potential errors due to gitignore. 

if os.path.exists("env.py"):
    import env


# app is the instance of Flask
app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")



# an instance of pymongo by adding a constructor method, so the app object communicates with the Mongo db. 

mongo = PyMongo(app)


# Pagination Max 10
PER_PAGE = 5

# Paginate listings: 
# ref https://gist.github.com/mozillazg/69fb40067ae6d80386e10e105e6803c9

def paginated(events):
    ## extensive lists parameters
    page, per_page, offset = get_page_args(
                            page_parameter='page',
                            per_page_parameter='per_page')
    offset = page * PER_PAGE - PER_PAGE

    return events[offset: offset + PER_PAGE]


def pagination_args(events):
    # Extensive listing parameters
    page, per_page, offset = get_page_args(
                            page_parameter='page',
                            per_page_parameter='per_page')
    total = len(events)

    return Pagination(page=page, per_page=PER_PAGE, total=total)


    
@app.route("/")
@app.route("/events")
def events():
    """ Returns list of events from folder, newest to oldest """
    events = list(mongo.db.events.find().sort("created_on", -1))
    types = mongo.db.types.find().sort("event_type", 1)
    events_paginated = paginated(events)
    pagination = pagination_args(events)
    return render_template(
        "events.html",
        events=events_paginated,
        types = types,
        pagination=pagination)



# route without pagination
# @app.route("/")
# @app.route("/events")
# def events():
#     """ return the listings on events page"""
#     events = list(mongo.db.events.find()) 
#     return render_template("events.html", events=events)



@app.route("/search", methods = ["POST", "GET"])
def search():    
    query=request.form.get('text')
    events = list(mongo.db.events.find().sort("created_on", -1))
    result = list(mongo.db.events.find({"$text": {"$search": query}}))
    result_paginated = paginated(result)
    pagination = pagination_args(result)
    return render_template(
        "events.html",
        events=result_paginated,        
        pagination=pagination)


@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if request.method =="POST":        
         
        event = {
            "event_name": request.form.get("event_name"),
            "event_type": request.form.get("event_type"),
            "location": request.form.get("location"),
            "description": request.form.get("description"),
            "date": request.form.get("date"),            
            "created_by": session['user'],
            "image_url" : request.form.get("image_url")            
            }
        mongo.db.events.insert_one(event)
        flash("Event Successfully Added")
    types= mongo.db.types.find().sort("event_type", 1) 
    return render_template("add_event.html", types=types)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username taken!")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "email": request.form.get("email").lower(),
            "favourites": []
        }
        mongo.db.users.insert_one(register)

        session["user"] = request.form.get("username").lower()
        flash("Registration complete!")
        return redirect(url_for("events"))
    return render_template('register.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                session['logged_in'] = True
                return redirect(url_for(
                    "profile", username= session['user']))
            else:
                flash("Invalid username/password")
                return redirect(url_for("login"))
        else:
            flash("Invalid username/password")
            return redirect(url_for("login"))
    return render_template("login.html")



@app.route("/edit_event/<event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    if request.method =="POST":        
        submit = {
            "event_name": request.form.get("event_name"),
            "event_type": request.form.get("event_type"),
            "location": request.form.get("location"),
            "description": request.form.get("description"),
            "date": request.form.get("date"),            
            "created_by": session['user'],
            "image_url" : request.form.get("image_url")            
            }
        mongo.db.events.update({"_id": ObjectId(event_id)},submit)
        flash("Event Successfully Updated. Thank You!")

    event = mongo.db.events.find_one({"_id":ObjectId(event_id)})
    types= mongo.db.types.find().sort("event_type", 1) 
    return render_template("edit_event.html", event=event, types=types)


@app.route("/delete_event/<event_id>")
def delete_event(event_id):
    mongo.db.users.update(
        {"favourites": ObjectId(event_id)},
        {"$pull": {"favourites": ObjectId(event_id)}})
    mongo.db.events.remove({"_id": ObjectId(event_id)})
    flash("Your Event has been Deleted.")
    return redirect(url_for("events"))


# view event 


@app.route("/view_event/<id>")
def view_event(id):
    current_event = mongo.db.events.find_one({"_id": ObjectId(id)})
    return render_template("view_event.html", event=current_event)


# logout app 


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    session.pop('logged_in', None)
    return redirect(url_for("login"))

# profile app
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    myevents = {"created_by": session["user"]}

    user = mongo.db.users.find_one({"username": session["user"]})

    favourites = user['favourites']
    results = []
    for fav in favourites:
        results.append(mongo.db.events.find_one({"_id": ObjectId(fav)}))

    own_events = mongo.db.events.find(myevents)

    if session["user"]:
        return render_template(
            "profile.html", username=username, favourites=favourites,
            myevents=myevents, own_events=own_events, results=results)

    return redirect(url_for("login"))


@app.route("/add_favourite/<event_id>", methods=["GET", "POST"])
def add_favourite(event_id):
    username = session["user"]
    user = mongo.db.users.find_one({"username": session["user"]})

    favourites = user['favourites']
    results = []
    for fav in favourites:
        results.append(mongo.db.events.find_one({"_id": ObjectId(fav)}))

    current_event = mongo.db.events.find_one({"_id": ObjectId(event_id)})

    if current_event in results:
        flash("This event is already in your favourites")
        return redirect(url_for("profile", username=username))
    else:
        mongo.db.users.update_one(
            {"username": session["user"].lower()},
            {"$push": {"favourites": ObjectId(event_id)}})
        flash("Favourite saved")
        return redirect(url_for("profile", username=username))


@app.route("/remove_favourite/<event_id>", methods=["GET", "POST"])
def remove_favourite(event_id):
    username = session['user']
    mongo.db.users.find_one_and_update(
        {"username": session["user"].lower()},
        {"$pull": {"favourites": ObjectId(event_id)}})
    flash("Favourite removed")
    return redirect(url_for("profile", username=username))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), port=int(os.environ.get("PORT")), 
            debug=True)
