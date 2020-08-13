import base64
import os
import json
import logging
import datetime

from flask import Flask, request, session, render_template, url_for, redirect
from authlib.integrations.flask_client import OAuth

from google.cloud import firestore

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
oauth = OAuth(app)


oauth.register(
    name='amazon',
    client_kwargs={
        'scope': 'profile'
    },
    client_id=os.environ.get('AMAZON_CLIENT_ID'),
    client_secret=os.environ.get('AMAZON_CLIENT_SECRET'),
    #request_token_url='https://www.amazon.com/ap/oa',
    access_token_url='https://api.amazon.com/auth/o2/token',
    authorize_url='https://www.amazon.com/ap/oa'
)


@app.route('/', methods=['GET'])
def index():
    if 'user_id' not in session:
        return redirect('login')
    
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/auth/amazon', methods=['GET'])
def amazon_auth():
    redirect_uri = url_for('amazon_auth_finished', _external=True)
    return oauth.amazon.authorize_redirect(redirect_uri)

@app.route('/auth/finished', methods=['GET'])
def amazon_auth_finished():
    token = oauth.amazon.authorize_access_token()
    resp = oauth.amazon.get('https://api.amazon.com/user/profile', token=token)
    profile = resp.json()
    session['user_id'] = profile['user_id']
    session['name'] = profile['name']
    # do something with the token and profile
    return redirect('/')

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    session.pop('name')
    return redirect(url_for('login'))

if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080
    app.run(host='127.0.0.1', port=PORT, debug=True)
