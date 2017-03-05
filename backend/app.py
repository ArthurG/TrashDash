import keys 
import utils

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from clarifai.rest import ClarifaiApp

import traceback
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
CORS(app)

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
    category = db.Column(db.String(50)) 
    datetime = db.Column(db.DateTime)
    wishtopost = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('disposals', lazy='dynamic'))
    def __init__(self, user, amount, itemname):
        self.user = user
        self.value = amount
        self.datetime = datetime.utcnow()
        self.category = utils.get_product_category(itemname)
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

@app.route('/<user_id>/spending_summary/', methods=['GET'])
def spending(user_id):
    week_since = datetime.utcnow()-timedelta(hours = 7*24)
    month_since = datetime.utcnow()-timedelta(hours = 30 * 24)
    day_since = datetime.utcnow()-timedelta(hours = 1*24)

    m = {"weekly": get_total_waste_since(user_id, week_since), "monthly": get_total_waste_since(user_id, month_since), "daily": get_total_waste_since(user_id, day_since)}

    spendingsPerDay = []
    for i in range(30):
        later = datetime.utcnow() - timedelta(hours = 24*i)
        earlier = datetime.utcnow() - timedelta(hours = 24*(i+1))
        allSpending = DisposalTransaction.query.filter(DisposalTransaction.user_id==user_id).filter(DisposalTransaction.datetime>=earlier).filter(DisposalTransaction.datetime<=later).all()
        s = sum([s.value for s in allSpending])
        spendingsPerDay.append(s)
    m["per_day"] = spendingsPerDay
    m["days"] = [str((datetime.utcnow()-timedelta(hours  = 24 * i)).date()) for i in range(30)]

    return json.dumps(m), 200

def get_total_waste_since(u_id, since):
    transactions = DisposalTransaction.query.filter(DisposalTransaction.user_id==u_id).filter(DisposalTransaction.datetime>=since).all()
    totals = sum([transaction.value for transaction in transactions])
    return totals

@app.route('/<user_id>/transactions/', methods=['GET'])
def transactions(user_id):
    allSpending = DisposalTransaction.query.filter(DisposalTransaction.user_id==user_id).all()
    a = [{"amount": s.value, "date": str(s.datetime), "category": s.category} for s in allSpending]
    return json.dumps({"transactions": a}), 200


@app.route('/<user_id>/category/<duration>', methods=['GET'])
def categories(user_id, duration):
    if duration not in ["week", "month", "day"]:
        duration = "day"
        print("You entered an invalid duration, setting to day")
    since = datetime.utcnow()-timedelta(hours = 1*24)
    if duration == "day":
        since = datetime.utcnow()-timedelta(hours = 1*24)
    if duration == "month":
        since = datetime.utcnow()-timedelta(hours = 30*24)
    if duration == "week":
        since = datetime.utcnow()-timedelta(hours = 7*24)
    unique_categories =DisposalTransaction.query.filter(DisposalTransaction.user_id==user_id).filter(DisposalTransaction.datetime>=since).distinct(DisposalTransaction.category).all()

    m = {}
    for item in unique_categories:
        cat = item.category
        items =DisposalTransaction.query.filter(DisposalTransaction.user_id==user_id).filter(DisposalTransaction.datetime>=since).filter(DisposalTransaction.category == cat).all()
        spending_sum = sum([item.value for item in items])
        m[cat] = spending_sum

    return json.dumps(m), 200

@app.route('/<user_id>/friends/<friend_name>', methods=['POST'])
def add_friend(user_id, friend_name):
    self = User.query.filter_by(id=user_id).first_or_404()
    friend = User.query.filter_by(facebook_name=friend_name).first_or_404()

    hasRelationship = Friendship.query.filter(Friendship.user_follower_id==self.id).filter(Friendship.user_followed_id==friend.id).all()
    if len(hasRelationship)>0:
        return "Already exists", 400
    relationship = Friendship(self, friend)
    db.session.add(relationship)
    db.session.commit()
    return "ok", 200

@app.route('/<user_id>/friends', methods=['GET'])
def get_friends(user_id):
    self = User.query.filter_by(id=user_id).first_or_404()
    friendships = Friendship.query.filter_by(user_follower_id=user_id).all()
    since = datetime.utcnow() - timedelta(hours=24)
    spendingToday = get_total_waste_since(user_id, since)
    friends = []
    for f in friendships:
        f_id = f.user_followed_id
        friendTransactionsToday = get_total_waste_since(f_id, since)
        name = User.query.filter_by(id=f_id).first_or_404().fb_name
        friends.append({"name": name, "spendings": friendTransactionsToday, "mineIsGreater": friendTransactionsToday < spendingToday})

    return json.dumps({"friends": friends}), 200


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
                        utils.send_message(messaging_event["sender"]["id"], "Pls no stickers. My master didn't teach me to handle 'em")
                        #Process image => not sticker
                    elif messaging_event["message"].get("attachments", [])[0].get("type", "") == "image":
                        process_image(messaging_event)
                    #Process location requests TODO
                    elif messaging_event["message"].get("attachments", [])[0].get("type", "") == "location":
                        process_location(messaging_event)
                except:
                    traceback.print_exc()

    return "ok", 200

