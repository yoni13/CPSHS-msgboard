'''
Main control for entire app.
'''
import os
from flask import Flask, request
from flask_mail import Mail
from pymongo import MongoClient
from flask_limiter import Limiter
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = os.environ['app_secret_key']
app.config['CSRF_SECRET_KEY'] = os.urandom(24)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
csrf = CSRFProtect(app)

def get_remote_address():
    '''
    Get real user ip instead of cloudflare's ip
    '''
    if request.headers.get('cf-connecting-ip'):
        return request.headers.get('cf-connecting-ip')
    else:
        return request.remote_addr


limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


client = MongoClient(os.environ['DATABASE_URL'])
db = client["message"]



app.config.update(
    DEBUG=False,
    MAIL_SERVER=os.environ['MAIL_SERVER'],
    MAIL_PORT=587,
    MAIL_USE_SSL=False,
    MAIL_DEFAULT_SENDER=('admin', os.environ['MAIL_DEFAULT_SENDER']),
    MAIL_MAX_EMAILS=10,
    MAIL_USERNAME=os.environ['MAIL_USERNAME'],
    MAIL_PASSWORD=os.environ['email_key']
)
mail = Mail(app)

if not os.path.isdir("tmp"):
    os.mkdir("tmp")

# DISCORD
OAUTH2_CLIENT_ID = os.environ['DISCORD_OAUTH_CLIENT_ID']  # Your CLIENT ID
OAUTH2_CLIENT_SECRET = os.environ['DISCORD_OAUTH_CLIENT_SECURITE']  # Your CLIENT SECRET
REDIRECT_URI = os.environ['DISCORD_OAUTH_REDIRECT_URL']

AUTHORIZE_URL = os.environ['DISCORD_OAUTH_AUTH_URL']
TOKEN_URL = 'https://discord.com/api/oauth2/token'
API_URL_BASE = 'https://discord.com/api/users/@me'


from board import api, moderation, static_files, frontend, opengraph, redirect_page, discordoauth

app.register_blueprint(api.api)
app.register_blueprint(moderation.mod)
app.register_blueprint(static_files.static_files)
app.register_blueprint(frontend.frontend)
app.register_blueprint(opengraph.opengraph)
app.register_blueprint(redirect_page.redirect_page)
app.register_blueprint(discordoauth.discordoauth)


if __name__ == "__main__":
    app.run(port=8080, debug=True, host='0.0.0.0')
