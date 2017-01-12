import requests
from lxml import etree
import pickle

# getting all towns in Slovenia from 'http://www.itis.si/Kraji'

page = requests.get('http://www.itis.si/Kraji')
elTree = etree.HTML(page.text)

places = elTree.xpath('//*[@id="core"]/section[2]/div[2]/article//li/a/text()')
print(places)
print('Count:', len(places))

# lowercase
places = sorted([place.lower() for place in places])

# saving to file
with open('kraji_slovenija', 'wb') as fp:
    pickle.dump(places, fp)
