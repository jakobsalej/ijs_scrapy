import os
import collections
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser, MultifieldParser
from slovenia_info_scra import Attraction, Region, Town


# schema for attribute entries
attrSchema = Schema(id=ID(stored=True),
                    name=TEXT(stored=True),
                    link=ID(stored=True),
                    address=TEXT,
                    phone=KEYWORD(commas=True),
                    webpage=ID,
                    tags=KEYWORD(commas=True, scorable=True, lowercase=True),
                    type=ID(stored=True),
                    description=TEXT,
                    picture=ID,
                    regionName=TEXT(stored=True),
                    regionID=ID,
                    destination=TEXT,
                    place=TEXT,
                    gpsX=NUMERIC,
                    gpsY=NUMERIC,
                    topResult=BOOLEAN
                    )



def init():
    # Create index dir if it does not exists.
    if not os.path.exists("index"):
        os.mkdir("index")

    index = create_in("index", attrSchema)

    writer = index.writer()

    # fill index from DB
    for attraction in Attraction.select():
        print(attraction.name, attraction.gpsX, attraction.gpsY)
        writer.add_document(
            id=str(attraction.id).encode("utf-8").decode("utf-8"),
            name=attraction.name,
            link=attraction.link,
            address=attraction.address,
            phone=attraction.phone,
            webpage=attraction.webpage,
            tags=attraction.tags,
            type=attraction.type,
            description=attraction.description,
            picture=attraction.picture,
            regionName=attraction.regionName,
            destination=attraction.destination,
            place=attraction.place,
            gpsX=attraction.gpsX,
            gpsY=attraction.gpsY
        )

    for town in Town.select():
        print(town.name, town.gpsX, town.gpsY)
        writer.add_document(
            id=str(town.id).encode("utf-8").decode("utf-8"),
            name=town.name,
            link=town.link,
            webpage=town.webpage,
            tags=town.tags,
            type=town.type,
            description=town.description,
            picture=town.picture,
            regionName=town.regionName,
            destination=town.destination,
            place=town.place,
            gpsX=town.gpsX,
            gpsY=town.gpsY,
            topResult=town.topResult
        )
        
    writer.commit()


def testSearch(index):
    # test search
    with index.searcher() as searcher:
        query = QueryParser("name", index.schema).parse("bled")
        results = searcher.search(query)
        for result in results:
            print(result)


def searchIndex(index, text):

    # search for a given string
    with index.searcher() as searcher:
        # using MultifieldParser to search all relevant fields
        query = MultifieldParser(["name", "type", "regionName", "description"], index.schema).parse(text)
        results = searcher.search(query)
        print('Number of hits:', len(results))

        # saving hits to the ordered dict, so we can return it (look at this: http://stackoverflow.com/questions/19477319/whoosh-accessing-search-page-result-items-throws-readerclosed-exception)
        dict = collections.OrderedDict()
        for result in results:
            print(result)
            dict[result['id']] = {'name': result['name'], 'link': result['link'], 'type': result['type'], 'regionName': result['regionName'] }

        return dict




# only run once, to build index
#init()

# testing search
index = open_dir("index")
testSearch(index)
results = searchIndex(index, 'bled')



# TO-DO: add region entries (new index, add to this index?)
