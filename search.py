#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import collections
import pickle
import Levenshtein

from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, OrGroup, QueryParser
from whoosh.analysis import *
from whoosh.query import *
from whoosh.spelling import ListCorrector
from slovenia_info_scra import Attraction, Region, Town


# this only works for user queries in slovenian language

# WARNING: to be able to get suggestions, all list must be SORTED!

# list of special words we'd like to detect to show more than one result
# SLO
countryList = sorted(['dežela', 'država', 'slovenija', 'deželi'])
nearByList = sorted(['okolici', 'bližini', 'blizu', 'okolišu', 'občini'])
znamenitostiList = sorted(['znamenitosti', 'zanimivosti', 'atrakcije'])
specialWords = sorted(['seznam', 'tabela'])
commonWords = sorted(['kaj', 'kje', 'kako', 'povej', 'mi', 'pokaži', 'veš', 'lahko', 'je', 'prikaži', 'morda', 'tej', 'ali', 'poznaš'])
prepositions = sorted(['na', 'v', 'ob', 'pri', 's', 'z', 'bližini', 'blizu', 'zraven'])



# schema for attribute entries
attrSchema = Schema(id=ID(stored=True),
                    name=TEXT(stored=True, field_boost=1.5),
                    link=ID(stored=True),
                    address=TEXT,
                    phone=KEYWORD(commas=True),
                    webpage=ID(stored=True),
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
                    topResult=BOOLEAN(stored=True),
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
            topResult=False,
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
            type='regije',
            topResult=False,
            typeID='region'
        )
        
    writer.commit()

    return


def findMatch(index, query):

    # using whole query we try to find requested town/region/attraction in query
    print('Starting with "findMatch", user query is:', query)

    # proccess text and look for suggestions in names
    # we need to recognize variations - ljubljana, ljubljani, ljubljano,...
    newQueryList = processText(query, commonWords, mode=1)
    newQueryList, lastCorrection = getSuggestionWord(index, newQueryList, 'name', mode=1)

    # check if any word in query matches a place in a static list with all slovenian towns
    # TODO: think hard if we really need to do this
    isPlace = False
    placeName = None
    placeIndex = -1
    for i, word in enumerate(newQueryList):
        if word in townsStatic:
            isPlace = True
            placeIndex = i
            placeName = word    # TODO: need some extra requirements?

    processedQuery = ' '.join(newQueryList)
    print('Starting search with query:', processedQuery)

    # search
    results = searchIndex(index, processedQuery, 1)
    isExactMatch = False
    remainingWords = None
    if len(results) > 0:

        # if no match was found in a list with all slo towns
        # compare result's name, place and destination with user query (but, BUT, we remove common words before that)
        # get the closest one
        # for example: query 'povej mi kaj je na bledu' will return 'veseli december na bledu', but we want only 'Bled'
        closestString = None
        result = results[0]
        if not placeName and result['name'] != result['place']:
            locations = [result['name'], result['place'], result['destination'], result['regionName']]
            closestString = selectClosestString(locations, processText(processedQuery, commonWords, mode=2))
            print('Closest find:', closestString)
            # TODO: something with that, also use 'isPlace', 'placeIndex',...
            # TODO: return the closest one? 'povej mi kaj o bledu'

    else:
        print('No hits, correcting query and searching again')
        suggestedProcessedQueryList, suggestion = getSuggestionWord(index, newQueryList, 'name')
        suggestedProcessedQuery = ' '.join(suggestedProcessedQueryList)
        results = searchIndex(index, suggestedProcessedQuery, 1)

    if len(results) > 0:
        # remove matching words from original query by using hit's name as stoplist
        nameList = processText(results[0]['name'])
        remainingWords = processText(processedQuery, nameList)
        print('Remaining words after removing hit words:', remainingWords)

        # check for exact match by comparing strings
        print('Compare names:', nameList, newQueryList)
        if ' '.join(nameList) == ' '.join(newQueryList):
            isExactMatch = True

    print('\n')
    # TODO: something smart with "other words"
    return results, remainingWords, isExactMatch, placeName


def selectClosestString(list, string):

    # using Levenshtein distance, return word from a given list that is closest to a given string
    best = None
    bestRatio = 0
    for word in list:
        ratio = Levenshtein.ratio(word, string)
        #print(word, ';', string, '- ratio:', ratio)

        if ratio > bestRatio:
            bestRatio = ratio
            best = word

    return best


def processText(str, stopWords=None, mode=1):

    # returns cleaned up text; if mode == 1, return list; if mode == 2, return string

    # remove special characters
    # TODO. not ok, also removes ščž..
    # str = re.sub('[^a-zA-Z0-9 \n\.]', '', str)

    # next we use standard analyzer which composes a RegexTokenizer with a LowercaseFilter and optional StopFilter
    # (docs: 'http://whoosh.readthedocs.io/en/latest/api/analysis.html#analyzers')
    sa = StandardAnalyzer(stoplist=stopWords)
    strList = [token.text for token in sa(str)]

    if mode == 1:
        return strList
    elif mode == 2:
        return ' '.join(strList)


