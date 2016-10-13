from lxml import html, etree
import requests
import time
import datetime
from peewee import *

# getting data from webpage www.slovenia.info using lxml and Xpath

baseUrl = "http://www.slovenia.info"
baseUrlPictures = "http://www.slovenia.info/"



def selectRegion():

    # Gorenjska, Goriška, Obalno - kraška, Osrednjeslovenska, Podravska, Notranjsko - kraška, Jugovzhodna Slovenija, Koroška, Savinjska, Pomurska, Spodnjeposavska, Zasavska

    regions = [
        'http://www.slovenia.info/si/Regije/Gorenjska.htm?_ctg_regije=10&lng=1',
        'http://www.slovenia.info/si/Regije/Gori%C5%A1ka-Smaragdna-pot.htm?_ctg_regije=9&lng=1',
        'http://www.slovenia.info/si/Regije/Obalno-kra%C5%A1ka.htm?_ctg_regije=17&lng=1',
        'http://www.slovenia.info/si/Regije/Osrednjeslovenska.htm?_ctg_regije=11&lng=1',
        'http://www.slovenia.info/si/Regije/Podravska.htm?_ctg_regije=15&lng=1',
        'http://www.slovenia.info/si/Regije/Notranjsko-kra%C5%A1ka.htm?_ctg_regije=134&lng=1',
        'http://www.slovenia.info/si/Regije/Jugovzhodna-Slovenija.htm?_ctg_regije=13&lng=1',
        'http://www.slovenia.info/si/Regije/Koro%C5%A1ka.htm?_ctg_regije=121&lng=1',
        'http://www.slovenia.info/si/Regije/Savinjska.htm?_ctg_regije=14&lng=1',
        'http://www.slovenia.info/si/Regije/Pomurska.htm?_ctg_regije=16&lng=1',
        'http://www.slovenia.info/si/Regije/Spodnjeposavska.htm?_ctg_regije=133&lng=1',
        'http://www.slovenia.info/si/Regije/Zasavska.htm?_ctg_regije=12&lng=1'
    ]

    for region in regions:
        # wait 0.3 sec
        time.sleep(.300)
        regionGetData(region)

    return



def regionGetAttractions(regionUrl):

    # get attraction links from [ Home -> Regions -> Attractions ] page

    page = requests.get(regionUrl)
    tree = html.fromstring(page.content)
    linksAttractions = tree.xpath('//*[@id="tdMainCenter"]//p/a[2]/@href')
    print('links:', linksAttractions)
    print('number of links:', len(linksAttractions))

    # finds those div-s that are named "resultsBox..", they contain links of attractions (sorted by type: churches, lakes, rivers,..)
    regexpNS = "http://exslt.org/regular-expressions"
    attrGroups = tree.xpath('//*[@id="tdMainCenter"]//div[re:test(@id, "^resultsBox")]', namespaces={'re': regexpNS})
    print('num of groups:', len(attrGroups))

    # we pass on whole tree element so we can extract links (root is div named resultsBox; it contains all links of attractions)
    n = 1
    for node in attrGroups:
        print(n, ":", node.tag, node.attrib['id'])
        attrLinksList = attractionGroup(node)
        n += 1

        regionAllLinks(attrLinksList)

    return



def attractionGroup(group):

    # get all attraction links for specific group (lakes, rivers,...)

    # first we get all the attraction links from page one (default)
    attrLinksList = []

    # we only need the second link, first one is location of attraction (a[2])
    for link in group.iterfind('div[@class="box2"]/p/a[2]'):
        attrLinksList.append(link.attrib['href'])
        #print('adding link:', link.attrib['href'])

    print("Number of links in group:", len(attrLinksList))

    # we need selected div ID because once we load a new link (page two, for example), we have to know which group are we looking at (all the links from other groups are still visible)
    groupId = group.attrib['id']

    # we look for the links of pages (if there are more than 50 attractions in a group, they are paginated)
    # we don't need to 'click' on the first link (we already have those attractions, they are shown by default)
    count = 0
    for pageLinks in group.iterfind('div[@class="subbox"]/div[@class="paging"]/div[@class="links"]/a'):
        print("Page link found:", pageLinks.tag, pageLinks.attrib['href'])

        if count != 0:
            # wait 0.3 sec
            time.sleep(.300)

            # adding links from page 2, 3, ..
            attractionsPage = attrGroupSubPage(pageLinks.attrib['href'], groupId)
            attrLinksList.extend(attractionsPage)
            print('new number of links:', len(attrLinksList))

        count += 1

    return attrLinksList



