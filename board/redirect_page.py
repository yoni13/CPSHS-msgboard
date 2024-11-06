'''
The modules that manages redirect page.
'''
import os
from flask import Blueprint, render_template, request, abort
import requests


redirect_page = Blueprint('redirect_page', __name__)


@redirect_page.route('/redirect')
def redirect_page_function():
    '''
    Redirect page.
    '''
    if request.headers.get('referer') is None:
        return abort(403)

    url = request.args.get('url')
    # google safe broswring api v4
    r_body =   {
    "client": {
      "clientId":      "cpshs-forum",
      "clientVersion": "1.0"
    },
    "threatInfo": {
      "threatTypes":      ["THREAT_TYPE_UNSPECIFIED","MALWARE", "SOCIAL_ENGINEERING","UNWANTED_SOFTWARE","POTENTIALLY_HARMFUL_APPLICATION"],
      "platformTypes":    ["ANY_PLATFORM"],
      "threatEntryTypes": ["URL","EXECUTABLE","THREAT_ENTRY_TYPE_UNSPECIFIED"],
      "threatEntries": [
        {"url": url}
          ]
        }
      }
    api_response = requests.post(f'https://safebrowsing.googleapis.com/v4/threatMatches:find?key={os.environ.get("GOOGLE_SAFE_BROSWERING_API_KEY")}',json=r_body,timeout=60)

    if api_response.status_code != 200:
        print('Error in google safe broswring api')
        print(api_response.json())
        return abort(500)
    if api_response.json().get('matches'):
        return render_template('unsafe_site_redirect.html',url=url)
    else:
        return render_template('redirect.html',url=url)
