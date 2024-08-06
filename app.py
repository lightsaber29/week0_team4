from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient
client = MongoClient('mongodb+srv://sparta:jungle@cluster0.yrie6f6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client.week0_team4

## HTML을 주는 부분
@app.route('/')
def home():
   return render_template('index.html')

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)