from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

import os
from dotenv import load_dotenv

load_dotenv()

mongodb_url = os.environ.get(MONGODB_URL)

import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient
client = MongoClient('mongodb_url')
db = client.week0_team4


## HTML을 주는 부분
@app.route('/')
def home():
   return render_template('index.html')

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)
