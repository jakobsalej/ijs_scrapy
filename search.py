import os
import collections

from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, OrGroup, QueryParser
from whoosh.analysis import *
from whoosh.query import *
from slovenia_info_scra import Attraction, Region, Town


# this only works for user queries in slovenian language

# list of special words we'd like to detect to show more than one result
# SLO
specialWords = ['seznam', 'tabela']
prepositions = ['na', 'v', 'ob', 'pri', 's', 'z', 'bližini', 'blizu', 'zraven']


# schema for attribute entries
attrSchema = Schema(id=ID(stored=True),
                    name=TEXT(stored=True, field_boost=1.5),
                    link=ID(stored=True),
                    address=TEXT,
                    phone=KEYWORD(commas=True),
                    webpage=ID,
                    tags=KEYWORD(commas=True, scorable=True, lowercase=True, stored=True),
                    type=KEYWORD(stored=True, field_boost=1.2, lowercase=True, scorable=True),
                    description=TEXT(field_boost=0.01, stored=True),
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
            regionName=region.name,    # just for displaying results, doesn't matter
            destination='',
            place='',
            type='region',
            typeID='region'
        )
        
    writer.commit()

    return



def searchIndex(index, newText, resultLimit, filterQuery):

    # search for a given string
    with index.searcher() as searcher:
        # using MultifieldParser to search all relevant fields

        # in case of multiple words in query, use OR (query: 'lake bled' => 'lake' OR 'bled')
        # boost score of items that contain both tokens
        orGroup = OrGroup.factory(0.9)
        query = MultifieldParser(["name", "type", "regionName", "description", "tags", "topResult", "destination", "place"], index.schema, group=orGroup).parse(newText)
        results = searcher.search(query, limit=resultLimit, terms=True, filter=filterQuery)
        print('Number of hits:', len(results))


        # saving hits (only hits with score bigger than 0) to the ordered dict, so we can return it
        # http://stackoverflow.com/questions/19477319/whoosh-accessing-search-page-result-items-throws-readerclosed-exception
        dict = collections.OrderedDict()

        hasResult = False
        for i, result in enumerate(results):
            if float(results.score(i)) > 0:
                hasResult = True
                print(result, 'SCORE:', results.score(i), 'MATCHED TERMS:', result.matched_terms())
                dict[i] = {'id': result['id'], 'name': result['name'], 'link': result['link'], 'type': result['type'], 'regionName': result['regionName'], 'destination': result['destination'], 'place': result['place'], 'typeID': result['typeID'], 'description': result['description'], 'suggestion': False, 'suggestionText': None, 'score': results.score(i)}

        if hasResult == False:
            print('___ NO RESULTS ___')

        return dict



def analyzeQuery(index, query):

    print('Original search query:', query)

    # check for empty / non-existent query
    if not query or query.isspace():
        print('Query is empty.')
        return {}

    # before we start with analysis, let's check if there is a hit that matches search query word for word in title
    # if there is, return it immediately
    # if its not exact hit (word for word in title), save it for later
    resultHit, exactHit = checkOneHit(index, query)
    if exactHit:
        print('-------------------------------------------------------------------------------------------------\n\n\n')
        return resultHit

    # if there was no exact hit (query == name of first result), we try to do some smart things
    # use standard analyzer which composes a RegexTokenizer with a LowercaseFilter and optional StopFilter
    # (docs: 'http://whoosh.readthedocs.io/en/latest/api/analysis.html#analyzers')
    sa = StandardAnalyzer(stoplist=specialWords)
    print('Special words: ', [(token.text, token.stopped) for token in sa(query, removestops=False)])

    # look for stopwords (seznam, tabela) or plural form to decide if user wants more than one result
    limit = 1
    newQuery = []
    with index.searcher() as s:
        correctorType = s.corrector('type')
        for token in sa(query, removestops=False):
            # len(token.test) > 1 is needed as Whoosh automatically removes all words that are only one letter long,
            # but we need them as prepositions (s, z, v)
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

    # if limit = 10, we want to make search a bit more general because a stopword/plural was detected, since we need
    # more results based on type, not name (probably)
    filterQuery = None
    if limit == 10:
        text, gotLocation, locationFilter, typeFilter, correctedLocation = multipleResultsAnalyzer(index, text)
        filterQuery = joinFilters(typeFilter, locationFilter)
    else:
        # since we now know user wants just one hit, we can return the one we saved earlier, from 'checkOneHit' method
        print(resultHit)
        print('---------------------------------------------------------------------------------------------\n\n\n\n\n')
        return resultHit

    print('New user query after analysis:', text)

    # get results; if empty, change location filters
    hits = searchIndex(index, text, limit, filterQuery)
    if len(hits) == 0:
        if limit == 1:
            print('No hits!')
        # more-than-one-result search
        elif limit == 10:
            # returns 3 location filter options: place, destination, region; if there are still no results
            # after applying them, remove location filter completely
            newLocationFilter, fieldOptions = changeLocationFilter(index, correctedLocation, locationFilter)

            while len(hits) == 0 and gotLocation > -1:
                if newLocationFilter[gotLocation-1] != None and newLocationFilter[gotLocation-1] != '' :
                    if gotLocation == 0:
                        # if nothing was found using location filter, try without it
                        newFilter = None
                    else:
                        newFilter = Term(fieldOptions[gotLocation-1], fixFilter(newLocationFilter[gotLocation-1]))

                    filterQuery = joinFilters(typeFilter, newFilter)
                    hits = searchIndex(index, text, limit, filterQuery)

                gotLocation -= 1

    print('-------------------------------------------------------------------------------------------------')
    print('-------------------------------------------------------------------------------------------------\n\n\n\n\n')
    return hits



