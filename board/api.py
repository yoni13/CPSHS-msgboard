'''
The module that manages api.
'''
import time
import random
import re
from flask import Blueprint, abort, request, jsonify, session
from flask_mail import Message
from app import db, limiter, mail
import little_conponment

api = Blueprint('api', __name__)


@api.route('/api/v1/')
def index():
    '''
    This is the msg board API v1
    '''
    return 'This is the msg board API v1'


@api.route('/api/v1/mb_board/')
def mb_board():
    '''
    Api for getting main board
    '''
    if session.get("user_info"):
        logined = True
    else:
        logined = False

    if request.args.get('limit'):
        if not request.args.get('limit').isdigit():
            return abort(400, 'limit must be a number')
        limit = request.args.get('limit')
    else:
        limit = 10

    if request.args.get('page'):
        if not request.args.get('page').isdigit():
            return abort(400, 'page must be a number')
        page = int(request.args.get('page'))
    else:
        page = 1


    datas = db.mb_message.find().sort({'_id':-1}).limit(limit).skip((page-1)*limit)
    res = []
    for data in datas:
        replys_count = db.mb_replys.count_documents({"post_id": data['post_id']})
        if data['hidden']:
            content = '此留言已被隱藏'
        else:
            content = little_conponment.markdown_to_html_secure(data['content'])

        info = {'uname': data['uname'], 'content': content, 'pub_time': data['pub_time'], 'post_id': data['post_id'], 'replys_count': replys_count,'might_fake': data['might_fake'],'hidden': data['hidden'],'like':db.mb_reaction.count_documents({"post_id": data['post_id'], "reaction": "like"}),'dislike':db.mb_reaction.count_documents({"post_id": data['post_id'], "reaction": "dislike"}),'laugh':db.mb_reaction.count_documents({"post_id": data['post_id'], "reaction": "laugh"}),'login':logined}
        res.append(info)

    if request.args.get('reverse') == '1':
        res = list(res)
    else:
        res = list(reversed(res))

    return jsonify(res)

@api.route('/api/v1/mb_replys/')
def mb_board_post():
    '''
    Api for getting reply data.
    '''
    post_id = request.args.get('post_id')
    if not post_id:
        return jsonify({"error": "post_id is required"}), 400

    if request.args.get('limit'):
        if not request.args.get('limit').isdigit():
            return jsonify({"error": "limit must be a number"}), 400

        limit = int(request.args.get('limit'))
    else:
        limit = 10

    if request.args.get('page'):
        if not request.args.get('page').isdigit():
            return jsonify({"error": "page must be a number"}), 400
        page = int(request.args.get('page'))
    else:
        page = 1

    data = db.mb_message.find_one({'post_id': post_id})
    if data:
        res = {'post':
               {'uname': data['uname'], 'content': data['content'], 'pub_time': data['pub_time'], 'post_id': data['post_id']}
                }
        replysres = []

        replys = db.mb_replys.find({'post_id': post_id}).limit(limit).skip((page-1)*limit)
        for reply in replys:
            if reply['hidden']:
                content = '此留言已被隱藏'
            else:
                content = little_conponment.markdown_to_html_secure(reply['content'])

            replydata = {'uname': reply['uname'], 'content': content, 'pub_time': reply['pub_time']}
            replysres.append(replydata)
        res['replys'] = replysres
        if request.args.get('reverse') == '1':
            res['replys'] = list(reversed(res['replys']))
        return jsonify(res)
    else:
        return abort(400)

@api.route('/api/v1/send_email_code', methods=['POST'])
@limiter.limit("1/second")
def send_email_code():
    '''
    This api send email code

    {"email":email}
    '''
    email = request.json.get('email')
    if not email:
        return jsonify({"err": 1, "desc": "請輸入信箱！"})

    if not re.fullmatch(r"[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+", email):
        return jsonify({"err": 1, "desc": "信箱格式錯誤！"})

    if db.mb_user.find_one({"email": email}):
        return jsonify({"err": 1, "desc": "信箱已被註冊！"})

    code = random.randint(100000, 999999)
    if db.reg_code.find_one({"email":email}):
        db.reg_code.delete_one({"email":email})
    db.reg_code.insert_one({
    "email":email,
    "reg_code":str(code),
    "send_time":time.time()
    })
    msg = Message('SGGS ANON 驗證碼', recipients=[email])
    msg.body = '您的驗證碼是：' + str(code) +'，有效期為5分鐘。'
    mail.send(msg)
    return jsonify({"err": 0, "desc": "驗證碼已發送！"})

@api.route('/api/v1/reaction', methods=['POST'])
@limiter.limit("5/second")
def reaction_api():
    '''
    Reaction api for posts.
    '''
    post_id = request.json.get('post_id')
    reaction = request.json.get('reaction')

    user_info = session.get("user_info")

    if not user_info:
        return jsonify({"err": 1, "desc": "請先登入！"})

    if not post_id or not reaction:
        return jsonify({"err": 1, "desc": "post_id and reaction is required!"})

    if reaction not in ['like', 'dislike','laugh']:
        return jsonify({"err": 1, "desc": "reaction must one of like, dislike, laugh"})

    if not db.mb_message.find_one({"post_id": post_id}):
        return jsonify({"err": 1, "desc": "post_id not exist!"})


    if db.mb_reaction.find_one({"post_id": post_id, "uname": user_info['uname']}):
        try:
            if reaction == db.mb_reaction.find_one({"post_id": post_id, "uname": user_info['uname'], "reaction": reaction})['reaction']:
                db.mb_reaction.delete_one({"post_id": post_id, "uname": user_info['uname'], "reaction": reaction})
        except TypeError: # user reacted to other emotes before
            db.mb_reaction.update_one({"post_id": post_id, "uname": user_info['uname']}, {"$set": {"reaction": reaction}})

    else:
        db.mb_reaction.insert_one({"post_id": post_id, "uname": user_info['uname'], "reaction": reaction})

    reactions = []
    for i in ['like', 'dislike', 'laugh']:
        reactions.append(db.mb_reaction.count_documents({"post_id": post_id, "reaction": i}))

    return jsonify({"err": 0, "desc": "success", "reaction": reactions})
