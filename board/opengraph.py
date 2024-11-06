'''
Modules that manages opengraph.
'''
import os
from flask import Blueprint, request, abort, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
import little_conponment

from app import db, limiter

opengraph = Blueprint('opengraph', __name__)

@opengraph.route('/opengraph')
@limiter.limit("1 per second")
def og():
    '''
    Api for opengraph.
    '''
    if not request.args.get('post_id'):
        abort(400)

    post_id = request.args.get('post_id')

    if not db.mb_message.find_one({"post_id": post_id}):
        abort(404)


    if os.path.isfile("tmp/"+post_id+".png"):
        return send_from_directory("tmp", post_id+".png")

    post = db.mb_message.find_one({"post_id": post_id})

    uname = post['uname']
    pub_time = post['pub_time']

    content = BeautifulSoup(little_conponment.markdown_to_html_secure(post['content'],True), "html.parser").getText()

    if len(content) > 30:
        content = content[:30] + ' ...'

    if post['hidden']:
        content = '此留言已被隱藏'
    like_count = db.mb_reaction.count_documents({'post_id': post_id, 'reaction': 'like'})
    dislike_count = db.mb_reaction.count_documents({'post_id': post_id, 'reaction': 'dislike'})
    laugh_count = db.mb_reaction.count_documents({'post_id': post_id, 'reaction': 'laugh'})

    img = Image.open("static/img/opengraph.png")

    draw = ImageDraw.Draw(img)
    # font = ImageFont.truetype(<font-file>, <font-size>)
    font = ImageFont.truetype("ChocolateClassicalSans-Regular.ttf", 60)
    # draw.text((x, y),"Sample Text",(r,g,b))
    draw.text((243, 120),uname,(255,255,255),font=font)

    font = ImageFont.truetype("ChocolateClassicalSans-Regular.ttf", 40)
    draw.text((100, 230),pub_time,(175,175,175),font=font)

    font = ImageFont.truetype("ChocolateClassicalSans-Regular.ttf", 40)
    draw.text((100, 300),content,(255,255,255),font=font)

    font = ImageFont.truetype("ChocolateClassicalSans-Regular.ttf", 50)
    draw.text((190, 440),str(like_count),(172,172,172),font=font)

    font = ImageFont.truetype("ChocolateClassicalSans-Regular.ttf", 50)
    draw.text((320, 440),str(dislike_count),(172,172,172),font=font)

    font = ImageFont.truetype("ChocolateClassicalSans-Regular.ttf", 50)
    draw.text((450, 440),str(laugh_count),(172,172,172),font=font)

    current_path = os.getcwd()
    imgname = post_id+ '.png'
    img.save(current_path+"/tmp/"+imgname)
    return send_from_directory(current_path+"/tmp/", imgname)

@opengraph.route('/oembedapi')
def oembedapi():
    '''
    Api gathering ombed.
    '''
    if not request.args.get('post_id'):
        abort(400)
    post = db.mb_message.find_one({"post_id": request.args.get('post_id')})

    content = BeautifulSoup(little_conponment.markdown_to_html_secure(post['content']), "html.parser").getText()

    if len(content) > 20:
        title = post['uname'] + ' 說:' + content[:20] + '...'
    else:
        title = post['uname'] + ' 說:' + content

    json_template = {
        "author_name":  title,
        "author_url": "https://"+request.host,
        "provider_name": post['uname'] ,
        "provider_url": "https://"+request.host+"/opengraph?post_id="+request.args.get('post_id'),
        "type": "photo"
    }
    return json_template
