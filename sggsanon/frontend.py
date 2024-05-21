from flask import Blueprint, redirect, request, render_template,abort, Response, session, url_for
import time
import re
import hashlib
import datetime
from app import get_mail, limiter
from app import db
from markupsafe import escape
import little_conponment

mail = get_mail()
limiter = limiter


frontend = Blueprint('frontend', __name__)

@frontend.route("/")
def index():
    return redirect('/message_board')


@frontend.route("/reg", methods=["GET", "POST"])
def reg_handle():
    if request.method == "GET":
        if session.get("user_info"):
            return redirect(url_for("message_board_handle"))
        return render_template("reg.html")
    elif request.method == "POST":
        uname = request.form.get("uname")
        upass = request.form.get("upass")
        upass2 = request.form.get("upass2")
        verify_code = request.form.get("verify_code")
        email = request.form.get("email")

        if not (uname and uname.strip() and upass and upass2 and verify_code and email):
            abort(400)
        if not db.reg_code.find_one({"email":email,"reg_code":verify_code}):
            abort(Response("驗證碼錯誤!"))

        # Verify time
        if time.time() - db.reg_code.find_one({"email":email,"reg_code":verify_code})["send_time"] > 300: # 5 minutes
            db.reg_code.delete_one({"email":email,"reg_code":verify_code})
            abort(Response("驗證碼已過期!"))

        if re.search(r"[\u4E00-\u9FFF]", uname):
            abort(Response("中文名稱請使用英文名稱！"))

        if not re.fullmatch("[a-zA-Z0-9_]{4,20}", uname):
            abort(Response("帳號名稱請介於4-20個字，且僅接受英文、數字、和底線"))

        cur = db.mb_user.find_one({"uname": uname})
        if cur:
            abort(Response("名子已被註冊！"))
        findemail = db.mb_user.find_one({"email": email})
        if findemail:
            abort(Response("信箱已被註冊！"))

        if not upass == upass2:
            abort(Response("密碼錯誤！"))

        if len(upass) < 6:
            abort(Response("密碼長度需大於6！"))
        
        if len(upass) > 20:
            abort(Response("密碼長度需小於20！"))

        if not re.fullmatch(r"[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+", email):
            abort(Response("信箱格式錯誤！"))

        try:
            db.mb_user.insert_one({
                "uname": uname,
                "upass": hashlib.md5(upass.encode()).hexdigest(),
                "email": email,
                "reg_time": datetime.datetime.now(),
                "last_login_time": datetime.datetime.now(),
                "priv": 1, # 1: user, 2: admin(mark as might be fake post&comments), 3: super admin (hide&mark)
                "state": 1 # 1: normal, 2: banned
            })
            db.reg_code.delete_one({"email":email,
                "reg_code":verify_code})
        except:
            abort(Response("註冊失敗！"))

        return redirect('/login?reg=1')


@frontend.route("/logout")
def logout_handle():
    if session.get("user_info"):
        session.pop("user_info")
    return redirect('/login')


@frontend.route("/post_anonymous", methods=["GET", "POST"])
def post_anonymous_handle():
    if request.method == "GET":
        return render_template("post_anonymous.html")
    elif request.method == "POST":
        user_info = session.get("user_info")
        if not user_info:
            real_uname = None
        else:
            real_uname = user_info.get("uname")
        content = request.form.get("content")

        if content:
            content = escape(content.strip())
            if 0 < len(content) <= 200:
                db.mb_message.insert_one({
                    "uname": "匿名",
                    "content": content,
                    "pub_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "post_id": little_conponment.generate_random_string(10) + 'anonymous',
                    "real_uname": real_uname,
                    "hidden": False,
                    "might_fake": False
                })
                return redirect('/message_board')
        else:
            abort(Response('留言不能為空'))

