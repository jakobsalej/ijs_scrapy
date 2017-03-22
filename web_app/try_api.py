import requests
import urllib

baseAPIUrl = 'http://127.0.0.1:5000/'


def testItem(type, id):
    # get item form DB

    fullUrl = baseAPIUrl + 'item/' + type + '/' + str(id)
    response = requests.get(fullUrl, auth=('asistent', 'projektasistent'))
    print(response)
    data = response.json()
    print(data['name'], data)
    print('---------------------------------------------------------------------------\n')

    return


def testQuery(query):
    # get results for given query

    query = urllib.parse.quote(query)
    fullUrl = baseAPIUrl + 'query/' + query
    response = requests.get(fullUrl, auth=('asistent', 'projektasistent'))
    print(response)
    data = response.json()
    print(data)
    print('-----------------------------------------------------------------------------------------------\n')

    for key in data:
        if key == '0':
            print('-> Exact hit:', data[key]['exactHit'])

        print(data[key]['name'], ',', data[key]['regionName'])

    return


testItem('attraction', 50)
testQuery('ljubljanski grad')
#testQuery('seznam rek v ljubljani')
