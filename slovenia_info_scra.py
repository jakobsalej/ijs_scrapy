from lxml import html, etree
import requests
import time
from models import *



# getting data from webpage www.slovenia.info using lxml and Xpath
# using ORM 'peewee': http://docs.peewee-orm.com/en/latest/index.html
# postgreSQL database

baseUrl = "http://www.slovenia.info"
baseUrlPictures = "http://www.slovenia.info/"
topResults = []

regionLog = None
attrLog = None
townLog = None

# select language: 1 = SLO, 2 = English, 3 = Deutsch, 4 = Italiano, 5 = Français, 6 = Pусский, 7 = Español
lng = 1



def prepareLogFiles():
    global regionLog, attrLog, townLog

    # log files
    regionLog = open('region_errors.log', 'w')
    attrLog = open('attr_errors.log', 'w')
    townLog = open('town_errors.log', 'w')

    return



def getRegion(name):

    # find Region by name in db

    try:
        region = Region.get(Region.name == name)
        #print('Getting region', region.name)
        return region

    except:
        print('ERROR: No such entry found.')
        return None



def getAttraction(link):

    # find Attraction by link (unique for every attr.) in db

    try:
        attraction = Attraction.get(Attraction.link == link)
        print('Getting attraction', attraction.name)
        return attraction

    except:
        print('ERROR: No such entry found.')
        return None



def addTowns():

    # one page that contains links of all the cities and places
    # added lng param so we can simply choose lng
    towns = 'http://www.slovenia.info/si/Mesta-in-kraji.htm?_ctg_kraji=0&lng=' + str(lng)
    pageGetLinks(towns, None)



def selectRegion():

    # Gorenjska, Goriška, Obalno - kraška, Osrednjeslovenska, Podravska, Notranjsko - kraška, Jugovzhodna Slovenija, Koroška, Savinjska, Pomurska, Spodnjeposavska, Zasavska
    # without lng param in url, we add it later

    regions = [
        #'http://www.slovenia.info/si/Regije/Gorenjska.htm?_ctg_regije=10&lng=',
        #'http://www.slovenia.info/si/Regije/Gori%C5%A1ka-Smaragdna-pot.htm?_ctg_regije=9&lng=',
        #'http://www.slovenia.info/si/Regije/Obalno-kra%C5%A1ka.htm?_ctg_regije=17&lng=',
        #'http://www.slovenia.info/si/Regije/Osrednjeslovenska.htm?_ctg_regije=11&lng=',
        #'http://www.slovenia.info/si/Regije/Podravska.htm?_ctg_regije=15&lng=',
        #'http://www.slovenia.info/si/Regije/Notranjsko-kra%C5%A1ka.htm?_ctg_regije=134&lng=',
        #'http://www.slovenia.info/si/Regije/Jugovzhodna-Slovenija.htm?_ctg_regije=13&lng=',
        'http://www.slovenia.info/si/Regije/Koro%C5%A1ka.htm?_ctg_regije=121&lng=',
        'http://www.slovenia.info/si/Regije/Savinjska.htm?_ctg_regije=14&lng=',
        'http://www.slovenia.info/si/Regije/Pomurska.htm?_ctg_regije=16&lng=',
        'http://www.slovenia.info/si/Regije/Spodnjeposavska.htm?_ctg_regije=133&lng=',
        'http://www.slovenia.info/si/Regije/Zasavska.htm?_ctg_regije=12&lng='
    ]

    for region in regions:
        # wait 0.3 sec
        time.sleep(.300)
        # adding lng param
        region = region + str(lng)
        regionGetData(region)

    return



def regionGetData(regionUrl):

    # get data from individual region
    #print('region:', regionUrl)

    try:
        page = requests.get(regionUrl)
        elTree = etree.HTML(page.text)

        # name
        name = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[1]/div[2]/h1/text()')
        print('region name:', name)

        # description
        description = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]')

        # find all relative links in description and replace them with absolute ones
        descriptionFixed = fixLinks(description[0])

        description = etree.tostring(descriptionFixed)
        #print('data:', description)

        # picture link
        pictureLink = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/a/img/@src')
        if len(pictureLink) > 0:
            pictureLink = baseUrlPictures + pictureLink[0]
        #print('link to picture:', pictureLink)

        # attractions link
        attrLinks = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[1]/div[4]/a[4]/@href')
        if len(attrLinks) > 0:
            attrLinks = attrLinks[0]
        #print('attractions:', attrLinks)
        #print('----------------------------------------\n')

        #saving to db
        newRegion = Region(name = name[0], link = regionUrl, description = description, picture = pictureLink)
        newRegion.save()

        # let's get attractions from attraction link
        pageGetLinks(attrLinks, newRegion)

    except Exception as e:
        print('ERROR:', e)
        regionLog.write("ERROR: " + regionUrl + ' : ' + str(e) + '\n')

    print('FINISHED WITH REGION', name, '\n---------------------------------------------\n')

    return



