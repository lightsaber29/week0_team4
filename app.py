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
   return render_template('index.html')

@app.route('/qna/<id>')
def go_user_tetail(id):
   return render_template('detail.html')

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
