import os
from flask import (
    Flask, flash, render_template, redirect, request, session, url_for )
from flask_pymongo import PyMongo 
from bson.objectid import ObjectId 
from werkzeug.security import generate_password_hash, check_password_hash



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

@app.route("/")
@app.route("/events")
def events():
    """ return the listings on events page"""
    events = list(mongo.db.events.find()) 
    return render_template("events.html", events=events)


@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if request.method =="POST":         
         
        event = {
            "event_name": request.form.get("event_name"),
            "event_type": request.form.get("event_type"),
            "event_location": request.form.get("event_location"),
            "description": request.form.get("description"),
            "date": request.form.get("date"),            
            # "created_by": session['user'],
            "image" : request.form.get("image_url")            
            }
        mongo.db.homes.insert_one(event)
        flash("Event Successfully Added")
    types= mongo.db.types.find().sort("event_type", 1)
 
    return render_template("add_event.html", types=types)
    


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), port=int(os.environ.get("PORT")),debug=True)