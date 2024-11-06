'''
The module that manages frontend.
'''
import time
import re
import hashlib
import datetime
import markdown
from bs4 import BeautifulSoup
from flask import Blueprint, redirect, request, render_template,abort, Response, session
from markupsafe import escape
from app import limiter, db
import little_conponment


frontend = Blueprint('frontend', __name__)

@frontend.route("/reg", methods=["GET", "POST"])
@limiter.limit("5 per minute",methods=["POST"])
def reg_handle():
    '''
    Register page.
    '''
    if request.method == "GET":
        if session.get("user_info"):
            return redirect('/message_board')
        return render_template("reg.html")
    elif request.method == "POST":
        uname = request.form.get("uname")
        upass = request.form.get("upass")
        upass2 = request.form.get("upass2")
        verify_code = request.form.get("verify_code")
        email = request.form.get("email")

        if not (uname and uname.strip() and upass and upass2 and verify_code and email):
            return '<script>alert("請填寫完整！");history.back();</script>'
        if not db.reg_code.find_one({"email":email,"reg_code":verify_code}):
            return '<script>alert("驗證碼錯誤!");history.back();</script>'

        # Verify time
        if time.time() - db.reg_code.find_one({"email":email,"reg_code":verify_code})["send_time"] > 300: # 5 minutes
            db.reg_code.delete_one({"email":email,"reg_code":verify_code})
            return '<script>alert("驗證碼已過期!");history.back();</script>'

        if re.search(r"[\u4E00-\u9FFF]", uname):
            return '<script>alert("請使用英文名稱！");history.back();</script>'

        if not re.fullmatch("[a-zA-Z0-9_]{4,20}", uname):
            return '<script>alert("帳號名稱請介於4-20個字，且僅接受英文、數字、和底線");history.back();</script>'

        cur = db.mb_user.find_one({"uname": uname})
        if cur:
            return '<script>alert("名子被別人使用！");history.back();</script>'
        findemail = db.mb_user.find_one({"email": email})
        if findemail:
            return '<script>alert("信箱已被註冊！");history.back();</script>'

        if not upass == upass2:
            return '<script>alert("密碼錯誤！");history.back();</script>'

        if len(upass) < 6:
            return '<script>alert("密碼長度需大於6！");history.back();</script>'

        if len(upass) > 20:
            return '<script>alert("密碼長度需小於20！");history.back();</script>'

        if not re.fullmatch(r"[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+", email):
            return '<script>alert("信箱格式錯誤！");history.back();</script>'

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
            return '<script>alert("註冊失敗！");history.back();</script>'

        return redirect('/login?reg=1')


@frontend.route("/logout")
def logout_handle():
    '''
    Logout page.
    '''
    if session.get("user_info"):
        session.pop("user_info")
    return redirect('/login')


@frontend.route("/post_anonymous", methods=["GET", "POST"])
@limiter.limit("2 per hour",methods=["POST"])
def post_anonymous_handle():
    '''
    Page that allows anyone to post anonymously.
    '''
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
                return '<script>alert("留言不能大於200字或沒有字！");history.back();</script>'
        else:
            return '<script>alert("留言不能為空！");history.back();</script>'

@frontend.route("/message_board", methods=["GET", "POST"])
@limiter.limit("1 per minute",methods=["POST"])
def message_board_handle():
    '''
    Main page.
    '''
    if request.method == "GET":
        messages = db.mb_message.find().sort({'_id':-1}).limit(10)

        resp_dict = []

        for document in messages:
            content = document.get("content")
            content = little_conponment.markdown_to_html_secure(content)

            if document.get("hidden"):
                content = "此留言已被隱藏"

            like_count = db.mb_reaction.count_documents({"post_id": document.get("post_id"),'reaction':'like'})
            dislike_count = db.mb_reaction.count_documents({"post_id": document.get("post_id"),'reaction':'dislike'})
            laugh_count = db.mb_reaction.count_documents({"post_id": document.get("post_id"),'reaction':'laugh'})

            resp_dict.append((document.get("uname"), document.get("pub_time"), content, document.get("post_id"), db.mb_replys.count_documents({"post_id": document.get("post_id")}), document.get("might_fake"),document.get("hidden"),like_count,dislike_count,laugh_count))
        resp_messages = resp_dict

        return render_template("message_board.html", messages=resp_messages)
    elif request.method == "POST":
        user_info = session.get("user_info")
        if not user_info:
            return '<script>alert("請先登入！");location.href="/login?after=message_board";</script>'

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
                return '<script>alert("留言內容長度需在1-200字之間！");history.back();</script>'
        else:
            return '<script>alert("留言內容不能為空！");history.back();</script>'


