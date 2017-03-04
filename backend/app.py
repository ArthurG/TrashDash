import keys 

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from clarifai.rest import ClarifaiApp

import traceback
import requests
import json
from datetime import datetime

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
        self.fb_id = facebook_id
        self.fb_name = facebook_name
        self.pastAction = ""
        self.kijiji_email = ""
        self.kijiji_password = ""

class DisposalTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    itemname = db.Column(db.String(50))
    category = db.Column(db.String(50)) #TODO: Process category of product instead of just name
    datetime = db.Column(db.DateTime)
    wishtopost = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('disposals', lazy='dynamic'))
    def __init__(self, user, amount, itemname, category):
        self.user = user
        self.value = amount
        self.datetime = datetime.utcnow()
        self.category = category
        self.itemname = itemname
        self.wishtopost = False

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
                    if messaging_event["message"].get("quick_reply", False):
                        process_quick_reply(messaging_event)
                    #Process text
                    elif messaging_event["message"].get("text", False):
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
    prices = {"banana": 1, "milk": 5, "cheese": 5, "orange": 1, "apple": 1, None: -1}
    return prices.get(product_type, 10)

def get_food_type(concepts):
    accepted_foods = ["banana", "orange", "apple", "milk", "cheese"]
    for concept in concepts:
        if concept["name"] in accepted_foods:
            return concept["name"]

def suggest_kijiji(messaging_event):
    return ""

def save_trash_to_database(user, product_type, value):
    product = DisposalTransaction(user, value, product_type, product_type)
    db.session.add(product)
    db.session.commit()

def process_image(messaging_event):
    user = get_user_or_signup(messaging_event)
    ans = model.predict_by_url(messaging_event["message"]["attachments"][0]["payload"]["url"])
    print(json.dumps(ans, indent=4))
    product_type = str(ans["outputs"][0]["data"]["concepts"][0]["name"])
    if product_type != "food":
        value = get_price(product_type)
    else:
        food_ans = model_food.predict_by_url(messaging_event["message"]["attachments"][0]["payload"]["url"])
        product_type = get_food_type(food_ans["outputs"][0]["data"]["concepts"])
        value = get_food_price(product_type)
        print(json.dumps(food_ans, indent=4))

    send_message(messaging_event["sender"]["id"], "You sent me {} and I think it is worth {}".format(product_type, value))
    save_trash_to_database(user, product_type, value)


    if (value >= 30):
        if (user.kijiji_email != "" and user.kijiji_email) and (user.kijiji_password and user.kijiji_password != ""):
            suggest_kijiji(messaging_event)
        else:
            m = {"message": "That looks valuable, you might want to list that on Kijiji...", "replies": [{"msg": "Yes", "payload": "YESLIST"},{"msg": "No", "payload": "NOLIST"}]}
            send_message_quick_reply(user.fb_id, m)
    else:
        send_message(user.fb_id, "Waste is now saved")

def get_user_or_signup(messaging_event):
    user = User.query.filter_by(fb_id=messaging_event["sender"]["id"]).first()
    if user == None:
        #TODO: get the user's facebook name too
        uid = messaging_event["sender"]["id"]
        name = get_user_full_name(uid)
        user = User(uid, name)
        db.session.add(user)
        db.session.commit()
        send_message(user.fb_id, "Thank you for signing up! You can now start sending me pictures of your trash")
    return user

def process_quick_reply(messaging_event):
    quick_reply_payload = messaging_event["message"]["quick_reply"]["payload"] 
    if quick_reply_payload == "YESLIST":
        messaging_event["message"]["text"] = "Link Kijiji"
        process_string_message(messaging_event)
        user = User.query.filter_by(fb_id=messaging_event["sender"]["id"]).first()
        disposal = user.disposals[-1]
        disposal.wishtopost = True
        db.session.commit()

def process_string_message(messaging_event):
    user = get_user_or_signup(messaging_event)
    message = messaging_event["message"]["text"]
    past_state = user.command_in_progress
        ##Kijiji type actions
    if past_state == "kijiji_username":
        user.kijiji_email = message
        user.command_in_progress = "kijiji_password"
        db.session.commit()
        send_message(user.fb_id, "And your Kijiji password is?")
        return
    elif past_state == "kijiji_password":
        user.command_in_progress = ""
        user.kijiji_password = message
        db.session.commit()
        send_message(user.fb_id, "Done! Your Kijiji info is saved. You will now be prompted to list expensive products on Kijiji")
        return
    elif message == "Link Kijiji":
        send_message(user.fb_id, "What is your kijiji email?")
        user.command_in_progress = "kijiji_username"
        db.session.commit()
        return

    #Retriving status Web UI links
    elif message == "Dashboard":
        send_dashboard_link(user)
    #Branch for processing quick requests ie: summaryToday, etc

def process_wish_to_post(user):
    #if user.disposals[-1].wishtopost:
        #kijiji_post(item)
    return 

def send_dashboard_link(user):
    msg = {
        "attachment":{
          "type":"template",
          "payload":{
            "template_type":"generic",
            "elements":[
               {
                "title":"Welcome to your Trash Dash(board)",
                "image_url":"https://d13yacurqjgara.cloudfront.net/users/15720/screenshots/989123/chartjs.png",
                "subtitle":"Making you less waste, one product at a time",
                "buttons": [
                    {
                      "type": "web_url",
                      "url": "http://localhost:8080/uid={}".format(user.id),
                      "title": "View",
                    }
                ],
              }
            ]
          }
        }
    }
    #send_message(user.fb_id, "http://localhost:3000/uid={}".format(user.id))
    send_message_raw(json.dumps({"recipient": {"id": user.fb_id},"message": msg}))


def send_message(recipient, text):
    data = json.dumps({
    "recipient": {
        "id": recipient
        },
    "message": {

        "text": text,

        }
    })
    send_message_raw(data)

def send_message_quick_reply(recipient, data):
    msg = data["message"]
    replies = data["replies"]
    quick_replies = [{"content_type": "text", "title": reply["msg"], "payload": reply["payload"]} for reply in replies]
    content = json.dumps({"recipient": {"id": recipient},
           "message": {
               "text": msg,
               "quick_replies": quick_replies
               }
           })
    send_message_raw(content)

def send_message_raw(data):
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

def get_user_full_name(uid):
    url = "https://graph.facebook.com/v2.6/1314551495274556?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token="+keys.ACCESS_TOKEN
    r = requests.get(url)
    response = r.json()
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)
    return response["first_name"] + " " + response["last_name"]

