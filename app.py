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
from bson.objectid import ObjectId

from pymongo import MongoClient
client = MongoClient(mongodb_url)
db = client.week0_team4

def convert_user_list(all_users):
   for user in all_users:
      if 'url' not in user:
         user['url'] = '../static/img/no_user.jpg'
      
      user['mbti'] = ''
      if 'mbti1' in user:
         user['mbti'] = user['mbti1'] + user['mbti2'] + user['mbti3'] + user['mbti4']
      
      user['age_ko'] = ''
      if 'age' in user:
         if user['age'] == "~23" : 
            user['age_ko'] = "20대 초반"
         elif user['age'] == "24~26":
            user['age_ko'] = "20대 중반"
         elif user['age'] == "27~29":
            user['age_ko'] = "20대 후반"
         elif user['age'] == "30~":
            user['age_ko'] = "30대"

      user['gender_ko'] = ''
      if 'gender' in user:
         if user['gender'] == 'F':
            user['gender_ko'] = '여'
         elif user['gender'] == 'M':
            user['gender_ko'] = '남'

      user['_id'] = str(user['_id'])
   return all_users

## HTML을 주는 부분
@app.route('/')
def home():
   all_users = list(db.user.find({}))
   all_users = convert_user_list(all_users)
   return render_template('main.html',users=all_users)

@app.route('/qna/<id>')
def go_user_tetail(id):
   print('qna in')
   jwt = convert_cookie_2_jwt(request.cookies)
   print(jwt)
   if jwt is None:
       return unauthorized_response()
   
   me = jwt.copy()
   detail_user = db.user.find_one({'_id': ObjectId(id)})

   print(detail_user)

   if 'user_id' not in detail_user:
      all_users = list(db.user.find({}))
      all_users = convert_user_list(all_users)
      return render_template('main.html', msg='아직 참여하지 않은 정글러입니다.',users=all_users)
   
   print(detail_user)
   questions = list(db.question.find({'a_user':detail_user['user_id']}))
   
   return render_template('detail.html', me=me, detail_user=detail_user, questions=questions)

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
   all_users = list(db.user.find({}))
   all_users = convert_user_list(all_users)

   return render_template('main.html', name=name, users=all_users)

@app.route('/list', methods=['GET'])
def listing():
   all_users = list(db.user.find({}))
   all_users = convert_user_list(all_users)
    
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
   all_users = list(db.user.find({}))
   all_users = convert_user_list(all_users)

   response = make_response(render_template('main.html', msg='로그인이 필요합니다.', users=all_users))
   response.delete_cookie('jwt')
   response.delete_cookie('expires')
   return response

# {'_id': ObjectId('66b207e0c8083c31d4b0d629'), 'name': '최수빈', 'user_id': 'lightsaber29', 'user_pw': '1234', 'gender': 'F', 'mbti1': 'E', 'mbti2': 'N', 'mbti3': 'F', 'mbti4': 'J', 'hobby': 'etc', 'age': '27~29', 'meal': 'goout', 'exercise': 'no', 'laptop': 'apple', 'coffee': 'americano', 'breakfast': 'Y', 'drink': 0, 'url': '../static/img/no_user.jpg'}

@app.route('/regist')
def regist():
   return render_template('regist.html')

@app.route('/api/regist-user', methods=['POST'])
def regist_user():
   new_user = request.form.to_dict()
   db.user.insert_one(new_user)
   return jsonify({'result': 'success', 'msg': '등록 완료!'})

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)