def pageGetLinks(pageUrl, regionObject):

    # get attraction links from [ Home -> Regions -> Some region -> Attractions ] page OR [ Home -> Towns ] page

    page = requests.get(pageUrl)
    tree = html.fromstring(page.content)

    # finds those div-s that are named "resultsBox..", they contain links of attractions (sorted by type: churches, lakes, rivers,..)
    regexpNS = "http://exslt.org/regular-expressions"
    attrGroups = tree.xpath('//*[@id="tdMainCenter"]//div[re:test(@id, "^resultsBox")]', namespaces={'re': regexpNS})
    print('num of groups:', len(attrGroups))

    # we pass on whole tree element so we can extract links (root is div named resultsBox; it contains all links of attractions)
    n = 1
    for node in attrGroups:
        #print(n, ":", node.tag, node.attrib['id'])
        attrLinksList = attractionGroup(node, n)
        print('Starting with group', n, '- number of items:', len(attrLinksList))
        pageAllLinks(attrLinksList, regionObject)
        print('Finished with group', n, '\n---------------------------------------------------------\n')
        n += 1

    return



def attractionGroup(group, n):
    global topResults

    # get all attraction links for specific group (lakes, rivers,...)

    # save links of the top results (n = 1, group 1 is top results) to array, so we can access it later; TO-DO: works even for attractions ('lepote')?
    if n == 1:
        topResults = group.xpath('//div[@class="info"]/a[1]/@href')
        #print('adding TOP link:', topResults)
        #print('No:', len(topResults))

    # first we get all the attraction links from page one (default)
    attrLinksList = []

    # we only need the second link, first one is location of attraction (a[2])
    for link in group.iterfind('div[@class="box2"]/p/a[2]'):
        attrLinksList.append(link.attrib['href'])
        #print('adding link:', link.attrib['href'])

    #print("Number of links in group:", len(attrLinksList))

    # we need selected div's ID because once we load a new link (page two, for example), we have to know which group are we looking at (all the links from other groups are still visible, just collapsed)
    groupId = group.attrib['id']
    #print('ID:', groupId)

    # we look for the links of pages (if there are more than 50 attractions in a group, they are paginated)
    # we don't need to 'click' on the first link (we already have those attractions, they are shown by default)
    count = 0
    for pageLinks in group.iterfind('div[@class="subbox"]/div[@class="paging"]/div[@class="links"]/a'):
        #print("Page link found:", pageLinks.tag, pageLinks.attrib['href'])

        if count != 0:
            # wait 0.3 sec
            time.sleep(.300)

            # adding links from page 2, 3, .. of selected group
            attractionsPage = attrGroupSubPage(pageLinks.attrib['href'], groupId)
            attrLinksList.extend(attractionsPage)
            #print('number of attractions in group:', len(attrLinksList))

        count += 1

    return attrLinksList



def attrGroupSubPage(link, id):

    # find the correct div based on given id, extract links and return them

    fullLink = baseUrl + link
    #print("going to page:", fullLink)

    page = requests.get(fullLink)
    tree = html.fromstring(page.content)

    # search string
    searchStr = '//div[@id="' + id + '"]//p/a[2]/@href'
    #print(searchStr)

    linksPageAttractions = tree.xpath(searchStr)
    #print('new links:', linksPageAttractions)
    #print('number of new links:', len(linksPageAttractions))

    return linksPageAttractions



def pageAllLinks(links, regionObject):

    # now we have links of all the attractions of specific region, lets go through them and get data out

    n = 1
    for link in links:
        fullLink = baseUrl + link
        time.sleep(.300)

        # use regionObject as an identifier between attraction/town type (town has regionObject 'None', all attractions have valid regionObject (not None))
        if regionObject == None:
            townGetData(fullLink, n, len(links))
        else:
            attractionGetData(fullLink, regionObject, n, len(links))
        n += 1

    return