def calculatePrefix(word):

    # this is not meant for correcting user mistakes, but for stemming variations of words

    # default
    variationLength = 3

    wordLen = len(word)
    if wordLen == 0:
        prefix = 0
    elif wordLen < 4:
        prefix = wordLen - 1
    elif wordLen < 6:
        prefix = wordLen - 2
    else:
        prefix = wordLen - variationLength

    return prefix


def getSuggestionWord(index, query, field, prefix=-1, maxDist=3, mode=1):

    # returns new query by checking each word in original query list and correcting it (if needed) with word
    # from a given field (mode=1)/ list (mode=2)
    # if prefix == -1, automatically calculate prefix for a given word; else, use prefix set by user

    print('Getting suggestions for each word.')

    correction = None
    with index.searcher() as s:

        if mode == 1:
            corrector = s.corrector(field)
        elif mode == 2:
            corrector = ListCorrector(field)

        for i, word in enumerate(query):
            if len(word) > 2:

                # gradually increase maxdist --> don't know why we need to do this
                # there seems to be a bug/feature in whoosh
                # for bigger maxdist, not always is the closest suggestion selected??
                # example: word = goricko, maxdist=1 suggestion=goričko, maxdist=2 suggestion=gori
                # probably returns the most frequent word for given restraints?
                for j in range(0, maxDist+1):
                    if prefix == -1:
                        corrected = corrector.suggest(word, limit=1, prefix=calculatePrefix(word), maxdist=j)

                    else:
                        corrected = corrector.suggest(word, limit=1, prefix=prefix, maxdist=j)

                    if len(corrected) > 0:
                        print('Swapping words:', query[i], corrected[0])
                        query[i] = corrected[0]
                        correction = corrected[0]
                        break

    return query, correction


def getSuggestionQuery(index, query, field):

    # returns new query by correcting the old one using correct_query

    qp = QueryParser(field, schema=index.schema)
    parsedQuery = qp.parse(query)
    with index.searcher() as s:
        corrected = s.correct_query(parsedQuery, query, prefix=1, maxdist=2)
        print('Suggestion for query:', corrected.string)

    return corrected.string


def getLocationSuggestion(queryList, prefix=-1):

    # firs we look for suggestions on the list of all slovenian towns
    # if there is a match, we swap it with original word
    # if prefix == -1, automatically calculate prefix for a given word; else, use prefix set by user

    correction = None
    correctorList = ListCorrector(townsStatic)
    for i, word in enumerate(queryList):
        if len(word) > 2:
            if prefix == -1:
                corrected = correctorList.suggest(word, limit=1, prefix=calculatePrefix(word), maxdist=2)
            else:
                corrected = correctorList.suggest(word, limit=1, prefix=prefix, maxdist=2)

            if len(corrected) > 0:
                print('Swapping words from list:', queryList[i], corrected[0])
                queryList[i] = corrected[0]
                correction = corrected[0]

    return queryList, correction


def searchIndex(index, newText, resultLimit=1, filterQuery=None):

    #print('Tekst', newText)
    # search for a given string
    with index.searcher() as searcher:

        # using MultifieldParser to search all relevant fields

        # in case of multiple words in query, use OR (query: 'lake bled' => 'lake' OR 'bled')
        # boost score of items that contain both tokens
        orGroup = OrGroup.factory(0.9)
        query = MultifieldParser(["name", "type", "regionName", "description", "tags", "topResult", "destination", "place"], index.schema, group=orGroup).parse(newText)
        results = searcher.search(query, limit=resultLimit, terms=True, filter=filterQuery)
        print('Number of hits:', len(results))

        # saving hits (only hits with score bigger than 0.5 - topResult value) to the ordered dict, so we can return it
        dict = collections.OrderedDict()

        hasResult = False
        for i, result in enumerate(results):
            if (result['topResult'] and float(results.score(i)) > 0.5) or (not result['topResult'] and float(results.score(i)) > 0):
                hasResult = True
                print(result['name'], ',', result['place'], ',', result['destination'], ',', result['regionName'], ',', result['type'], ',', result['webpage'], '; ', 'SCORE:', results.score(i), 'MATCHED TERMS:', result.matched_terms())
                dict[i] = {'id': result['id'], 'name': result['name'], 'link': result['link'], 'type': result['type'], 'regionName': result['regionName'], 'destination': result['destination'], 'place': result['place'], 'typeID': result['typeID'], 'description': result['description'], 'webpage': result['webpage'], 'exactHit': False, 'suggestion': False, 'suggestionText': None, 'score': results.score(i)}

        if hasResult == False:
            print('___ NO RESULTS ___')

        return dict