def attrGroupSubPage(link, id):

    # find the correct div based on given id, extract links and return them

    fullLink = baseUrl + link
    print("going to page:", fullLink)

    page = requests.get(fullLink)
    tree = html.fromstring(page.content)

    # search string
    searchStr = '//*[@id="tdMainCenter"]/div[@id="' + id + '"]//p/a[2]/@href'

    linksPageAttractions = tree.xpath(searchStr)
    print('new links:', linksPageAttractions)
    print('number of new links:', len(linksPageAttractions))

    return linksPageAttractions



def regionAllLinks(links):

    # lets get data from attraction links!

    for link in links:
        fullLink = baseUrl + link
        time.sleep(.300)
        attractionGetData(fullLink)

    return


def regionGetData(regionUrl):

    # get data from individual region using XPath
    print('link:', regionUrl)

    page = requests.get(regionUrl)
    elTree = etree.HTML(page.text)

    # description
    description = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]')
    print('data:', etree.tostring(description[0]))

    # picture link
    pictureLink = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/a/img/@src')
    if len(pictureLink) > 0:
        pictureLink = baseUrlPictures + pictureLink[0]
    print('link to picture:', pictureLink)

    # attractions link
    attrLinks = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[1]/div[4]/a[4]/@href')
    if len(attrLinks) > 0:
        attrLinks = baseUrl + attrLinks[0]
    print('attractions:', attrLinks)
    print('----------------------------------------\n')

    # lets get attraction links
    #regionGetAttractions(attrLinks)

    return



def attractionGetData(attractionUrl):

    # get data from individual attraction using XPath
    print('link:', attractionUrl)

    page = requests.get(attractionUrl)
    tree = html.fromstring(page.content)
    elTree = etree.HTML(page.text)


    # name of the attraction:
    attractionName = tree.xpath('// *[ @ id = "tdMainCenter"] / div[3] / div[1] / div[4] / h1/text()')
    print("name:", attractionName)

    # address:
    attractionAddress = tree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[1]/div[1]/div[@class="prop propLocation"]/div[2]/text()')
    print("address:", attractionAddress)

    # phone:
    attractionPhone = tree.xpath(
        '//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[1]/div[1]/div[@class="prop propPhone"]/div[2]/text()')
    print("phone:", attractionPhone)

    # email:
    #attractionEmail = tree.xpath(
    #    '//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[1]/div[1]/div[@class="prop propEmail"]/div[2]/text()')
    #print("email:", attractionEmail)

    # email does not work, problem with js (link is not visible to lxml?)
    attractionEmail = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]')
    if len(attractionEmail) > 0:
        print("email:", etree.tostring(attractionEmail[0]))

    # webpage:
    attractionWebpage = tree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/div[1]/div[1]/div[1]/div[@class="prop propRow propWWW"]/a/text()')

    # in case link is split, we have to merge it
    attractionWebpage = ''.join(attractionWebpage)
    print("webpage:", attractionWebpage)

    # webpage path to attraction:
    attractionNavPath = tree.xpath('//*[@id="tdMainCenter"]/div[1]//a/text()')
    print("navigation path:", attractionNavPath)

    # description:
    attractionDescription = elTree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]')
    #print("raw:,", etree.tostring(attractionDescription[0]))

    # we remove unecessary parts (we only need text)
    childDiv = attractionDescription[0].find('div')
    #print('Odstranjujem:', etree.tostring(childDiv))
    if childDiv is not None:
        attractionDescription[0].remove(childDiv)

    # if we try to remove picture link, we also remove text -> NOT OK! TO-DO: http://stackoverflow.com/questions/22967659/removing-an-element-but-not-the-text-after-it
    # childLink = attractionDescription[0].find('a')
    # print('Odstranjujem:', etree.tostring(childLink))
    # attractionDescription[0].remove(childLink)
    content = etree.tostring(attractionDescription[0])
    print("description:", content)

    # main picture: (we have to concatenate it with base url for full picture url)
    attractionPictureMain = tree.xpath('//*[@id="tdMainCenter"]/div[3]/div[2]/div[1]/a/img/@src')
    if len(attractionPictureMain) > 0:
        attractionPictureMain = baseUrlPictures + attractionPictureMain[0]
    print("link to main picture:", attractionPictureMain)

    # region    //TO-DO: save link!
    attractionRegion = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row region"]/a/text()')
    if len(attractionRegion) < 1:
        attractionRegion = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row region"]/text()')
    print("region:", attractionRegion)

    # destination    //TO-DO: save link!
    attractionDestination = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row destination"]/a/text()')
    if len(attractionDestination) < 1:
        attractionDestination = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row destination"]/text()')
    print("destination:", attractionDestination)

    # place    //TO-DO: save link! (.../a/@href)
    attractionPlace = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row place"]/a/text()')
    if len(attractionPlace) < 1:
        attractionPlace = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row place"]/text()')
    print("place:", attractionPlace)

    # GPS coordinates
    attractionGPS = tree.xpath('//*[@id="wpMapSmall"]/div[2]/div[@class="row gps"]/a/text()')
    print("gps [x, y]:", attractionGPS)

    print('------------------------------------------')
    print('\n')


    # TO-DO: save all this somehow, somewhere

    return




