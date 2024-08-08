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

import hashlib

from pymongo import MongoClient
client = MongoClient(mongodb_url)
db = client.week0_team4

def convert_user_list(all_users):
   for user in all_users:
      user['url'] = '../static/img/no_user.jpg' if 'img' not in user else user['img']
      
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
   jwt = convert_cookie_2_jwt(request.cookies)
   name = ''
   if jwt:
      name = jwt['name']
   
   all_users = list(db.user.find({}))
   all_users = convert_user_list(all_users)
   return render_template('main.html',users=all_users, name=name)

@app.route('/qna', methods=['POST'])
def create_question():
   jwt = convert_cookie_2_jwt(request.cookies)
   if jwt is None:
      return unauthorized_response()
   
   data = request.form.to_dict()
   data['q_user'] = jwt['user_id']
   data['q_name'] = jwt['name']

   db.question.insert_one(data)

   return jsonify({'result':'success'})

@app.route('/qna/<id>', methods=['GET'])
def go_user_tetail(id):
   jwt = convert_cookie_2_jwt(request.cookies)
   if jwt is None:
       return unauthorized_response()
   
   me = jwt.copy()
   detail_user = db.user.find_one({'_id': ObjectId(id)})
   detail_user['_id'] = str(detail_user['_id'])

   if 'user_id' not in detail_user:
      all_users = list(db.user.find({}))
      all_users = convert_user_list(all_users)
      return render_template('main.html', msg='아직 참여하지 않은 정글러입니다.',users=all_users)
   
   questions = list(db.question.find({'a_user':detail_user['user_id']}))
   
   for q in questions: q['_id'] = str(q['_id'])
   
   return render_template('detail.html', me=me, detail_user=detail_user, questions=questions, name=jwt['name'])

@app.route('/qna/<q_id>', methods=['DELETE'])
def delete_qna(q_id):

   q = db.question.find_one({'_id':ObjectId(q_id)})
   if 'answer' in q:
      return jsonify({'result':'answered'})

   db.question.delete_one({'_id':ObjectId(q_id)})
   return jsonify({'result':'success'})

@app.route('/qna/<q_id>', methods=['PUT'])
def modify_qna(q_id):
   question = request.form['question']
   anonymous = request.form['anonymous']

   q = db.question.find_one({'_id':ObjectId(q_id)})
   if 'answer' in q :
      return jsonify({'result':'answered'})
   
   db.question.update_one({'_id':ObjectId(q_id)}, {'$set':{'question': question, 'anonymous':anonymous}})
   return jsonify({'result':'success'})

@app.route('/qna/answer/<q_id>',methods=['POST'])
def regist_answer(q_id):
   q = db.question.find_one({'_id':ObjectId(q_id)})

   if q == None:
      return jsonify({'result':'none'})
   
   answer = request.form['answer']
   db.question.update_one({'_id':ObjectId(q_id)}, {'$set':{'answer': answer}})
   return jsonify({'result':'success'})

@app.route('/qna/answer/<q_id>',methods=['PUT'])
def modify_answer(q_id):
   answer = request.form['answer']
   if answer == '':
      db.question.update_one({'_id':ObjectId(q_id)}, {'$unset':{'answer': ''}})
   else :
      db.question.update_one({'_id':ObjectId(q_id)}, {'$set':{'answer': answer}})
   return jsonify({'result':'success'})


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

@app.route('/friends')
def find_friends():
   jwt = convert_cookie_2_jwt(request.cookies)
   if jwt is None:
      return unauthorized_response()
   return render_template('friends.html', name=jwt['name'])

@app.route('/friends', methods=['POST'])
def show_friends():
   gender = request.form['gender']
   mbti1 = request.form['mbti1']
   mbti2 = request.form['mbti2']
   mbti3 = request.form['mbti3']
   mbti4 = request.form['mbti4']
   hobby = request.form['hobby']
   age = request.form['age']
   meal = request.form['meal']
   exercise = request.form['exercise']
   laptop = request.form['laptop']
   coffee = request.form['coffee']
   breakfast = request.form['breakfast']
   drink = request.form['drink']

   condition = {}
   if gender and gender != '':
      condition['gender'] = gender
   if mbti1 and mbti1 != '':
      condition['mbti1'] = mbti1
   if mbti2 and mbti2 != '':
      condition['mbti2'] = mbti2   
   if mbti3 and mbti3 != '':
      condition['mbti3'] = mbti3   
   if mbti4 and mbti4 != '':
      condition['mbti4'] = mbti4
   if hobby and hobby != '':
      condition['hobby'] = hobby
   if age and age != '':
      condition['age'] = age
   if meal and meal != '':
      condition['meal'] = meal
   if exercise and exercise != '':
      condition['exercise'] = exercise
   if laptop and laptop != '':
      condition['laptop'] = laptop
   if coffee and coffee != '':
      condition['coffee'] = coffee
   if breakfast and breakfast != '':
      condition['breakfast'] = breakfast
   if drink and drink != '':
      condition['drink'] = drink
   
   friends = list(db.user.find(condition))
   friends = convert_user_list(friends)


   return jsonify({'result':'success', 'friends':friends})



