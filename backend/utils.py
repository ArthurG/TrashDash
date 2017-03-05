import keys

import requests
import json
from textblob import Word

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
                      "url": "https://707a979a.ngrok.io/#/dashboard/{}".format(user.id),
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
    url = "https://graph.facebook.com/v2.6/{}?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token={}".format(uid, keys.ACCESS_TOKEN)
    r = requests.get(url)
    response = r.json()
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)
    return response["first_name"] + " " + response["last_name"]

def get_product_category(name):
    pl = Word(name).pluralize().lower()
    f = open('category_mapping.txt', 'r')
    for line in f:
        if line.split(',')[0] == name or line.split(',')[0] == pl:
            return line.split(',')[1].strip()
    return name

def is_near_store(lat, lng, category="store",keyword="grocery",radius=100):
    endpoint = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
            "location": "{},{}".format(lat, lng),
            "radius": radius,
            "type": category,
            "key": keys.google_maps,
            "keyword": keyword
            }
    r = requests.get(endpoint, params=params)
    return len(r.json()["results"]) > 0
    
def get_kijiji_data(title, description, price, product_name):
    m = {"postAdForm.attributeMap[forsaleby_s]": "ownr", "postAdForm.priceAmount": price,"postAdForm.priceType": "FIXED", "featuresForm.topAdDuration": "7", "postAdForm.title": title, "postAdForm.locationId": "1700212", "postAdForm.city": "Waterloo", "postAdForm.province": "ON", "postAdForm.description": description, "submitType": "saveAndCheckout", "locationLevel0": "1700209", "postAdForm.geocodeLng": "-80.5980028", "postAdForm.postalCode": "N2V 2W6", "postAdForm.adType": "OFFER", "postAdForm.geocodeLat": "43.472549", "PostalLng": "-80.5980028", "PostalLat": "43.472549"} 
    if product_name == "laptop":
        m["postAdForm.attributeMap[laptopscreensize_s]"] = "laptopunder14inch"
        m["postAdForm.attributeMap[laptopbrand_s]"] = "laptoplenovo"
        m["categoryId"] = "773"
    elif product_name == "iphone" or product_name == "phone":
        m["categoryId"] = "760"
        m["postAdForm.attributeMap[phonebrand_s]"]="apple"
        m["postAdForm.attributeMap[phonecarrier_s]"]="other"
    print(m)
    return m