def attractionGetData(attractionUrl, regionObject, n, numLinks):
    global topResults

    # get data from individual attraction
    # print('link:', attractionUrl)

    try:
        page = requests.get(attractionUrl)
        tree = html.fromstring(page.content)
        elTree = etree.HTML(page.text)

        # name of the attraction:
        attractionName = tree.xpath('// *[ @ id = "tdMainCenter"] / div[3] / div[1] / div[4] / h1/text()')
        if len(attractionName) == 0:
            attractionName = ['']

        print(attractionName[0], '(', n, '/', numLinks, ')')

        # address:
        attractionAddress = tree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[1]/div[1]/div[@class="prop propLocation"]/div[2]/text()')
        if len(attractionAddress) == 0:
            attractionAddress = ['']
        #print("address:", attractionAddress)

        # phone:
        attractionPhone = tree.xpath(
            '//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[1]/div[1]/div[@class="prop propPhone"]/div[2]/text()')
        if len(attractionPhone) == 0:
            attractionPhone = ['']
        #print("phone:", attractionPhone)

        # email does not work, problem with js (link is not visible to lxml?)
        attractionEmail = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]')
        #if len(attractionEmail) > 0:
            #print("email:", etree.tostring(attractionEmail[0]))

        # webpage:
        attractionWebpage = tree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[1]/div[1]/div[@class="prop propRow propWWW"]/a/text()')

        # in case link is split, we have to merge it
        attractionWebpage = ''.join(attractionWebpage)
        #print("webpage:", attractionWebpage)

        # webpage path to attraction, we remove the first one as its always "Domov" and save the one before last as it tells as type of attraction
        attractionNavPath = tree.xpath('//*[@id="tdMainCenter"]/div[1]//a/text()')
        attractionType = attractionNavPath[len(attractionNavPath)-2]
        attractionNavPath.pop(0)
        attractionNavPath = ','.join(attractionNavPath)
        #print("navigation path:", attractionNavPath)

        # description:
        attractionDescription = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]')
        #print("raw:,", etree.tostring(attractionDescription[0]))

        # we remove unecessary parts (we only need body text)
        childDiv = attractionDescription[0].find('div')
        #print('Odstranjujem:', etree.tostring(childDiv))
        if childDiv is not None:
            attractionDescription[0].remove(childDiv)

        # if we try to remove picture link, we also remove text -> NOT OK! TO-DO: http://stackoverflow.com/questions/22967659/removing-an-element-but-not-the-text-after-it
        # childLink = attractionDescription[0].find('a')
        # print('Removing:', etree.tostring(childLink))
        # attractionDescription[0].remove(childLink)

        # find all relative links in description and replace them with absolute ones
        attractionDescriptionFixed = fixLinks(attractionDescription[0])
        content = etree.tostring(attractionDescriptionFixed)
        #print("description:", content)

        # main picture: (we have to merge it with base url for full picture url)
        attractionPictureMain = tree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/a/img/@src')
        if len(attractionPictureMain) > 0:
            attractionPictureMain = baseUrlPictures + attractionPictureMain[0]
        #print("link to main picture:", attractionPictureMain)

        # region
        attractionRegion = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row region"]/a/text()')
        if len(attractionRegion) < 1:
            attractionRegion = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row region"]/text()')
            if len(attractionRegion) == 0:
                attractionRegion = ['']
        #print("region:", attractionRegion)

        # destination
        attractionDestination = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row destination"]/a/text()')
        if len(attractionDestination) < 1:
            attractionDestination = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row destination"]/text()')
            if len(attractionDestination) == 0:
                attractionDestination = ['']
        #print("destination:", attractionDestination)

        # place
        attractionPlace = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row place"]/a/text()')
        if len(attractionPlace) < 1:
            attractionPlace = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row place"]/text()')
            if len(attractionPlace) == 0:
                attractionPlace = ['']
        #print("place:", attractionPlace)

        # GPS coordinates
        attractionGPS = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row gps"]/a/text()')
        if len(attractionGPS):
            gpsX = float(attractionGPS[0].replace(',', '.'))
            gpsY = float(attractionGPS[1].replace(',', '.'))
        else:
            gpsX = -1
            gpsY = -1

        #print("gps [x, y]:", attractionGPS)

        # check if it's top result with array we saved in the beginning (by comparing the part of urls, after the last '/' - we cannot commpare full urls, they are different)
        isTopResult = False
        for link in topResults:
            linkID = link.split('/')[-1]
            townUrlID = attractionUrl.split('/')[-1]
            if linkID == townUrlID:
                isTopResult = True
                break

        #print('Top result:', isTopResult)

        #print('------------------------------------------\n')

        # saving to DB
        newAttr = Attraction(name = attractionName[0],
                             link = attractionUrl,
                             address = attractionAddress[0],
                             phone = attractionPhone[0],
                             webpage = attractionWebpage,
                             tags = attractionNavPath,
                             type = attractionType,
                             description = content,
                             picture = attractionPictureMain,
                             regionName = attractionRegion[0],
                             region = regionObject,
                             destination = attractionDestination[0],
                             place = attractionPlace[0],
                             gpsX = gpsX,
                             gpsY = gpsY,
                             topResult = isTopResult
                             )

        newAttr.save()

    except Exception as e:
        print('EXCEPTION: ', str(e))
        attrLog.write("ERROR: " + attractionUrl + ' : ' + str(e) + '\n')

    return



