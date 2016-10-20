from lxml import html, etree
import requests
import time
import datetime
from peewee import *


# getting data from webpage www.slovenia.info using lxml and Xpath
# using ORM 'peewee': http://docs.peewee-orm.com/en/latest/index.html
# postgreSQL database

baseUrl = "http://www.slovenia.info"
baseUrlPictures = "http://www.slovenia.info/"

# log file
logf = open("errors.log", "w")

# select language: 1 = SLO, 2 = English, 3 = Deutsch, 4 = Italiano, 5 = Français, 6 = Pусский, 7 = Español
lng = 1


def connectDB():
    db = PostgresqlDatabase(
        'slovenia_db',
        user='adminslo',
        password='slo',
        host='localhost',
    )

    return db


class BaseModel(Model):
    class Meta:
        database = connectDB()


class Region(BaseModel):
    name = CharField()
    link = CharField()
    description = TextField()
    picture = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)


class Attraction(BaseModel):
    name = CharField()
    link = CharField()
    address = CharField()
    phone = CharField()
    webpage = CharField()
    tags = CharField()
    type = CharField()
    description = TextField()
    picture = CharField()
    regionName = CharField()
    region = ForeignKeyField(Region, related_name='attractions')
    destination = CharField()
    place = CharField()
    gpsX = DoubleField()
    gpsY = DoubleField()
    timestamp = DateTimeField(default=datetime.datetime.now)



def initDB(db):

    # create tables
    db.create_tables([Region, Attraction])

    return



def getRegion(name):

    # find Region by name in db

    try:
        region = Region.get(Region.name == name)
        print('Getting region', region.name)
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



def selectRegion():

    # Gorenjska, Goriška, Obalno - kraška, Osrednjeslovenska, Podravska, Notranjsko - kraška, Jugovzhodna Slovenija, Koroška, Savinjska, Pomurska, Spodnjeposavska, Zasavska
    # without lng param in url, we add it later

    regions = [
        'http://www.slovenia.info/si/Regije/Gorenjska.htm?_ctg_regije=10&lng=',
        'http://www.slovenia.info/si/Regije/Gori%C5%A1ka-Smaragdna-pot.htm?_ctg_regije=9&lng=',
        'http://www.slovenia.info/si/Regije/Obalno-kra%C5%A1ka.htm?_ctg_regije=17&lng=',
        'http://www.slovenia.info/si/Regije/Osrednjeslovenska.htm?_ctg_regije=11&lng=',
        'http://www.slovenia.info/si/Regije/Podravska.htm?_ctg_regije=15&lng=',
        'http://www.slovenia.info/si/Regije/Notranjsko-kra%C5%A1ka.htm?_ctg_regije=134&lng=',
        'http://www.slovenia.info/si/Regije/Jugovzhodna-Slovenija.htm?_ctg_regije=13&lng=',
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
        description = etree.tostring(description[0])
        #print('data:', description)

        # picture link
        pictureLink = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/a/img/@src')
        if len(pictureLink) > 0:
            pictureLink = baseUrlPictures + pictureLink[0]
        #print('link to picture:', pictureLink)

        # attractions link
        attrLinks = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[1]/div[4]/a[4]/@href')
        if len(attrLinks) > 0:
            attrLinks = baseUrl + attrLinks[0]
        #print('attractions:', attrLinks)
        #print('----------------------------------------\n')

        #saving to db
        newRegion = Region(name = name[0], link = regionUrl, description = description, picture = pictureLink)
        newRegion.save()

        # let's get attractions from attraction link
        regionGetAttractions(attrLinks, newRegion)

    except Exception as e:
        logf.write("Failed to get data from region " + regionUrl + ' : ' + str(e) + '\n')

    print('FINISHED WITH REGION', name, '\n---------------------------------------------\n')

    return



def regionGetAttractions(regionUrl, regionObject):

    # get attraction links from [ Home -> Regions -> Some region -> Attractions ] page

    page = requests.get(regionUrl)
    tree = html.fromstring(page.content)
    linksAttractions = tree.xpath('//*[@id="tdMainCenter"]//p/a[2]/@href')
    #print('links:', linksAttractions)
    #print('number of links:', len(linksAttractions))

    # finds those div-s that are named "resultsBox..", they contain links of attractions (sorted by type: churches, lakes, rivers,..)
    regexpNS = "http://exslt.org/regular-expressions"
    attrGroups = tree.xpath('//*[@id="tdMainCenter"]//div[re:test(@id, "^resultsBox")]', namespaces={'re': regexpNS})
    #print('num of groups:', len(attrGroups))

    # we pass on whole tree element so we can extract links (root is div named resultsBox; it contains all links of attractions)
    n = 1
    for node in attrGroups:
        #print(n, ":", node.tag, node.attrib['id'])
        attrLinksList = attractionGroup(node)
        print('Starting with group', n, '- number of attractions:', len(attrLinksList))
        regionAllLinks(attrLinksList, regionObject)
        print('Finished with group', n, '\n------------------------\n')
        n += 1

    return



def attractionGroup(group):

    # get all attraction links for specific group (lakes, rivers,...)

    # first we get all the attraction links from page one (default)
    attrLinksList = []

    # we only need the second link, first one is location of attraction (a[2])
    for link in group.iterfind('div[@class="box2"]/p/a[2]'):
        attrLinksList.append(link.attrib['href'])
        #print('adding link:', link.attrib['href'])

    #print("Number of links in group:", len(attrLinksList))

    # we need selected div's ID because once we load a new link (page two, for example), we have to know which group are we looking at (all the links from other groups are still visible, just collapsed)
    groupId = group.attrib['id']

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
    searchStr = '//*[@id="tdMainCenter"]/div[@id="' + id + '"]//p/a[2]/@href'

    linksPageAttractions = tree.xpath(searchStr)
    #print('new links:', linksPageAttractions)
    #print('number of new links:', len(linksPageAttractions))

    return linksPageAttractions



def regionAllLinks(links, regionObject):

    # now we have links of all the attractions of specific region, lets go through them and get data out

    n = 1
    for link in links:
        fullLink = baseUrl + link
        time.sleep(.300)
        attractionGetData(fullLink, regionObject, n, len(links))
        n += 1

    return



def attractionGetData(attractionUrl, regionObject, n, numLinks):

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
        content = etree.tostring(attractionDescription[0])
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
                             gpsY = gpsY
                             )

        newAttr.save()

    except Exception as e:
        logf.write("Failed to get data from link " + attractionUrl + ' : ' + str(e) + '\n')

    return




# starting
#db = connectDB()
#db.connect()
#initDB(db)

# start with all regions
#selectRegion()

#db.close()

