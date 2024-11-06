'''
Module that manages static files.
'''
from flask import Blueprint, render_template,redirect,request


static_files = Blueprint('static_files', __name__)

@static_files.route('/policy')
def tos():
    '''
    TOS page.
    '''
    return render_template('policy.html')

@static_files.route('/favicon.ico')
def favicon():
    '''
    Favicon.ico
    '''
    return redirect('/static/img/logo.png')

@static_files.route('/robots.txt')
def robots():
    '''
    robots.txt
    '''
    # if request.host == 'indev-sggsanon.nicewhite.xyz':
    return redirect('/static/robots_dev.txt')
    # if request.host == 'sggsanon.nicewhite.xyz':
    #     return redirect('/static/robots_prod.txt')
    # else:
    #     return '',403
