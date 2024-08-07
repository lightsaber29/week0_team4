from flask import Flask, render_template, jsonify, request, redirect, make_response
app = Flask(__name__)

import os
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
# @jwt_required() 이걸 사용하면 Authorization 헤더의 존재와 그 안에 토큰이 정상인지 체크함
from flask_jwt_extended import  get_jwt_identity, jwt_required

load_dotenv()

mongodb_url = os.environ.get('MONGODB_URL')

app.config["JWT_SECRET_KEY"] = os.environ.get('SECRET_PRE')
jwt = JWTManager(app)

import requests
from bs4 import BeautifulSoup
from source.auth.jwt_token import create_token, unauthorized_response, convert_cookie_2_jwt
from datetime import datetime, timedelta

from pymongo import MongoClient
client = MongoClient(mongodb_url)
db = client.week0_team4


## HTML을 주는 부분
@app.route('/')
def home():
   return render_template('main.html')

@app.route('/regist')
def regist():
   return render_template('regist.html')

@app.route('/qna/<id>')
def go_user_tetail(id):
   print('qna in')
   jwt = convert_cookie_2_jwt(request.cookies)
   print(jwt)
   if jwt is None:
       return unauthorized_response()
   return render_template('detail.html')

@app.errorhandler(401)
def unathentication(error):
    print(error)
    return unauthorized_response()

@app.errorhandler(422)
def jwt_expires(error):
    print(error)
    return unauthorized_response()

@app.route('/login', methods=['GET'])
def login_success():
   #토큰에서 유저네임 꺼내기. 
   jwt = convert_cookie_2_jwt(request.cookies)
   
   if jwt is None:
      return unauthorized_response()
   
   name = jwt['name']
   return render_template('main.html', name=name)

@app.route('/list', methods=['GET'])
def listing():
   all_users = list(db.user.find({}))
   for user in all_users:
      user['_id'] = str(user['_id'])
    
   return jsonify({'result':'success', 'users':all_users})



@app.route('/login', methods=['POST'])
def login_user():
   user_id = request.form['ID']
   user_pw = request.form['PW']

   user = db.user.find_one({'user_id':user_id,'user_pw':user_pw}, {'_id':False})

   if user:
      jwt_token = create_token(user)
      response = make_response(jsonify({'result': 'success'}))
      expire_time = datetime.now() + timedelta(hours=24)
      max_age = 60 * 60 * 24

      response.set_cookie('jwt', jwt_token, httponly=True, samesite='Strict', max_age=max_age, secure=True)
      response.set_cookie('expires', str(expire_time), httponly=True, samesite='Strict', max_age=max_age, secure=True)
      return response
   else:
        return jsonify({'result': 'fail'})


@app.route('/recive_token_test')
@jwt_required()
def recive_token_test():
   # get_jwt_identity : jwt 안에 있는 id 를 가져옴
   current_user_id = get_jwt_identity()
   return current_user_id

@app.route('/main/nologin')
def go_main_if_nologin():
   response = make_response(render_template('main.html', msg='로그인이 필요합니다.'))
   response.delete_cookie('jwt')
   response.delete_cookie('expires')
   return response

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)