def changeLocationFilter(index, correctedLocation, locationFilter):

    # based on locationFilter, get other fields (if available): region, destination, place
    # (we have one already from the filter and we use that one for search)
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

    # let's check if there is a hit that matches search query word for word in title

    # tokenizer, lowercase filters
    sa = StandardAnalyzer(stoplist=None)
    parser = QueryParser("name", schema=index.schema)
    newQuery = []
    exactHit = False

    # did we change user query? (corrected typos...)
    suggestion = False
    suggestionText = None

    # check for typos
    with index.searcher() as s:
        for token in sa(query):
            newQuery.append(token.text)

        newQuery = ' '.join(newQuery)
        filterName = parser.parse(newQuery)
        correctedName = s.correct_query(filterName, newQuery, prefix=2, maxdist=2)
        if correctedName.query != filterName:
            filterName = correctedName.query
            newQuery = correctedName.string
            suggestion = True       # correcting user typos!
            suggestionText = newQuery

    print(filterName)
    hit = searchIndex(index, newQuery, 1, filterName)

    # check again if name is exactly the same as search query; first we have to lowercase all words
    for key in hit:
        # if field 'suggestion' is TRUE, user should be asked "Did you mean [suggestionText]?"
        hit[key]['suggestion'] = suggestion
        hit[key]['suggestionText'] = suggestionText

        hitName = []
        for token in sa(hit[key]['name']):
            hitName.append(token.text)
        hitName = ' '.join(hitName)
        print('Comparing names:', newQuery, hitName)
        if hitName == newQuery:
            print('EXACT MATCH!!')
            exactHit = True

    return hit, exactHit



def multipleResultsAnalyzer(index, text):

    # here we try to do all the smart things to make search more accurate when we want more than one result

    # look for any prepositions and remove them (as stopwords)
    sa = StandardAnalyzer(stoplist=prepositions)
    analyzedText = []
    
    # here we save an index of a word that's probably a location
    # (we assume location follows a preposition: "arhitektura na gorenjskem");
    # in case there is more than one preposition, we take index of the last one
    locationIndex = -1
    for i, token in enumerate(sa(text, removestops=False)):
        if token.stopped == True:
            if locationIndex == -1:
                locationIndex = i
        else:
            analyzedText.append(token.text)

    print(analyzedText)

    # as we try to turn words in a more 'general' form, we look in the regionName and tags fields for
    # potential 'corrections' of our words in query, using "Did you mean..." method from Whoosh

    with index.searcher() as s:
        correctorType = s.corrector('type')
        correctorName = s.corrector('name')
        gotlocation = -1                        # 0 = region, 1 = destination, 2 = place
        allowLocation = None                    # location filter
        allowType = None                        # type filter
        isLocation = False
        isType = False
        nameSingular = None
        addToQuery = None
        correctedLocation = None

        # no preposition means no info on what is type and what is location
        if locationIndex == -1:
            print('No locatin index!')
            # TODO: improve detection of location / type


        for j, word in enumerate(analyzedText):
            if j == locationIndex:
                fullLocation = ' '.join(analyzedText[j:len(analyzedText)])

                locationList = ['regionName', 'destination', 'place']
                for i, location in enumerate(locationList):
                    qp = QueryParser(location, schema=index.schema)
                    qLocation = qp.parse(fullLocation)
                    corrected = s.correct_query(qLocation, fullLocation, prefix=2, maxdist=2)
                    if corrected.query != qLocation:
                        analyzedText[j:len(analyzedText)] = corrected.string.split()    # replace location in query with corrected version
                        allowLocation = corrected.query                                 # set location filter, starting from broader to smaller (region -> place)
                        gotlocation = i                                                 # save location field index
                        correctedLocation = corrected.string                            # save corrected name

                if not allowLocation:
                    # in case of no match with region, destination or place, do a look up for region
                    selectedRegions = findCorrectLocation(index, word)
                    gotlocation = 0
                    locationField = 'regionName'
                    allowLocation = joinTerms(locationField, selectedRegions)


            # other words - check corrections of 'type' field
            elif isType is False and len(word) > 1:
                correctedType = correctorType.suggest(word, limit=1, prefix=2)
                correctedName = correctorName.suggest(word, limit=1, prefix=2, maxdist=3)
                print(word, 'suggestions for type:', correctedType)
                print(word, 'suggestions for type name:', correctedName)
                if len(correctedType) > 0:
                    isType = True
                    analyzedText[j] = correctedType[0]
                    allowType = Term('type', fixFilter(correctedType[0]))

                    # also add things from type 'vredno ogleda' that have matching name
                    # (some items have type 'vredno ogleda', instead of their real type,
                    # for example, 'Ljubljanski grad' - instead, we search for 'grad')
                    if len(correctedName) > 0:
                        nameSingular = correctedName[0]
                        addType = 'vredno'
                        additionalType = Term('type', addType)
                        additionalTypeName = Term('name', correctedName[0])
                        additionalTypeFilter = And([additionalType, additionalTypeName])
                        print(additionalTypeFilter)

                        # join with regular type filter
                        allowType = Or([allowType, additionalTypeFilter])


        # if we find a name in singular, add it to the query list
        if nameSingular:
            analyzedText.append(nameSingular)

        # turn list back to string
        text = ' '.join(analyzedText)

        return text, gotlocation, allowLocation, allowType, correctedLocation