@frontend.route('/messages_replys', methods=['GET', 'POST'])
@limiter.limit("5 per minute",methods=["POST"])
def messages_replys():
    '''
    Reply message page.
    '''
    if request.method == "GET":
        post_id = request.args.get("post_id")
        if not post_id:
            abort(400)
        messages = db.mb_message.find({"post_id": post_id})
        resp_dict = []

        for document in messages:
            content = document.get("content")
            content = little_conponment.markdown_to_html_secure(content)

            if document.get("hidden"):
                content = "此留言已被隱藏"

            like_count = db.mb_reaction.count_documents({"post_id": document.get("post_id"),'reaction':'like'})
            dislike_count = db.mb_reaction.count_documents({"post_id": document.get("post_id"),'reaction':'dislike'})
            laugh_count = db.mb_reaction.count_documents({"post_id": document.get("post_id"),'reaction':'laugh'})

            markdown_html_text = BeautifulSoup(markdown.markdown(document.get('content')), "html.parser").getText()

            if len(markdown_html_text) > 20:
                title = document.get('uname') + ' 說:' + markdown_html_text[:20] + '...'
            else:
                title = document.get('uname') + ' 說:' + markdown_html_text

            if document.get('hidden'):
                title = '此留言已被隱藏'

            resp_dict.append((document.get("uname"), document.get("pub_time"), content,document.get("might_fake"),document.get("hidden"),like_count,dislike_count,laugh_count,document.get("post_id"),title))
        if not resp_dict:
            abort(404)

        resp_messages = resp_dict

        replys = db.mb_replys.find({"post_id": post_id})
        replys_dict = []

        for document in replys:
            content = document.get("content")
            content = little_conponment.markdown_to_html_secure(content)

            if document.get("hidden"):
                content = "此回覆已被隱藏"

            replys_dict.append((document.get("uname"), document.get("pub_time"), content, document.get("might_fake"), document.get("hidden")))
        resp_replys = replys_dict

        return render_template("replys.html", messages=resp_messages,replys=resp_replys,title=title,post_id=post_id)
    elif request.method == "POST":
        user_info = session.get("user_info")
        if not user_info:
            return '<script>alert("請先登入！");location.href="/login?after=messages_replys&post_id='+request.args.get('post_id')+'";</script>'

        content = request.form.get("content")
        post_id = request.args.get("post_id")
        if content and post_id:
            content = escape(content.strip())

            if user_info.get("uname") == db.mb_message.find_one({"post_id": post_id}).get("real_uname"):
                uname = "匿名"
            else:
                uname = user_info.get("uname")

            if 0 < len(content) <= 200:
                db.mb_replys.insert_one({
                    "uname": uname,
                    "content": content,
                    "pub_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "post_id": post_id,
                    "hidden": False,
                    "might_fake": False,
                    "reply_id": little_conponment.generate_random_string(10) + "reply" + post_id
                })
                return redirect("/messages_replys?post_id=" + post_id)
            else:
                return '<script>alert("回覆內容長度需在1-200字之間！");history.back();</script>'
        else:
            return '<script>alert("回覆內容不能為空！");history.back();</script>'

@frontend.route("/login", methods=["GET", "POST"])
def login_handle():
    '''
    Login page.
    '''
    if request.method == "GET":
        if session.get("user_info"):
            if request.args.get("after"):
                if request.args.get("after") == "message_board":
                    return redirect('/message_board')
                elif request.args.get("after") == "messages_replys":
                    return redirect('/messages_replys?post_id=' + request.args.get("post_id"))
                elif request.args.get("after") == "mod":
                    return redirect('/mod')
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
                    "uname": dbres.get("uname"),
                    "email": dbres.get("email"),
                    "priv": dbres.get("priv"),
                    "state": dbres.get("state"),
                    "current_login_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                db.mb_user.update_one({"uname": uname}, {"$set": {"last_login_time": datetime.datetime.now()}})
            else:
                return '<script>alert("登入失敗！");history.back();</script>'
        except:
            return '<script>alert("登入失敗！");history.back();</script>'
        if request.args.get("after"):
            if request.args.get("after") == "message_board":
                return redirect('/message_board')
            elif request.args.get("after") == "messages_replys":
                return redirect('/messages_replys?post_id=' + request.args.get("post_id"))
            elif request.args.get("after") == "mod":
                return redirect('/mod')

        return redirect('/message_board')


@frontend.route('/')
def root():
    '''
    Root route.
    '''
    return render_template('root.html')
