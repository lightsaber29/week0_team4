import os
from dotenv import load_dotenv
from flask import request, redirect, make_response, render_template
from datetime import datetime, timedelta
# create_access_token : jwt 토큰을 만드는 함수
from flask_jwt_extended import create_access_token, decode_token, decode_token
load_dotenv()
SECRET_KEY = os.environ.get('SECRET_PRE')

def create_token(user):
    del user['user_pw']
    user['exp'] = datetime.utcnow() + timedelta(hours=24)
    # additional_claims는 payload에 추가적으로 넣을 정보들
    #  토큰을 만들때 id를 기준으로 만듬
    access_token = create_access_token(user['user_id'], additional_claims=user)
    return access_token

def unauthorized_response():
    return redirect('/main/nologin')

def convert_cookie_2_jwt(cookie):
    jwt = cookie.get('jwt')
    expires = cookie.get('expires')
    
    try:
        expires = datetime.strptime(expires, "%Y-%m-%d %H:%M:%S.%f")
        if expires < datetime.now():
            jwt = None
        else:
            jwt = decode_token(jwt)
    except:
        jwt = None
    return jwt
   
