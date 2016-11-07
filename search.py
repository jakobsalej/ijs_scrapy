import os
import collections
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.analysis import *
from whoosh.lang.morph_en import variations
from slovenia_info_scra import Attraction, Region, Town


# list of special words we'd like to detect
specialWords = ['seznam', 'tabela',     # SLO
                'list',                 # ENG
                ]



# schema for attribute entries
attrSchema = Schema(id=ID(stored=True),
                    name=TEXT(stored=True, field_boost=1.5),
                    link=ID(stored=True),
                    address=TEXT,
                    phone=KEYWORD(commas=True),
                    webpage=ID,
                    tags=KEYWORD(commas=True, scorable=True, lowercase=True),
                    type=ID(stored=True),
                    description=TEXT(field_boost=0.25),
                    picture=ID,
                    regionName=TEXT(stored=True),
                    regionID=ID,
                    destination=TEXT,
                    place=TEXT,
                    gpsX=NUMERIC,
                    gpsY=NUMERIC,
                    topResult=BOOLEAN,
                    typeID=TEXT(stored=True)
                    )



def init():
    # Create index dir if it does not exists.
    if not os.path.exists("index"):
        os.mkdir("index")

    index = create_in("index", attrSchema)

    writer = index.writer()

    # fill index from DB with regions, attractions and towns
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
            gpsY=attraction.gpsY,
            typeID='attraction'
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
            topResult=town.topResult,
            typeID='town'
        )

    for region in Region.select():
        print(region.name)
        writer.add_document(
            id=str(region.id).encode("utf-8").decode("utf-8"),
            name=region.name,
            link=region.link,
            description=region.description,
            picture=region.picture,
            regionName='region',    # just for displaying results, doesn't matter
            type='region',
            typeID='region'
        )
        
    writer.commit()

    return



def searchIndex(index, text):

    # look at the query for special words
    newText, resultLimit = analyzeQuery(text)

    # search for a given string
    with index.searcher() as searcher:
        # using MultifieldParser to search all relevant fields

        # in case of multiple words in query, use OR (query: 'lake bled' => 'lake' OR 'bled'), but boost score of items that contain both tokens
        orGroup = OrGroup.factory(0.8)
        query = MultifieldParser(["name", "type", "regionName", "description", "tags", "topResult"], index.schema, group=orGroup).parse(newText)
        results = searcher.search(query, limit=resultLimit, terms=True)
        print('Number of hits:', len(results))


        # saving hits to the ordered dict, so we can return it (look at this: http://stackoverflow.com/questions/19477319/whoosh-accessing-search-page-result-items-throws-readerclosed-exception)
        dict = collections.OrderedDict()

        for i, result in enumerate(results):
            print(result, 'SCORE:', results.score(i), 'MATCHED TERMS:', result.matched_terms())
            dict[i] = {'id': result['id'], 'name': result['name'], 'link': result['link'], 'type': result['type'], 'regionName': result['regionName'], 'typeID': result['typeID'], 'score': results.score(i) }

        return dict



def analyzeQuery(query):

    # use standard analyzer which composes a RegexTokenizer with a LowercaseFilter and optional StopFilter (docs: 'http://whoosh.readthedocs.io/en/latest/api/analysis.html#analyzers')
    sa = StandardAnalyzer(stoplist=specialWords)
    print([(token.text, token.stopped) for token in sa(query, removestops=False)])

    limit = 1
    newQuery = []
    for token in sa(query, removestops=False):
        if token.stopped == True:
            # stopword detected, do what you have to do
            limit = 10
        else:
            newQuery.append(token.text)

    # turn list to string and pass it to search
    index = open_dir("index")
    wordCorrector(index, newQuery)

    text = ' '.join(newQuery)
    print('New user query after analysis:', text)

    return text, limit



def wordCorrector(index, text):
    with index.searcher() as s:
        corrector = s.corrector('regionName')
        corrector2 = s.corrector('name')    # probably better to create a custom word list that has words in singular: jezero, reka, itd..
        for word in text:
            print(word, ', suggestions1:', corrector.suggest(word, limit=3), ', suggestions2:', corrector2.suggest(word, limit=3))




# only run once, to build index
#init()

# testing search
index = open_dir("index")
results = searchIndex(index, 'blejsko jezero')




# TO-DO: check search query for special words ("seznam,..") and return list of hits (first 10 for example); "seznam jezer na gorenjskem"

analyzeQuery('seznam jezera na gorenjskem, Gorenjska, gorenjsko, hello, working, helped, tabela jezer')
print(variations('jezero'))

# TO-DO: make variations of word, dummy way? --> use 'did u mean method!!'
wordCorrector(index, 'jezera na gorenjskem')