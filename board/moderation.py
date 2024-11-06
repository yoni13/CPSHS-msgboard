'''
Module that controls moderation.
'''
from flask import Blueprint, render_template, abort, request, jsonify, Response,session, redirect
from app import db

mod = Blueprint('mod', __name__)


@mod.route('/mod')
def mod_():
    '''
    Main moderation page.
    '''
    user_info = session.get("user_info")
    if not user_info:
        return redirect('/login?after=mod')
    if user_info.get("priv") < 2:
        return Response("權限不足！")
    if request.method == "GET":
        messages = db.mb_message.find().sort({'_id':-1}).limit(10)

        resp_dict = []

        for document in messages:
            if '\n' in document.get("content"):
                content = document.get("content").replace("\n","<br>")
            else:
                content = document.get("content")

            resp_dict.append((document.get("uname"), document.get("pub_time"), content, document.get("post_id"), db.mb_replys.count_documents({"post_id": document.get("post_id")})))
        resp_messages = resp_dict

        return render_template("moderation.html", messages=resp_messages)

@mod.route('/mod/moderation_posts', methods=['GET', 'POST'])
def mod_post():
    '''
    Managing posts.
    '''
    user_info = session.get("user_info")
    if not user_info:
        return redirect('/login?after=mod')
    if user_info.get("priv") < 2:
        return Response("權限不足！")

    post_id = request.args.get("post_id")

    if request.method == "POST":
        if not post_id:
            abort(400)
        if request.json.get("action") == "hide":
            if user_info.get("priv") < 3:
                return jsonify({"err": 1, "desc": "權限不足！"})
            if db.mb_message.find_one({"post_id": post_id}).get("hidden"):
                db.mb_message.update_one({"post_id": post_id}, {"$set": {"hidden": False}})
                return jsonify({"err": 0, "desc": "已顯示！"})
            else:
                db.mb_message.update_one({"post_id": post_id}, {"$set": {"hidden": True}})
                return jsonify({"err": 0, "desc": "已隱藏！"})

        elif request.json.get("action") == "mark":
            if db.mb_message.find_one({"post_id": post_id}).get("might_fake"):
                db.mb_message.update_one({"post_id": post_id}, {"$set": {"might_fake": False}})
                return jsonify({"err": 0, "desc": "已取消標記！"})
            else:
                db.mb_message.update_one({"post_id": post_id}, {"$set": {"might_fake": True}})
                return jsonify({"err": 0, "desc": "已標記！"})


    if request.method == "GET":
        if not post_id:
            abort(400)
        messages = db.mb_message.find({"post_id": post_id})
        resp_dict = []

        for document in messages:
            if '\n' in document.get("content"):
                content = document.get("content").replace("\n","<br>")
            else:
                content = document.get("content")
            resp_dict.append((document.get("uname"), document.get("pub_time"), content))
        if not resp_dict:
            abort(400)

        resp_messages = resp_dict

        replys = db.mb_replys.find({"post_id": post_id})
        replys_dict = []

        for document in replys:

            if '\n' in document.get("content"):
                content = document.get("content").replace("\n","<br>")
            else:
                content = document.get("content")

            replys_dict.append((document.get("uname"), document.get("pub_time"), content,document.get('reply_id')))
        resp_replys = replys_dict

        return render_template("mod_posts.html", messages=resp_messages,replys=resp_replys)


@mod.route('/mod/moderation_replys', methods=['GET', 'POST'])
def mod_replys():
    '''
    Moderating replys.
    '''
    user_info = session.get("user_info")
    if not user_info:
        return redirect('/login?after=mod')
    if user_info.get("priv") < 2:
        return Response("權限不足！")

    reply_id = request.args.get("reply_id")

    if request.method == "POST":
        if not reply_id:
            abort(400)
        if request.json.get("action") == "hide":
            if user_info.get("priv") < 3:
                return jsonify({"err": 1, "desc": "權限不足！"})
            if db.mb_replys.find_one({"reply_id": reply_id}).get("hidden"):
                db.mb_replys.update_one({"reply_id": reply_id}, {"$set": {"hidden": False}})
                return jsonify({"err": 0, "desc": "已顯示！"})
            else:
                db.mb_replys.update_one({"reply_id": reply_id}, {"$set": {"hidden": True}})
                return jsonify({"err": 0, "desc": "已隱藏！"})

        elif request.json.get("action") == "mark":
            if db.mb_replys.find_one({"reply_id": reply_id}).get("might_fake"):
                db.mb_replys.update_one({"reply_id": reply_id}, {"$set": {"might_fake": False}})
                return jsonify({"err": 0, "desc": "已取消標記！"})
            else:
                db.mb_replys.update_one({"reply_id": reply_id}, {"$set": {"might_fake": True}})
                return jsonify({"err": 0, "desc": "已標記！"})


    if request.method == "GET":
        if not reply_id:
            abort(400)
        messages = db.mb_replys.find({"reply_id": reply_id})
        resp_dict = []

        for document in messages:
            if '\n' in document.get("content"):
                content = document.get("content").replace("\n","<br>")
            else:
                content = document.get("content")
            resp_dict.append((document.get("uname"), document.get("pub_time"), content))
        if not resp_dict:
            abort(400)

        resp_messages = resp_dict
        return render_template("mod_replys.html", replys=resp_messages)