def joinTerms(type, list):

    # join more terms

    termList = []
    for word in list:
        newTerm = Term(type, fixFilter(word))
        termList.append(newTerm)

    joinedTerm = Or(termList)
    print(termList)
    print(joinedTerm)

    return joinedTerm



def fixFilter(string):

    # ugly fix: take only the first word of filter and LOWERCASE it!
    # TODO: fix that ugly fix with correct use of terms
    stringSplit = string.split()
    fixed = stringSplit[0].lower()

    return fixed



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



def findCorrectLocation(index, word):

    # search for word that is supposed to be a location (and does not match neither region, destination or place),
    # determine region based on Region of most hits for a given word
    print('-----------------------------\nSELECTING REGIONS:\n')

    numOfResults = 50
    results = searchIndex(index, word, numOfResults, None)
    placesRegion = dict()

    for i, key in enumerate(results):
        if results[key]['score'] > 0:
            resultRegion = results[key]['regionName']
            placesRegion = countRegion(placesRegion, resultRegion)

    print(placesRegion)
    selectedRegions = selectRegions(placesRegion)
    print('------------------------------\n')

    return selectedRegions



def countRegion(placesRegion, result):

    # just a helper method for 'findCorrectLocation'
    # if region already in 'placesRegion' increase count by 1, else add it to dict

    exists = False
    for key in placesRegion:
        if key == result:
            placesRegion[key]['count'] += 1
            exists = True

    if exists == False:
        placesRegion[result] = {'count': 1}

    return placesRegion



def selectRegions(regionCount):

    selectedRegions = []
    countAll = 0
    regionNum = 0
    for key in regionCount:
        regionNum += 1
        countAll += regionCount[key]['count']

    if regionNum > 0:
        average = countAll/regionNum
    else:
        average = 0

    threshold = 0.2
    print('Number of regions:', regionNum, '; number of all votes:', countAll, '- average:', average)

    for key in regionCount:
        if regionCount[key]['count'] > countAll*threshold:
            selectedRegions.append(key)

    print('Selected regions:', selectedRegions)
    return selectedRegions





# only run once, to build index
#init()

# testing search
index = open_dir("index")

# TODO: find a way to distinguish between location and type?
#results = analyzeQuery(index, 'seznam arhitekturne dediščine na gorenjskem')
#results = analyzeQuery(index, 'reke ljubljana')     # TODO: improve this query!
results = analyzeQuery(index, 'lovrenška jezera')
results = analyzeQuery(index, 'grat')

#results = analyzeQuery(index, 'seznam gradov pri novem mestu') #!!!!
#results = analyzeQuery(index, 'reke na primorskem')   #!!!


# TODO: build database again
# TODO. maybe add dynamic prefix to improve search results? (in places where we only look for variations of words)
