import os
import collections
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.analysis import *
from whoosh.query import Term
from slovenia_info_scra import Attraction, Region, Town


# list of special words we'd like to detect
specialWords = ['seznam', 'tabela',     # SLO
                'list',                 # ENG
                ]

prepositions = ['na', 'v', 'ob', 'pri', 's', 'z']


# schema for attribute entries
attrSchema = Schema(id=ID(stored=True),
                    name=TEXT(stored=True, field_boost=1.5),
                    link=ID(stored=True),
                    address=TEXT,
                    phone=KEYWORD(commas=True),
                    webpage=ID,
                    tags=KEYWORD(commas=True, scorable=True, lowercase=True, field_boost=1.5),
                    type=ID(stored=True, field_boost=1),
                    description=TEXT(field_boost=0.01),
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
    newText, resultLimit, filterQuery = analyzeQuery(index, text)

    # search for a given string
    with index.searcher() as searcher:
        # using MultifieldParser to search all relevant fields

        # in case of multiple words in query, use OR (query: 'lake bled' => 'lake' OR 'bled'), but boost score of items that contain both tokens
        orGroup = OrGroup.factory(1.5)
        query = MultifieldParser(["name", "type", "regionName", "description", "tags", "topResult"], index.schema, group=orGroup).parse(newText)
        results = searcher.search(query, limit=resultLimit, terms=True, filter=filterQuery)
        print('Number of hits:', len(results))


        # saving hits to the ordered dict, so we can return it (look at this: http://stackoverflow.com/questions/19477319/whoosh-accessing-search-page-result-items-throws-readerclosed-exception)
        dict = collections.OrderedDict()

        for i, result in enumerate(results):
            print(result, 'SCORE:', results.score(i), 'MATCHED TERMS:', result.matched_terms())
            dict[i] = {'id': result['id'], 'name': result['name'], 'link': result['link'], 'type': result['type'], 'regionName': result['regionName'], 'typeID': result['typeID'], 'score': results.score(i) }

        return dict



def analyzeQuery(index, query):

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

    # turn list back to string
    text = ' '.join(newQuery)

    # if limit = 10, we want to make search a bit more general, since we need more results based on type, not name (probably)
    filterQuery = None
    if limit == 10:
        text, filterQuery = wordCorrector(index, text)


    print('New user query after analysis:', text)

    return text, limit, filterQuery



def wordCorrector(index, text):

    # here we try to do all the smart things to make search more accurate

    # look for any prepositions and remove them (as stopwords)
    sa = StandardAnalyzer(stoplist=prepositions)
    analyzedText = []
    
    # here we save an index of a word that's probably a location (we assume location follows a preposition: "arhitektura na gorenjskem"); in case there is more than one preposition, we take the index of the first one
    locationIndex = -1
    for i, token in enumerate(sa(text, removestops=False)):
        if token.stopped == True and locationIndex == -1:
            locationIndex = i
        else:
            analyzedText.append(token.text)

    filterQuery2 = None
    # as we try to turn words in a more 'general' form, we look in the regionName and tags fields for potential 'corrections' of our words in query, using "Did you mean..." method from Whoosh
    with index.searcher() as s:
        correctorRegion = s.corrector('regionName')
        corrector2 = s.corrector('tags')    # might be better to create a custom word list that has words in singular: jezero, reka, itd..??
        correctedList1 = []
        correctedList2 = []
        for i, word in enumerate(analyzedText):
            
            # look for index of a "location word", then check if it matches any region / destination / Town (TO-DO!!)
            if i == locationIndex:
                correctedLocation = correctorRegion.suggest(word, limit=1)
                # if there is a hit, replace original word with a corrected version (or should we remove it??)
                if len(correctedLocation) > 0:
                    analyzedText[i] = correctedLocation[0]
                else:
                    analyzedText[i] = findCorrectRegion(analyzedText[i])
                
            corrected2 = corrector2.suggest(word, limit=1)
            print(word, ', suggestions1:', correctedLocation, ', suggestions2:', corrector2.suggest(word, limit=1))
            if len(correctedLocation) > 0:
                analyzedText[i] = correctedLocation[0]
                correctedList1.append(correctedLocation[0])
                filterQuery1 = Term("regionName", correctedLocation[0])
            elif len(corrected2) > 0:
                analyzedText[i] = corrected2[0]
                correctedList2.append(corrected2[0])
                filterQuery2 = Term("tags", correctedList2)

        # turn list back to string
        text = ' '.join(analyzedText)

        # put together a filter query


        # TO-DO: filter results: http://whoosh.readthedocs.io/en/latest/searching.html#combining-results-objects

        return text, filterQuery2



def findCorrectRegion(word):

    # TO-DO: based on Region of most hits for a given word, return region?

    return word;





# only run once, to build index
#init()

# testing search
index = open_dir("index")
results = searchIndex(index, 'seznam slapov ob ljubljani')
results = searchIndex(index, 'seznam jezer na koroškem')




# TO-DO: check search query for special words ("seznam,..") and return list of hits (first 10 for example); "seznam jezer na gorenjskem"

#analyzeQuery('seznam jezera na gorenjskem, Gorenjska, gorenjsko, hello, working, helped, tabela jezer')

# TO-DO: make variations of word, dummy way? --> use 'did u mean method!!'
#wordCorrector(index, 'jezera na gorenjskem')