#Temp stub until I get a real api 
def get_price(product_type):
    prices = {"laptop": 100, "iphone": 300, "phone": 150, "ipad": 300}
    return prices.get(product_type, 10)

def get_food_price(product_type):
    prices = {"banana": 1, "milk": 5, "cheese": 5, "orange": 1, "apple": 1, "peanut butter": 3,None: -1}
    return prices.get(product_type, 10)

def get_food_type(concepts):
    accepted_foods = ["banana", "orange", "apple", "milk", "cheese", "peanut butter"]
    for concept in concepts:
        if concept["name"] in accepted_foods:
            return concept["name"]

def suggest_kijiji(messaging_event):
    return ""

def save_trash_to_database(user, product_type, value):
    product = DisposalTransaction(user, value, product_type)
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

    utils.send_message(messaging_event["sender"]["id"], "You sent me {} and I think it is worth {}".format(product_type, value))
    save_trash_to_database(user, product_type, value)


    if (value >= 30):
        if (user.kijiji_email != "" and user.kijiji_email) and (user.kijiji_password and user.kijiji_password != ""):
            suggest_kijiji(messaging_event)
        else:
            m = {"message": "That looks valuable, you might want to list that on Kijiji...", "replies": [{"msg": "Yes", "payload": "YESLIST"},{"msg": "No", "payload": "NOLIST"}]}
            utils.send_message_quick_reply(user.fb_id, m)
    else:
        utils.send_message(user.fb_id, "Waste is now saved")

def get_user_or_signup(messaging_event):
    user = User.query.filter_by(fb_id=messaging_event["sender"]["id"]).first()
    if user == None:
        uid = messaging_event["sender"]["id"]
        name = utils.get_user_full_name(uid)
        user = User(uid, name)
        db.session.add(user)
        db.session.commit()
        utils.send_message(user.fb_id, "Thank you for signing up! You can now start sending me pictures of your trash")
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
        utils.send_message(user.fb_id, "And your Kijiji password is?")
        return
    elif past_state == "kijiji_password":
        user.command_in_progress = ""
        user.kijiji_password = message
        db.session.commit()
        utils.send_message(user.fb_id, "Done! Your Kijiji info is saved. You will now be prompted to list expensive products on Kijiji")
        return
    elif message == "Link Kijiji":
        utils.send_message(user.fb_id, "What is your kijiji email?")
        user.command_in_progress = "kijiji_username"
        db.session.commit()
        return
    elif "looking to buy" in message:
        msg = message.split("looking to buy")
        category = utils.get_product_category(msg[-1].strip())
        duration = datetime.utcnow() - timedelta(hours = 7 * 24)
        relevant_trans = DisposalTransaction.query.filter(DisposalTransaction.user_id==user.id).filter(DisposalTransaction.category==category).filter(DisposalTransaction.datetime >= duration).all()
        print(relevant_trans)
        total_spending = sum([trans.value for trans in relevant_trans])
        if total_spending >= 5:
            reply = "You might want to reconsider that decision"
        else:
            reply = "You are probably fine buying that :)"
        utils.send_message(user.fb_id, "You threw out ${} in the {} category last week. {}".format(total_spending, category, reply))


    #Retriving status Web UI links
    elif message == "Dashboard":
        utils.send_dashboard_link(user)
    #Branch for processing quick requests ie: summaryToday, etc

def process_location(messaging_event):
    user = get_user_or_signup(messaging_event)
    coord = messaging_event["message"].get("attachments", [])[0]["payload"]["coordinates"]
    lat = coord["lat"]
    lng = coord["long"]
    if (utils.is_near_store(lat, lng)):
        after_time = datetime.utcnow() - timedelta(hours = 30 * 24)
        transactions = DisposalTransaction.query.filter(DisposalTransaction.user_id==user.id).filter(DisposalTransaction.category!="electronics").filter(DisposalTransaction.datetime >=after_time).all()
        cats = {}
        for t in transactions:
            print(t.category, cats.get(t.category,0)+t.value)
            cats.update({t.category: cats.get(t.category, 0)+t.value}) 
        catsList = sorted(cats.items(), key = lambda c: c[1], reverse=True)
        top3Cats = catsList[:min(len(catsList), 3)]
        utils.send_message(user.fb_id, "During the next grocery trip, consider your top three waste categories in your last month")
        [utils.send_message(user.fb_id, "{}: ${}".format(c[0], c[1])) for c in top3Cats]


        




def process_wish_to_post(user):
    #if user.disposals[-1].wishtopost:
        #kijiji_post(item)
    return 

