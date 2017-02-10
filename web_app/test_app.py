import sys
sys.path.append('../')

from flask import Flask, render_template, request, make_response, jsonify
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from search import analyzeQuery
from slovenia_info_scra import getFromDB
from whoosh.index import open_dir
import json


app = Flask(__name__)


# some basic http auth

auth = HTTPBasicAuth()

@auth.get_password
def get_password(username):
    if username == 'asistent':
        return 'projektasistent'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


# web page

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
        dict = analyzeQuery(index, text)

    return render_template('results.html', results=dict)


@app.route('/<type>/<int:id>')
def attraction(type=None, id=None):

    # getting attraction from DB based on ID and type in url
    item = getFromDB(type, id)

    return render_template('attraction.html', item=item)


# simple API

api = Api(app)



class QueryAPI(Resource):

    @auth.login_required
    def get(self, query):

        # perform a search, calling def from search.py
        # set a path to correct 'index' dir
        index = open_dir("../index")
        dict = analyzeQuery(index, query)
        result = json.dumps(dict, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
        print(result)

        # turning json-like string into actual object?
        resJson = json.loads(result)

        return resJson


class ItemAPI(Resource):
    def get(self, type, id):
        item = getFromDB(type, id)
        if item == None:
            return {'ERROR': 'No such item!'}, 400

        result = json.dumps(item, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
        print(result)

        # turning json-like string into actual object?
        resJson = json.loads(result)

        return resJson


api.add_resource(QueryAPI, '/query/<string:query>', endpoint='query')
api.add_resource(ItemAPI, '/item/<string:type>/<int:id>', endpoint='item')



