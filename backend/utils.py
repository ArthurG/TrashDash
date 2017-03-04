import keys

import requests
import json

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
                      "url": "http://localhost:8080/#/dashboard/{}".format(user.id),
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