def townGetData(townUrl, n, numLinks):
    global topResults

    # get data from individual town

    try:
        page = requests.get(townUrl)
        tree = html.fromstring(page.content)
        elTree = etree.HTML(page.text)

        # name of the town:
        townName = tree.xpath('// *[ @ id = "tdMainCenter"] / div[3] / div[1] / div[4] / h1/text()')
        if len(townName) == 0:
            townName = ['']

        print(townName[0], '(', n, '/', numLinks, ')')
        #print('link:', townUrl)

        # web page of the town (from the first information centre info)
        townWebPage = tree.xpath('//div[@class="ticItems"]/div[@class="item"]/div[@class="w"]/a/@href')
        if len(townWebPage) == 0:
            townWebPage = ['']
        #print('spletna stran:', townWebPage[0])

        # "mainTownData box with info"
        # population:
        townPop = tree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[@class="mainTownData"]/div[@class="item pop"]/div/text()')
        if len(townPop) == 0:
            townPop = -1
        else:
            townPop = int(townPop[0])
        #print("population:", townPop)

        # altitude:
        townAlt = tree.xpath(
            '//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[@class="mainTownData"]/div[@class="item alt"]/div/text()')
        if len(townAlt) == 0:
            townAlt = ['']
        #print("altitude:", townAlt)

        # position (more than one is possible, gotta join it):
        townPos = tree.xpath(
            '//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[@class="mainTownData"]/div[@class="item pos"]/text()')
        if len(townPos) == 0:
            townPos = ['']
        else:
            townPos = [','.join(townPos)]
        #print("position:", townPos)

        # temperatures (summer avg, winter avg):
        townTemp = tree.xpath(
            '//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[@class="mainTownData"]/div[@class="item tmpr"]//span[@class="N3"]/text()')
        if len(townTemp) == 0:
            townTemp = ['', '']
        #print("summer temp:", townTemp)

        # number of sunny / rainy days per year:
        townSunnyDays = tree.xpath(
            '//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[@class="mainTownData"]/div[@class="item sun"]//span[@class="N3"]/text()')
        if len(townSunnyDays) == 0:
            townSunnyDays = ['-1', '-1']
        #print("number of sunny/rainy days:", townSunnyDays)

        # webpage path to town, we remove the first one as its always "Domov" and save the one before last as it tells as type of town
        townNavPath = tree.xpath('//*[@id="tdMainCenter"]/div[1]//a/text()')
        townType = townNavPath[len(townNavPath)-2]
        townNavPath.pop(0)
        townNavPath = ','.join(townNavPath)
        #print("navigation path:", townNavPath)

        # description:
        townDescription = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]')
        #print("raw:,", etree.tostring(townDescription[0]))

        # we remove unecessary parts (we only need body text)
        childDiv = townDescription[0].find('div')
        #print('Odstranjujem:', etree.tostring(childDiv))
        if childDiv is not None:
            townDescription[0].remove(childDiv)

        # if we try to remove picture link, we also remove text -> NOT OK! TO-DO: http://stackoverflow.com/questions/22967659/removing-an-element-but-not-the-text-after-it
        # childLink = townDescription[0].find('a')
        # print('Removing:', etree.tostring(childLink))
        # townDescription[0].remove(childLink)

        # find all relative links in description and replace them with absolute ones
        townDescriptionFixed = fixLinks(townDescription[0])

        content = etree.tostring(townDescriptionFixed)
        print("description:", content)

        # main picture: (we have to merge it with base url for full picture url)
        townPictureMain = tree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/a/img/@src')
        if len(townPictureMain) > 0 and not 'www' in townPictureMain[0]:
            townPictureMain = baseUrlPictures + townPictureMain[0]
        #print("link to main picture:", townPictureMain)

        # region
        townRegion = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row region"]/a/text()')
        if len(townRegion) < 1:
            townRegion = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row region"]/text()')
            if len(townRegion) == 0:
                townRegion = ['']
        #print("region:", townRegion)

        # destination
        townDestination = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row destination"]/a/text()')
        if len(townDestination) < 1:
            townDestination = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row destination"]/text()')
            if len(townDestination) == 0:
                townDestination = ['']
        #print("destination:", townDestination)

        # place
        townPlace = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row place"]/a/text()')
        if len(townPlace) < 1:
            townPlace = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row place"]/text()')
            if len(townPlace) == 0:
                townPlace = ['']
        #print("place:", townPlace)

        # GPS coordinates
        townGPS = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row gps"]/a/text()')
        if len(townGPS):
            gpsX = float(townGPS[0].replace(',', '.'))
            gpsY = float(townGPS[1].replace(',', '.'))
        else:
            gpsX = -1
            gpsY = -1

        #print("gps [x, y]:", townGPS)

        # getting region from DB for foreign key (TO-DO: optimize this?)
        region = getRegion(townRegion[0])

        # check if it's top result with array we saved in the beginning (by comparing the part of urls, after the last '/' - we cannot commpare full urls, they are different)
        isTopResult = False
        for link in topResults:
            linkID = link.split('/')[-1]
            townUrlID = townUrl.split('/')[-1]
            if linkID == townUrlID:
                isTopResult = True
                break

        #print('Top result:', isTopResult)
        #print('------------------------------------------\n')


        # saving to DB
        newTown = Town(name = townName[0],
                             link = townUrl,
                             webpage = townWebPage[0],
                             population = townPop,
                             altitude = townAlt[0],
                             position = townPos[0],
                             tempSummer = townTemp[0],
                             tempWinter = townTemp[1],
                             sunnyDays = int(townSunnyDays[0]),
                             rainyDays = int(townSunnyDays[0]),
                             tags = townNavPath,
                             type = townType,
                             description = content,
                             picture = townPictureMain,
                             regionName = townRegion[0],
                             region = region,
                             destination = townDestination[0],
                             place = townPlace[0],
                             gpsX = gpsX,
                             gpsY = gpsY,
                             topResult = isTopResult
                             )

        #newTown.save()

    except Exception as e:
        print('EXCEPTION:', str(e))
        townLog.write("ERROR: " + townUrl + ' : ' + str(e) + '\n')

    return