def analyzeQuery(index, query, locationAssistant=None):

    # search starts here
    print('Original search query:', query, '\n')

    # simulating test data
    # MUST be lowercase!
    locationAssistant = 'Ljubljana'
    locationAssistant = locationAssistant.lower()

    # check for empty / non-existent query
    if not query or query.isspace():
        print('Nothing to search for, query is empty.')
        return {}

    # before we start with analysis, let's check if there is a hit that matches search query word for word in title
    # if there is, return it immediately
    # if its not exact hit (word for word in title), save it for later
    resultHit, exactHit = checkOneHit(index, query)
    if exactHit:
        #set a flag for exact hit
        resultHit[0]['exactHit'] = True

        print('RETURNING:', resultHit[0]['name'], ',', resultHit[0]['place'], ',', resultHit[0]['destination'], ',',
              resultHit[0]['regionName'], ',', resultHit[0]['type'], ', exactHit:', resultHit[0]['exactHit'])
        print('-------------------------------------------------------------------------------------------------\n\n\n')
        return resultHit

    # find a location match (from a list with all slovenian towns)
    resultHit, remainingWords, exactHit, correction = findMatch(index, query)

    # if there was no exact hit (query == name of first result), we try to do some smart things
    # use standard analyzer which composes a RegexTokenizer with a LowercaseFilter and optional StopFilter
    # (docs: 'http://whoosh.readthedocs.io/en/latest/api/analysis.html#analyzers')
    sa = StandardAnalyzer(stoplist=specialWords)
    print('Special words: ', [(token.text, token.stopped) for token in sa(query, removestops=False)])

    # look for stopwords ('seznam', 'tabela') or plural form to decide if user wants more than one result
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
            # also check that 'token.text' is not a slovenian town, because
            # some types are names of towns, for example there is a type 'ljubljana'
            elif len(token.text) > 2 and len(correctorType.suggest(token.text, limit=1, maxdist=0, prefix=calculatePrefix(token.text))) > 0 and not token.text in townsStatic:
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
        text, gotLocation, locationFilter, typeFilter, correctedLocation, globalFilter = multipleResultsAnalyzer(index, text)

        # in case we already have a location match from 'findMatch', we'd rather use that since we know it definitely
        # matches a place in Slovenia
        #if correction:
        #   locationFilter = Term('place', correction)
        #   gotLocation = 2
        #   correctedLocation = correction

        # if no location filter is set yet, use the default one (if available)
        # - except when we don't want one (when user adds '...v Sloveniji' or similar)
        if locationFilter == None and globalFilter is False:
            locationFilter = setDefaultLocationFilter(locationAssistant, 'place')
            gotLocation = 2
            correctedLocation = locationAssistant

        filterQuery = joinFilters(typeFilter, locationFilter)

    else:
        # since we now know user wants just one hit, we can return the one we saved earlier, from 'findMatch' method
        if len(resultHit) > 0:
            print('RETURNING:', resultHit[0]['name'], ',', resultHit[0]['place'], ',', resultHit[0]['destination'], ',', resultHit[0]['regionName'], ',', resultHit[0]['type'], ', exactHit:', resultHit[0]['exactHit'])

        else:
            print('RETURNING: no hits :(')

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
            # TODO: don't do this if you already got the object from 'findMatch'
            newLocationFilter, fieldOptions = changeLocationFilter(index, correctedLocation, locationFilter)

            while len(hits) == 0 and gotLocation > -1:

                if newLocationFilter[gotLocation-1] != None and newLocationFilter[gotLocation-1] != '':

                    if gotLocation == 0:
                        # if nothing was found using location filter, try without it
                        newFilter = None

                    else:
                        newFilter = Term(fieldOptions[gotLocation-1], fixFilter(newLocationFilter[gotLocation-1]))

                    filterQuery = joinFilters(typeFilter, newFilter)
                    hits = searchIndex(index, text, limit, filterQuery)

                gotLocation -= 1

    # set 'exactHit' to True for weighting purposes on client side if hits ain't empty
    if len(hits) > 0:
        hits[0]['exactHit'] = True

    print('RETURNING:', hits)
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
    print('checkOneHit: is there an item that matches search query word for word?')

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

    print('\n')
    return hit, exactHit


