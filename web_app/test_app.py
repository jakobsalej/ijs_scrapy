import sys
sys.path.append('../')

from flask import Flask, render_template, request
from search import searchIndex
from models import *
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


@app.route('/<type>/<id>')
def attraction(type=None, id=None):

    # getting attraction from DB based on ID and type in url
    id = float(id)

    if type == 'region':
        item = Region.get(Region.id == id)
    elif type == 'town':
        item = Town.get(Town.id == id)
    elif type == 'attraction':
        item = Attraction.get(Attraction.id == id)

    print(item.name)

    return render_template('attraction.html', item=item)