from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

import os
from dotenv import load_dotenv

load_dotenv()

mongodb_url = os.environ.get('MONGODB_URL')

import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient
client = MongoClient(mongodb_url)
db = client.week0_team4


## HTML을 주는 부분
@app.route('/')
def home():
   return render_template('main.html')

@app.route('/qna/<id>')
def go_user_tetail(id):
   return render_template('detail.html')

@app.route('/login', methods=['GET'])
def login_success():
   #토큰에서 유저네임 꺼내기. 
   user="김혜다"
   return render_template('main.html', name=user)

@app.route('/login', methods=['POST'])
def login_user():
   user_id = request.form['ID']
   user_pw = request.form['PW']

   user = db.user.find_one({'user_id':user_id,'user_pw':user_pw})
   if user:
        return jsonify({'result': 'success'})
   else:
        return jsonify({'result': 'fail'})


if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)