@app.route('/login', methods=['POST'])
def login_user():
   user_id = request.form['ID']
   user_pw = request.form['PW']
   
   given_pw_enc_val = hashlib.sha256(user_pw.encode()).hexdigest()

   user = db.user.find_one( {'user_id':user_id }, {'_id':False})

   if user and (user.get('user_pw') == given_pw_enc_val):
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

@app.route('/main/logout')
def go_main_if_logout():
   all_users = list(db.user.find({}))
   all_users = convert_user_list(all_users)

   response = make_response(redirect('/'))
   response.delete_cookie('jwt')
   response.delete_cookie('expires')
   return response


@app.route('/regist')
def regist():
   return render_template('regist.html')

@app.route('/api/regist-user', methods=['POST'])
def regist_user():
   new_user = request.form.to_dict()
   
   name = new_user.get('name')
   user = db.user.find_one({ 'name':name }, {'_id':False})
   
   # 가입 여부 확인: 이름으로 조회 후 user_id 값 존재 여부로 판단
   if user is None:
      # 정글러가 아니면 가입 불가
      return jsonify({'result': 'error', 'msg': '9기 정글러만 가입하실 수 있습니다.'})

   elif user.get('user_id') is None:
      # 이름이 같은지 체크하고
      # 같은 이름이 있으면 해당 값에 update

      # 비밀번호 암호화해서 문자열 형태로 저장
      enc_pw_object = hashlib.sha256(new_user.get('user_pw').encode())
      enc_pw_val = enc_pw_object.hexdigest()

      target = { "name" : name }
      value = {
         "user_id": new_user.get('user_id'),
         "user_pw": enc_pw_val,
         "gender": new_user.get('gender'),
         "mbti1": new_user.get('mbti1'),
         "mbti2": new_user.get('mbti2'),
         "mbti3": new_user.get('mbti3'),
         "mbti4": new_user.get('mbti4'),
         "hobby": new_user.get('hobby'),
         "age": new_user.get('age'),
         "meal": new_user.get('meal'),
         "exercise": new_user.get('exercise'),
         "laptop": new_user.get('laptop'),
         "coffee": new_user.get('coffee'),
         "breakfast": new_user.get('breakfast'),
         "drink": int(new_user.get('drink')),
         "img": new_user.get('img')
      }
      db.user.update_one(target, { '$set' : value })

   else:
      # 가입이 된 사람이 가입하면
      # 이미 가입하셨습니다 하고 튕겨내기
      return jsonify({'result': 'error', 'msg': '이미 가입하셨습니다.'})

   return jsonify({'result': 'success', 'msg': '회원가입이 완료되었습니다. 로그인 해 주세요.'})

@app.route('/update')
def update():
   # 로그인 한 유져 정보를 가져와서
   jwt = convert_cookie_2_jwt(request.cookies)
   if jwt is None:
      return unauthorized_response()
   
   user_id = jwt['user_id']
   # 해당 유저 정보를 조회하고
   user = db.user.find_one({'user_id':user_id})
   user['_id'] = str(user['_id'])

   # 조회한 정보 보내주기
   return render_template('update.html', user=user, name=jwt['name'])

@app.route('/api/update-user', methods=['POST'])
def update_user():
   new_user = request.form.to_dict()

   target = { "user_id" : new_user.get('user_id') }
   value = {
      "name": new_user.get('name'),
      "gender": new_user.get('gender'),
      "mbti1": new_user.get('mbti1'),
      "mbti2": new_user.get('mbti2'),
      "mbti3": new_user.get('mbti3'),
      "mbti4": new_user.get('mbti4'),
      "hobby": new_user.get('hobby'),
      "age": new_user.get('age'),
      "meal": new_user.get('meal'),
      "exercise": new_user.get('exercise'),
      "laptop": new_user.get('laptop'),
      "coffee": new_user.get('coffee'),
      "breakfast": new_user.get('breakfast'),
      "drink": int(new_user.get('drink')),
      "img": new_user.get('img')
   }

   db.user.update_one(target, { '$set' : value })
   return jsonify({'result': 'success', 'msg': '수정되었습니다.'})

@app.route('/api/update-password', methods=['POST'])
def update_password():
   past_pw = request.form['past_user_pw']
   new_pw = request.form['new_user_pw']

   past_pw_enc_val = hashlib.sha256(past_pw.encode()).hexdigest()
   new_pw_enc_val = hashlib.sha256(new_pw.encode()).hexdigest()

   # 유저정보 가져와서 조회
   jwt = convert_cookie_2_jwt(request.cookies)
   if jwt is None:
      return unauthorized_response()
   
   user_id = jwt['user_id']
   user = db.user.find_one({'user_id':user_id}, {'_id':False})

   # 현재비밀번호 일치 여부 검증
   if user['user_pw'] == past_pw_enc_val:
      target = { "user_id" : user_id }
      value = { "user_pw": new_pw_enc_val }
      db.user.update_one(target, { '$set' : value })
   else:
      return jsonify({'result': 'error', 'msg': '현재 비밀번호가 일치하지 않습니다.'})

   return jsonify({'result': 'success', 'msg': '수정되었습니다. 다시 로그인 해 주세요.'})

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)

