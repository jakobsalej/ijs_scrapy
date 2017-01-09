import requests
import urllib


baseAPIUrl = 'http://127.0.0.1:5000/'


def testItem(type, id):

    # get item form DB

    fullUrl = baseAPIUrl + 'item/' + type + '/' + str(id)
    response = requests.get(fullUrl)
    print(response.json())
    return



def testQuery(query):

    # get results for given query

    query = urllib.parse.quote(query)
    fullUrl = baseAPIUrl + 'query/' + query
    response = requests.get(fullUrl)
    data = response.json()
    print(data)
    print('-----------------------------------------------------------------------------------------------\n')
    for key in data:
        print(data[key]['name'], ',', data[key]['regionName'])

    return



# example JSON files
#testItem('attraction', 300)
testQuery('goriško kraska')
#testQuery('ljubljanski grad')