@frontend.route("/message_board", methods=["GET", "POST"])
def message_board_handle():
    if request.method == "GET":
        messages = db.mb_message.find().sort({'_id':-1}).limit(10)
        
        resp_dict = []

        for document in messages:
            if '\n' in document.get("content"):
                content = document.get("content").replace("\n","<br>")
            else:
                content = document.get("content")

            if document.get("hidden") == True:
                content = "此留言已被隱藏"

            resp_dict.append((document.get("uname"), document.get("pub_time"), content, document.get("post_id"), db.mb_replys.count_documents({"post_id": document.get("post_id")}), document.get("might_fake")))
        resp_messages = resp_dict

        return render_template("message_board.html", messages=resp_messages)
    elif request.method == "POST":
        user_info = session.get("user_info")
        if not user_info:
            abort(Response("請先登入！"))

        content = request.form.get("content")
        if content:
            content = escape(content.strip())
            if 0 < len(content) <= 200:
                post_id = little_conponment.generate_random_string(10)
                if db.mb_message.find_one({"post_id": post_id}):
                    post_id = little_conponment.generate_random_string(10)
                db.mb_message.insert_one({
                    "uname": user_info.get("uname"),
                    "content": content,
                    "pub_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "post_id": post_id,
                    "hidden": False,
                    "might_fake": False
                })
                return redirect('/message_board')
            else:
                abort(Response("留言內容長度需在1-200字之間！"))
        else:
            abort(Response("留言內容不能為空！"))


@frontend.route('/messages_replys', methods=['GET', 'POST'])
def messages_replys():
    if request.method == "GET":
        post_id = request.args.get("post_id")
        if not post_id:
            abort(400)
        messages = db.mb_message.find({"post_id": post_id})
        resp_dict = []

        for document in messages:
            if '\n' in document.get("content"):
                content = document.get("content").replace("\n","<br>")
            else:
                content = document.get("content")
            
            if document.get("hidden") == True:
                content = "此留言已被隱藏"

            resp_dict.append((document.get("uname"), document.get("pub_time"), content,document.get("might_fake")))
        if resp_dict == []:
            abort(400)

        resp_messages = resp_dict

        replys = db.mb_replys.find({"post_id": post_id})
        replys_dict = []

        for document in replys:

            if '\n' in document.get("content"):
                content = document.get("content").replace("\n","<br>")
            else:
                content = document.get("content")

            replys_dict.append((document.get("uname"), document.get("pub_time"), content, document.get("might_fake")))
        resp_replys = replys_dict

        return render_template("replys.html", messages=resp_messages,replys=resp_replys)
    elif request.method == "POST":
        user_info = session.get("user_info")
        if not user_info:
            abort(Response("請先登入！"))

        content = request.form.get("content")
        post_id = request.args.get("post_id")
        if content and post_id:
            content = escape(content.strip())
            if request.headers.get('cf-connecting-ip') == None:
                ip = request.remote_addr
            else:
                ip = request.headers.get('cf-connecting-ip') # cloudflare

            if user_info.get("uname") == db.mb_message.find_one({"post_id": post_id}).get("real_uname"):
                uname = "匿名"
            else:
                uname = user_info.get("uname")

            if 0 < len(content) <= 200:
                db.mb_replys.insert_one({
                    "uname": uname,
                    "content": content,
                    "pub_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "ip": ip,
                    "post_id": post_id,
                    "hidden": False,
                    "might_fake": False,
                    "reply_id": little_conponment.generate_random_string(10) + "reply" + post_id
                })
                return redirect(url_for("messages_replys", post_id=post_id))
            else:
                abort(Response("回覆內容長度需在1-200字之間！"))
        else:
            abort(Response("回覆內容不能為空！"))

@frontend.route("/login", methods=["GET", "POST"])
def login_handle():
    if request.method == "GET":
        if session.get("user_info"):
            return redirect('/message_board')
        return Response(render_template("login.html") + "<script>if (location.search == '?reg=1') {alert('註冊成功！')}</script>")
    elif request.method == "POST":
        upass = request.form.get("upass")
        uname = request.form.get("uname")

        if not (upass and uname):
            abort(400)

        try:
            dbres = db.mb_user.find_one({
                "upass": hashlib.md5(upass.encode()).hexdigest(),
                "uname": uname,
            })
            if dbres:
                session["user_info"] = {
                    "uid": dbres.get("uid"),
                    "uname": dbres.get("uname"),
                    "email": dbres.get("email"),
                    "reg_time": dbres.get("reg_time"),
                    "last_login_time": dbres.get("last_login_time"),
                    "priv": dbres.get("priv"),
                    "state": dbres.get("state"),
                    "current_login_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                db.mb_user.update_one({"uname": uname}, {"$set": {"last_login_time": datetime.datetime.now()}})
            else:
                abort(Response("login失敗！"))
        except:
            abort(Response("login失敗！"))

        return redirect('/message_board')