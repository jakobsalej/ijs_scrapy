import sys
sys.path.append('../')

from flask import Flask, render_template, request
from search import searchIndex
from slovenia_info_scra import Attraction
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
        # set a path to correct 'index' dir
        index = open_dir("../index")
        dict = searchIndex(index, text)


    return render_template('results.html', results=dict)


@app.route('/attractions/<id>')
def attraction(id=None):

    # getting attraction from DB based on ID in url
    id = float(id)
    attr = Attraction.get(Attraction.id == id)
    print(attr.name)

    return render_template('attraction.html', attr=attr)