def initDB():

    db = SqliteDatabase('slovenia.db', user = 'admin', passwd = 'sudosudo1')

    class BaseModel(Model):
        class Meta:
            database = db

    class Region(BaseModel):
        name = CharField()
        link = CharField()
        description = CharField()
        picture = CharField()
        timestamp = DateTimeField(default=datetime.datetime.now)



    return




















#just for testing purposes
attraction1 = "http://www.slovenia.info/si/naravne-znamenitosti-jame/Vintgar-Gorge-.htm?naravne_znamenitosti_jame=110&lng=1&redirected=1"
attraction2 = "http://www.slovenia.info/en/naravne-znamenitosti-jame/Lake-Bohinj-.htm?naravne_znamenitosti_jame=1746&lng=1"
attraction3 = "http://www.slovenia.info/si/arhitekturne-znamenitosti/Hi%C5%A1a-Percauz-.htm?arhitekturne_znamenitosti=705&lng=1"
attraction4 = "http://www.slovenia.info/si/kul-zgod-znamenitosti/Napoleonov-drevored-lip-.htm?kul_zgod_znamenitosti=11879&lng=1"
attraction5 = "http://www.slovenia.info/si/ponudniki-podezelje/Olive-in-olj%C4%8Dno-olje-na-Kmetiji-Bojanc-.htm?ponudniki_podezelje=438&lng=1"
attraction6 = "http://www.slovenia.info/si/excursion-farm/Turisti%C4%8Dna-kmetija-Pri-Rjav%C4%8Devih-.htm?excursion_farm=739&lng=1"
attraction7 = "http://www.slovenia.info/si/naravne-znamenitosti-jame/Izvir-kisle-vode-na-Jezerskem-.htm?naravne_znamenitosti_jame=169&lng=1"
attraction8 = 'http://www.slovenia.info/si/Biseri-narave/Bohinjsko-jezero-.htm?naravne_znamenitosti_jame=1745&lng=1'
#attractionGetData(attraction7)
#attractionGetData(attraction1)
#attractionGetData(attraction8)

region1 = "http://www.slovenia.info/si/Regije/Atrakcije-/search-predefined.htm?_ctg_regije=13&srch=1&srchtype=predef&searchmode=20&localmode=region&lng=1"
region2 = "http://www.slovenia.info/si/Regije/Atrakcije-/search-predefined.htm?_ctg_regije=10&srch=1&srchtype=predef&searchmode=20&localmode=region&lng=1"
#regionGetAttractions(region2)

#regionGetData('http://www.slovenia.info/si/Regije/Gorenjska.htm?_ctg_regije=10&lng=1')

selectRegion()