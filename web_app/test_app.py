import sys
sys.path.append('../')

from flask import Flask, render_template, request
from search import searchIndex
from whoosh.index import open_dir

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        text = request.form['input']

        # perform a search, calling def from search.py
        # set a path to 'index' dir
        index = open_dir("../index")
        results = searchIndex(index, text)

    return render_template('results.html', results=results)