def fixLinks(content):

    # find all links and picture links in description and change them from relative to absolute
    # solution from here: http://stackoverflow.com/questions/26167690/lxml-how-to-change-img-src-to-absolute-link

    for node in content.xpath('//*[@src]'):
        url = node.get('src')
        url = join(url)
        node.set('src', url)

    for node in content.xpath('//*[@href]'):
        href = node.get('href')
        url = join(href)
        node.set('href', url)

    return content



def join(url):

    # join relative URL with base URL

    if url.startswith("/") and not ("://" in url):
        # if it starts with /
        #print('Fixing:', (baseUrl+url))
        return baseUrl + url
    elif not ("://" in url or url.startswith("www")):
        # if it doesn't start with /
        #print('Fixing:', (baseUrlPictures + url))
        return baseUrlPictures + url
    elif url.startswith("www"):
        return 'http://' + url
    else:
        # already absolute
        return url




# starting
prepareLogFiles()
db = connectDB()
db.connect()
#initDB(db)

# start with all regions, then  add towns
selectRegion()
#addTowns()

db.close()


town1 = 'http://www.slovenia.info/si/Mesta-in-kraji-v-Sloveniji/Ljubljana.htm?_ctg_kraji=2609&lng=1'       # CHECK DESCRIPTION!!
#townGetData(town1, 1, 1)
