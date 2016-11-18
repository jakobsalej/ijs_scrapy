import os
import collections
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, OrGroup, QueryParser
from whoosh.analysis import *
from whoosh.query import *
from slovenia_info_scra import Attraction, Region, Town


# list of special words we'd like to detect to show more than one result
specialWords = ['seznam', 'tabela',     # SLO
                'list',                 # ENG
                ]

prepositions = ['na', 'v', 'ob', 'pri', 's', 'z', 'bližini', 'blizu', 'zraven']


# schema for attribute entries
attrSchema = Schema(id=ID(stored=True),
                    name=TEXT(stored=True, field_boost=1.5),
                    link=ID(stored=True),
                    address=TEXT,
                    phone=KEYWORD(commas=True),
                    webpage=ID,
                    tags=KEYWORD(commas=True, scorable=True, lowercase=True, stored=True),
                    #type=ID(stored=True, field_boost=1.3, lowercase=True),
                    type=KEYWORD(stored=True, field_boost=1.3, lowercase=True, scorable=True),
                    description=TEXT(field_boost=0.01),
                    picture=ID,
                    regionName=TEXT(stored=True),
                    regionID=ID,
                    destination=TEXT(stored=True),
                    place=TEXT(stored=True),
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



def searchIndex(index, newText, resultLimit, filterQuery):

    # search for a given string
    with index.searcher() as searcher:
        # using MultifieldParser to search all relevant fields

        # in case of multiple words in query, use OR (query: 'lake bled' => 'lake' OR 'bled'), but boost score of items that contain both tokens
        orGroup = OrGroup.factory(0.9)
        query = MultifieldParser(["name", "type", "regionName", "description", "tags", "topResult", "destination", "place"], index.schema, group=orGroup).parse(newText)
        results = searcher.search(query, limit=resultLimit, terms=True, filter=filterQuery)
        print('Number of hits:', len(results))


        # saving hits to the ordered dict, so we can return it (look at this: http://stackoverflow.com/questions/19477319/whoosh-accessing-search-page-result-items-throws-readerclosed-exception)
        dict = collections.OrderedDict()

        for i, result in enumerate(results):
            print(result, 'SCORE:', results.score(i), 'MATCHED TERMS:', result.matched_terms())
            dict[i] = {'id': result['id'], 'name': result['name'], 'link': result['link'], 'type': result['type'], 'regionName': result['regionName'], 'destination': result['destination'], 'place': result['place'], 'typeID': result['typeID'], 'score': results.score(i) }

        return dict



def analyzeQuery(index, query):

    print('Original search query:', query)
    # before we start with analysis, let's check if there is a hit that matches search query word for word in title
    resultHit = checkOneHit(index, query)
    if resultHit:
        print('------------------------------------------------------------------------------------------------------------------------------\n\n\n')
        return resultHit

    # if there was no exact hit (query == name of first result), we try to do some smart things
    # use standard analyzer which composes a RegexTokenizer with a LowercaseFilter and optional StopFilter (docs: 'http://whoosh.readthedocs.io/en/latest/api/analysis.html#analyzers')
    sa = StandardAnalyzer(stoplist=specialWords)
    print('Special words: ', [(token.text, token.stopped) for token in sa(query, removestops=False)])

    # look for stopwords (seznam, tabela) or plural form to decide if user wants more than one result
    limit = 1
    newQuery = []
    with index.searcher() as s:
        correctorType = s.corrector('type')
        for token in sa(query, removestops=False):
            # len(token.test) > 1 is needed as Whoosh automatically removes all words that are only one letter long - but we need them as prepositions (s, z, v)
            if token.stopped == True and len(token.text) > 1:
                limit = 10
            # len(token.text) > 2 is needed, otherwise type matches words like 'na'
            elif len(token.text) > 2 and len(correctorType.suggest(token.text, limit=1, maxdist=0, prefix=2)) > 0:
                print('Found type in plural, set limit to 10!:', token.text)
                limit = 10
                newQuery.append(token.text)
            else:
                newQuery.append(token.text)

    # turn list back to string
    text = ' '.join(newQuery)

    # if limit = 10, we want to make search a bit more general because a stopword/plural was detected, since we need more results based on type, not name (probably)
    filterQuery = None
    if limit == 10:
        text, gotLocation, locationFilter, typeFilter, locationField, correctedLocation = wordCorrector(index, text)
        filterQuery = joinFilters(typeFilter, locationFilter)

    print('New user query after analysis:', text)

    #get results; if empty, change location filters
    hits = searchIndex(index, text, limit, filterQuery)
    if len(hits) == 0:

        # more-than-one-result search
        if limit == 10:
            # returns 3 location filter options: place, destination, region; if there are still no results after applaying them, remove location filter
            newLocationFilter, fieldOptions = changeLocationFilter(gotLocation, locationField, correctedLocation, locationFilter)

            while len(hits) == 0 and gotLocation > 1:
                newFilter = None
                if newLocationFilter[gotLocation-2] != '':
                    if newLocationFilter[gotLocation-2] != None:
                        newFilter = Term(fieldOptions[gotLocation-2], newLocationFilter[gotLocation-2])

                    filterQuery = joinFilters(typeFilter, newFilter)
                    print('Searching again with new filter:', filterQuery)
                    hits = searchIndex(index, text, limit, filterQuery)

                gotLocation -= 1

                # TO-DO: OPTIMIZE THIS!! change this ugly code

    print('------------------------------------------------------------------------------------------------------------------------------\n\n\n')
    return hits



def changeLocationFilter(gotLocation, locationField, correctedLocation, locationFilter):

    # based on locationFilter, get other fields (if available): region, destination, place (we have one already from the filter and we use that one for search)
    # locationOptions = [region, destination, place]
    locationOptions = [None, None, None]
    fieldOptions = ['regionName', 'destination', 'place']

    hits = searchIndex(index, correctedLocation, 1, locationFilter)
    for key in hits:
        print(hits[key])
        locationOptions[0] = hits[key]['regionName'].lower()
        locationOptions[1] = hits[key]['destination'].lower()
        locationOptions[2] = hits[key]['place'].lower()

    print('Following filters for location are available:', locationOptions)
    return locationOptions, fieldOptions



def checkOneHit(index, query):

    # tokenizer, lowercase filters
    sa = StandardAnalyzer(stoplist=None)
    parser = QueryParser("name", schema=index.schema)
    newQuery = []
    for token in sa(query):
        newQuery.append(token.text)

    newQuery = ' '.join(newQuery)
    newQueryPhrase = '"' + newQuery + '"'
    filterName = parser.parse(newQueryPhrase)
    hit = searchIndex(index, query, 1, filterName)

    # check again if name is exactly the same as search query; first we have to lowercase all words; if there is a match, just return ONE result and done!
    for key in hit:
        hitName = []
        for token in sa(hit[key]['name']):
            hitName.append(token.text)
        hitName = ' '.join(hitName)
        print('Comparing names:', newQuery, hitName)
        if hitName == newQuery:
            print('EXACT MATCH!!')
            return hit

    return None



def wordCorrector(index, text):

    # here we try to do all the smart things to make search more accurate

    # look for any prepositions and remove them (as stopwords)
    sa = StandardAnalyzer(stoplist=prepositions)
    analyzedText = []
    
    # here we save an index of a word that's probably a location (we assume location follows a preposition: "arhitektura na gorenjskem"); in case there is more than one preposition, we take index of the last one
    locationIndex = -1
    for i, token in enumerate(sa(text, removestops=False)):
        if token.stopped == True:
            locationIndex = i
        else:
            analyzedText.append(token.text)

    # as we try to turn words in a more 'general' form, we look in the regionName and tags fields for potential 'corrections' of our words in query, using "Did you mean..." method from Whoosh
    allowLocation = None
    allowType = None
    # 0 = suggested region, 1 = region, 2 = destination, 3 = place
    gotlocation = 0
    corrected = None
    locationField = None
    with index.searcher() as s:
        correctorRegion = s.corrector('regionName')
        correctorDestination = s.corrector('destination')
        correctorPlace = s.corrector('place')
        correctorType = s.corrector('type')    # might be better to create a custom word list that has words in singular: jezero, reka, itd..??
        allowLocation = None  # location filter
        for i, word in enumerate(analyzedText):
            
            # look for index of a "location word", then check if it matches any region / destination / Town; if it doesn't, try to figure it out
            if i == locationIndex:
                correctedRegion = correctorRegion.suggest(word, limit=1, prefix=2)
                correctedDestination = correctorDestination.suggest(word, limit=1, prefix=2)
                correctedPlace = correctorPlace.suggest(word, limit=1, prefix=2)
                print(word, ', suggestions for location:', correctedRegion, correctedDestination, correctedPlace)

                # if there is a hit, replace original word with a corrected version (or should we remove it, or not correct it at all??)
                if len(correctedRegion) > 0:
                    gotlocation = 1
                    corrected = correctedRegion[0]  # split?
                    locationField = 'regionName'
                elif len(correctedDestination) > 0:
                    gotlocation = 2
                    corrected = correctedDestination[0]
                    locationField = 'destination'
                elif len(correctedPlace) > 0:
                    gotlocation = 3
                    corrected = correctedPlace[0]
                    locationField = 'place'
                else:
                    # in case of no match with region, destination or place
                    detectedRegion = findCorrectLocation(word)
                    gotlocation = 0
                    # ugly fix: take only the first word of region and LOWERCASE it! - it doesn't work because region is made of more than one word???
                    detectedRegionSplit = detectedRegion.split()
                    corrected = detectedRegionSplit[0].lower()
                    locationField = 'regionName'
                
                if not gotlocation == 0:
                    analyzedText[i] = corrected
                if locationField and corrected:
                    allowLocation = Term(locationField, corrected)


            # other words - check corrections of 'type' field
            else:
                allowType = None
                correctedType = correctorType.suggest(word, limit=1, prefix=2)
                print(word, 'suggestions for type:', correctedType)
                if len(correctedType) > 0:
                    analyzedText[i] = correctedType[0]
                    allowType = Term("type", correctedType[0].lower())


        # turn list back to string
        text = ' '.join(analyzedText)

        return text, gotlocation, allowLocation, allowType, locationField, corrected



def joinFilters(filter1, filter2):
    
    # filter results: http://whoosh.readthedocs.io/en/latest/searching.html#combining-results-objects
    # print('Filters:', filter1, filter2)

    # put together a filter query
    if filter1 and filter2:
        filter = And([filter1, filter2])
    elif filter1:
        filter = filter1
    elif filter2:
        filter = filter2
    else:
        filter = None
    print('Filter:', filter)

    return filter



def findCorrectLocation(word):

    # search for word that is supposed to be a location (and does not match neither region, destination or place), determine region based on Region of most hits for a given word
    numOfResults = 30
    results = searchIndex(index, word, numOfResults, None)

    placesRegion = dict()
    max = 0
    maxName = None

    for i, key in enumerate(results):
        resultRegion = results[key]['regionName']
        placesRegion, max, maxName = countRegion(placesRegion, resultRegion, max, maxName)



    print('Region suggestion:', maxName)
    return maxName;



def countRegion(placesRegion, result, max, maxName):

    # just a helper method for 'findCorrectLocation'
    # if region already in 'placesRegion' increase count by 1, else add it to dict

    exists = False
    for key in placesRegion:
        if key == result:
            placesRegion[key]['count'] +=1
            exists = True
            if placesRegion[key]['count'] > max:
                max = placesRegion[key]['count']
                maxName = key

    if exists == False:
        placesRegion[result] = {'count': 1}
        if placesRegion[result]['count'] > max:
            max = placesRegion[result]['count']
            maxName = result

    return placesRegion, max, maxName





# only run once, to build index
#init()

# testing search
index = open_dir("index")
#results = analyzeQuery(index, 'seznam gradov na dolenjskem')
#results = analyzeQuery(index, 'seznam jezer na koroškem')
#results = analyzeQuery(index, 'reke pri ljubljani') #!!!!
#results = analyzeQuery(index, 'reke v notranjskem')   #!!!

results = analyzeQuery(index, 'kmetije v ljubljani')
results = analyzeQuery(index, 'arhitekturna dediščina v ljubljani')
results = analyzeQuery(index, 'lovrenška jezera')
results = analyzeQuery(index, 'reke na primorskem')
results = analyzeQuery(index, 'kmetija na dolenjskem')
results = analyzeQuery(index, 'kmetije na morje')




# TO-DO: check search query for special words ("seznam,..") and return list of hits (first 10 for example); "seznam jezer na gorenjskem"

# TO-DO: make variations of word, dummy way? --> use 'did u mean method!!'
#wordCorrector(index, 'jezera na gorenjskem')