def multipleResultsAnalyzer(index, text):

    # here we try to do all the smart things to make search more accurate when we want more than one result
    print('MULTIPLE RESULTS ANALYZER')

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
        correctorAttractions = ListCorrector(znamenitostiList)
        gotlocation = -1                        # 0 = region, 1 = destination, 2 = place
        allowLocation = None                    # location filter
        allowType = None                        # type filter
        isLocation = False
        isType = False
        nameSingular = None
        addToQuery = None
        correctedLocation = None
        noFilter = False
        globalFilter = False                    # special case where we don't want default location filter

        # no preposition means no info on what is type and what is location
        if locationIndex == -1:
            print('No location index!')

        # LOCATION FILTER
        for j, word in enumerate(analyzedText):
            if j == locationIndex:
                fullLocation = ' '.join(analyzedText[j:len(analyzedText)])
                fullLocationList = analyzedText[j:len(analyzedText)]
                locationList = ['regionName', 'destination', 'place']
                filterSlovenia = ListCorrector(countryList)
                filterNearBy = ListCorrector(nearByList)

                # if we detect word from list 'countryList', we intentionally want location filter to be 'None'
                # check each word in part we think represents location (part after preposition) for a match with list
                print('full location string:', fullLocationList)
                for w in fullLocationList:
                    suggestionCountry = filterSlovenia.suggest(w, limit=1, prefix=1, maxdist=2)     # something weird: dežela, deželi???
                    suggestionNearBy = filterNearBy.suggest(w, limit=1, prefix=1, maxdist=2)
                    print('Suggestions: country -', suggestionCountry, '; nearby -', suggestionNearBy)

                    if len(suggestionCountry) > 0:
                        noFilter = True
                        globalFilter = True
                        break

                    elif len(suggestionNearBy) > 0:
                        noFilter = True
                        break

                if not noFilter:
                    print('Setting location filter')
                    for i, location in enumerate(locationList):
                        qp = QueryParser(location, schema=index.schema)
                        qLocation = qp.parse(fullLocation)
                        corrected = s.correct_query(qLocation, fullLocation, prefix=2, maxdist=2)   # prefix doesn't work..BUG?
                        print('Location filter suggestion '+location+':', corrected.string)

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

                else:
                    # remove unnecessary words in query
                    analyzedText = analyzedText[0:j]

            # TYPE FILTER
            # other words - check corrections of 'type' field
            elif isType is False and len(word) > 1:
                correctedType = correctorType.suggest(word, limit=1, prefix=2)
                correctedName = correctorName.suggest(word, limit=1, prefix=2, maxdist=3)
                correctedAttractions = correctorAttractions.suggest(word, limit=1, prefix=2)
                print(word, 'suggestions for type:', correctedType)
                print(word, 'suggestions for type name:', correctedName)
                print('filter for attractions:', correctedAttractions)

                if len(correctedAttractions) > 0:
                    # if a word matches something like 'znamenitosti', we want to return all attractions
                    # set type filter accordingly (read as: no type filter)
                    # TODO: exclude some types?
                    pass

                elif len(correctedType) > 0:
                    isType = True
                    analyzedText[j] = correctedType[0]
                    allowType = Term('type', fixFilter(correctedType[0]))

                    # also add things from type 'vredno ogleda' and 'Biseri narave' that have matching name
                    # (some items have type 'vredno ogleda', instead of their real type,
                    # for example, 'Ljubljanski grad' - instead, we search for 'grad')
                    if len(correctedName) > 0:
                        nameSingular = correctedName[0]
                        additionalTypeName = Term('name', correctedName[0])

                        # vredno ogleda
                        addType = 'vredno'
                        additionalType = Term('type', addType)
                        additionalTypeFilter = And([additionalType, additionalTypeName])

                        # biseri narave
                        addType2 = 'biseri'
                        additionalType2 = Term('type', addType2)
                        additionalTypeFilter2 = And([additionalType2, additionalTypeName])

                        # join with regular type filter
                        allowType = Or([allowType, additionalTypeFilter, additionalTypeFilter2])


        # if we find a name in singular, add it to the query list
        if nameSingular:
            analyzedText.append(nameSingular)

        # turn list back to string
        text = ' '.join(analyzedText)
        print(text)

        print('\n')
        return text, gotlocation, allowLocation, allowType, correctedLocation, globalFilter


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


def setDefaultLocationFilter(location, field):

    # set filter with location reported from assistant (for localized search in nearby area)

    if location is None or location == '':
        return None

    locationFilter = Term(field, location)

    return locationFilter



# only run once, to build index
#init()

# testing search
index = open_dir("../index")

# get slovenian towns from file
with open('../kraji_slovenija', 'rb') as fp:
    townsStatic = pickle.load(fp)


#results = analyzeQuery(index, 'seznam rek ob morju')
#results = analyzeQuery(index, 'znamenitosti v blizini')
#results = analyzeQuery(index, 'seznam arhitekture')
#results = analyzeQuery(index, 'grat')

#results = analyzeQuery(index, 'povej mi kaj o novem mestu') #!!!!
#results = analyzeQuery(index, 'povej mi kaj o bledu')
#results = analyzeQuery(index, 'arhitektura ljubljana')
#results = analyzeQuery(index, 'ljubljna')   #!!!