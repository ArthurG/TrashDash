import keys 

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from clarifai.rest import ClarifaiApp

import traceback
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

#Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fb_id = db.Column(db.String(50))
    fb_name = db.Column(db.String(50))
    kijiji_email = db.Column(db.String(50))
    kijiji_password = db.Column(db.String(50))
    command_in_progress = db.Column(db.String(50))
    def __init__(self, facebook_id, facebook_name):
        self.facebook_id = facebook_id
        self.facebook_name = facebook_name
        self.pastAction = ""

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    value = db.Column(db.Integer)
    category = db.Column(db.String(50))
    datetime = db.Column(db.DateTime)
    user = db.relationship('User', backref=db.backref('transactions', lazy='dynamic'))
    def __init__(self, user, amount, category):
        self.user = user
        self.amount = amount
        self.datetime = datetime.utcnow()
        self.category = category

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_follower_id = db.Column(db.Integer)
    user_followed_id =  db.Column(db.Integer)
    def __init__(self, follower, followed):
        self.user_follower_id = follower.id
self.user_followed_id = followed.id


clarifai = ClarifaiApp(keys.clarifai1, keys.clarifai2) 
# get the general model
model = clarifai.models.get("lhax")
model_food = clarifai.models.get("food-items-v1.0")

@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == keys.VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/webhook', methods=['POST'])
def process_webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    print("incoming msg " + str(data))  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":
        print(json.dumps(data, indent=4))

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                try:
                    #Process text
                    if messaging_event["message"].get("text", False):
                        process_string_message(messaging_event)
                    #Process image => sticker
                    elif messaging_event["message"].get("attachments", [])[0].get("type", "") == "image" and messaging_event["message"].get("attachments", [])[0].get("payload", {}).get("sticker_id", False):
                        send_message(messaging_event["sender"]["id"], "Pls no stickers. My master didn't teach me to handle 'em")
                        #Process image => not sticker
                    elif messaging_event["message"].get("attachments", [])[0].get("type", "") == "image":
                        process_image(messaging_event)
                    #Process location requests TODO
                except:
                    traceback.print_exc()

    return "ok", 200

#Temp stub until I get a real api 
def get_price(product_type):
    prices = {"laptop": 200, "iphone": 300, "phone": 200, "ipad": 300}
    return prices.get(product_type, 10)

def get_food_price(product_type):
    prices = {"banana": 1, "milk": 5, "cheese": 5, "orange": 1, "apple": 1}
    return prices.get(product_type, 10)

def get_food_type(concepts):
    accepted_foods = ["banana", "orange", "apple", "milk", "cheese"]
    
    return "banana"

def process_image(messaging_event):
    ans = model.predict_by_url(messaging_event["message"]["attachments"][0]["payload"]["url"])
    print(json.dumps(ans, indent=4))
    product_type = str(ans["outputs"][0]["data"]["concepts"][0]["name"])
    if product_type != "food":
        value = get_price(product_type)
        send_message(messaging_event["sender"]["id"], "You sent me {} and I think it is worth {}".format(product_type, value))
    elif product_type == "food":
        food_ans = model_food.predict_by_url(messaging_event["message"]["attachments"][0]["payload"]["url"])
        food_type = get_food_type(food_ans["outputs"][0]["data"]["concepts"])
        print(json.dumps(food_ans, indent=4))
        value = get_food_price(food_type)
        send_message(messaging_event["sender"]["id"], "You sent me {} and I think it is worth {}".format(food_type, value))

def process_string_message(messaging_event):
    user = User.query.filter_by(id=messaging_event["sender"]["id"]).first()
    message = messaging_event["message"]["text"]
    if user == None:
        #TODO: get the user's facebook name too
        user = User(messaging_event["sender"]["id"], "")
        db.session.add(user)
        db.session.commit()
        send_message(user.facebook_id, "Thank you for signing up! You can now start sending me pictures of your trash")
        return
    past_state = user.command_in_progress

    ##Kijiji type actions
    if past_state == "kijiji_username":
        user.kijiji_email = message
        user.command_in_progress = "kijiji_password"
        send_message(user.facebook_id, "And your Kijiji password is?")
        return
    elif past_state == "kijiji_password":
        user.command_in_progress = ""
        user.kijiji_password = message
        send_message(user.facebook_id, "Done! Your Kijiji info is saved. You will now be prompted to list expensive products on Kijiji")
        return
    elif message == "Link Kijiji":
        send_message(user.facebook_id, "What is your kijiji email?")
        user.command_in_progress = "kijiji_username"
        return

    #Retriving status Web UI links
    if message == "Dashboard":
        send_message(user.facebook_id, "What is your kijiji email?")
    #Branch for processing quick requests ie: summaryToday, etc




    send_message(messaging_event["sender"]["id"], messaging_event["message"].get("text", ""))

def send_message(recipient, text):
    data = json.dumps({
        "recipient": {
            "id": recipient
            },
        "message": {

            "text": text,

            }
        })
    params = {
            "access_token": keys.ACCESS_TOKEN
            }
    headers = {
            "Content-Type": "application/json"
            }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)

def send_message_raw(recipient, data):
    params = {
            "access_token": keys.ACCESS_TOKEN
            }
    headers = {
            "Content-Type": "application/json"
            }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)

