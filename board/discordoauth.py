'''
Module that controls Discord Oauth.
'''
from flask import Blueprint, redirect, request, session
import requests, datetime, random
from app import OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET, REDIRECT_URI, TOKEN_URL, API_URL_BASE
from app import db

discordoauth = Blueprint('discordoauth', __name__)

@discordoauth.route('/auth/discord/callback')
def discord_callback():
    if session.get("user_info"):
        return redirect('/message_board')
    
    code = request.args.get('code')
    data = {
        'client_id': OAUTH2_CLIENT_ID,
        'client_secret': OAUTH2_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(TOKEN_URL, data=data, headers=headers)
    try:
        access_token = response.json()['access_token']
    except KeyError:
        return "<script>alert('Erorr while trying to get userdata, perhaps try again?');history.back();</script>"
    headers = {
        'Authorization': f"Bearer {access_token}",
        'Accept': 'application/json',
    }
    getdata = requests.get(API_URL_BASE, headers=headers).json()
    
    if not getdata['verified']:
        return "<script>alert('Please verify your discord mail address in the discord app.');history.back();</script>"
    
    if db.mb_user.find_one({"email": getdata['email']}):
        dbres = db.mb_user.find_one({"email": getdata['email']})
        session["user_info"] = {
                    "uname": dbres.get("uname"),
                    "email": dbres.get("email"),
                    "priv": dbres.get("priv"),
                    "state": dbres.get("state"),
                    "current_login_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
        db.mb_user.update_one({"email": getdata['email']}, {"$set": {"last_login_time": datetime.datetime.now()}})

        return redirect('/message_board')

    else:
        uname = getdata['global_name']

        if db.mb_user.find_one({"uname": uname}): # if name in discord already exists in db, we use the name before mail.
            uname = getdata['email'].split("@")[0]

        while (db.mb_user.find_one({"uname": uname})): # if still exists, that the magics happen.
            uname = getdata['global_name'] + str(random.randrange(1000,9999))

        db.mb_user.insert_one({
                "uname": uname,
                "upass": None,
                "email": getdata['email'],
                "reg_time": datetime.datetime.now(),
                "last_login_time": datetime.datetime.now(),
                "priv": 1, # 1: user, 2: admin(mark as might be fake post&comments), 3: super admin (hide&mark)
                "state": 1, # 1: normal, 2: banned,
                "usingOauth":True # if using oauth,disable login via password
            })
        session["user_info"] = {
                    "uname": uname,
                    "email": getdata['email'],
                    "priv": 1,
                    "state": 1,
                    "current_login_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
        return redirect('/message_board')

