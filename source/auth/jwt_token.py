import os
from dotenv import load_dotenv
from flask import jsonify
import datetime
from flask_jwt_extended import JWTManager
# create_access_token : jwt 토큰을 만드는 함수
from flask_jwt_extended import create_access_token

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_PRE')

def create_token(user):
    del user['user_pw']
    user['exp'] = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    # additional_claims는 payload에 추가적으로 넣을 정보들
    #  토큰을 만들때 id를 기준으로 만듬
    access_token = create_access_token(user['user_id'], additional_claims=user)
    return jsonify(access_token)
