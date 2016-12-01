import requests
import urllib


baseAPIUrl = 'http://127.0.0.1:5000/'


def testItem(type, id):

    fullUrl = baseAPIUrl + 'item/' + type + '/' + str(id)
    response = requests.get(fullUrl)
    print(response.json())
    return



def testQuery(query):

    query = urllib.parse.quote(query)
    fullUrl = baseAPIUrl + 'query/' + query
    response = requests.get(fullUrl)
    print(response.json())
    return



# example JSON files
testItem('attraction', 300)
testQuery('seznam gradov na primorskem')
#testQuery('ljubljanski grad')


testItemResult = {
    "description": "<div class=\"wpContent\">&#13;\n<a href=\"http://www.slovenia.info/pictures/TB_region/1/2010/046_orig_270469.jpg\" target=\"_winFancyBox\" class=\"imgLightBox\"><img class=\"imgMainItemIMG\" src=\"http://www.slovenia.info/pictures/TB_region/1/2010/046_orig_270469_sml.jpg\" align=\"right\" title=\"Gori&#353;ka - Smaragdna pot\"/></a>Lepote Gori&#353;ke regije obsegajo vse od slikovitih alpskih vrhov in dolin, vklju&#269;enih v <strong><a href=\"http://www.slovenia.info/si/Triglavski-narodni-park.htm?triglavski_narodni_park=0&amp;lng=1\" target=\"_self\">Triglavski narodni park</a></strong>, o&#269;arljivih vinorodnih obmo&#269;ij <strong><a href=\"http://www.slovenia.info/si/-ctg-kraji/Gori&#353;ka-Brda.htm?_ctg_kraji=5629&amp;lng=1\" target=\"_self\">Gori&#353;kih Brd</a></strong> in <strong><a href=\"http://www.slovenia.info/si/-ctg-kraji/Vipava,-Vipavska-dolina.htm?_ctg_kraji=3144&amp;lng=1\" target=\"_self\">Vipavske doline</a></strong> do hribovij v okolici Cerknega in Idrije. Med najbolj prepoznavnimi znamenitostmi obmo&#269;ja je smaragdna reka <strong><a href=\"http://www.slovenia.info/si/reka-potok/Reka-So&#269;a.htm?reka_potok=12278&amp;lng=1\" target=\"_self\">So&#269;a</a></strong>.<br/><br/>Na zgornjem delu doline je slikovita <strong><a href=\"http://www.slovenia.info/?_ctg_kraji=2777\">Trenta</a></strong> z informacijsko pisarno Triglavskega narodnega parka, z muzejem in z najpomembnej&#353;im slovenskim alpskim botani&#269;nim vrtom Julijana. Kraji ob smaragdni reki privla&#269;ijo tako iskalce miru kot izzivalce adrenalina. Tu so na voljo &#353;tevilni <strong><a href=\"http://www.slovenia.info/?aktivne_pocitnice=0&amp;srch=1&amp;srchtype=spc&amp;wp_id=_wp_100_0_56_1_0_14&amp;searchKrajName_wp_100_0_56_1_0_14=&amp;searchStr_wp_100_0_56_1_0_14=&amp;searchCategoryId_wp_100_0_56_1_0_14=151\">vodni &#353;porti</a> </strong>&#8211; od kajaka&#353;tva in kanujinga do raftanja in soteskanja. Dolino je mogo&#269;e do&#382;iveti tudi z jadralnim padalom, zmajem ali gorskim kolesom. Iz doline, ki ima najve&#269; preno&#269;i&#353;&#269; in gosti&#353;&#269; v <a href=\"http://www.slovenia.info/?_ctg_kraji=2757&amp;lng=1\"><strong>Bovcu</strong></a>, <a href=\"http://www.slovenia.info/?_ctg_kraji=2857\"><strong>Kobaridu</strong></a> in <strong><a href=\"http://www.slovenia.info/?_ctg_kraji=2705\">Tolminu</a></strong>, je dostopno najvi&#353;je visokogorsko <a href=\"http://www.slovenia.info/si/smucanje/Smu&#269;i&#353;&#269;e-Kanin-Canin-(Sella-Nevea).htm?smucanje=335&amp;lng=1\" target=\"_self\"><strong>slovensko smu&#269;i&#353;&#269;e Kanin</strong></a>. <br/><br/>Poso&#269;je, ki na vsakem koraku razkriva izjemne naravne posebnosti, hrani tudi pretresljive spomine na najhuj&#353;e bitke prve svetovne vojne. Najpomembnej&#353;e ostaline in spominska obele&#382;ja so&#353;ke fronte so povezane v <strong><a href=\"http://www.slovenia.info/si/pot-dediscine/Pot-miru.htm?pot_dediscine=4761&amp;lng=1\" target=\"_self\">Pot miru</a></strong>. Predstavljene pa so tudi v ve&#269;krat nagrajenem <strong><a href=\"http://www.slovenia.info/?kul_zgod_znamenitosti=1961\">Kobari&#353;kem muzeju</a></strong>. &#352;e nekoliko ju&#382;neje ob reki So&#269;i le&#382;ita <strong>Tolmin</strong> in <strong><a href=\"http://www.slovenia.info/si/-ctg-kraji/Most-na-So&#269;i.htm?_ctg_kraji=2697&amp;lng=1\" target=\"_self\">Most na So&#269;i</a></strong>. V tem kraju so arheologi odkrili grobove iz &#382;elezne dobe, zaradi &#269;esar sodi med pomembnej&#353;a prazgodovinska najdi&#353;&#269;a v Evropi.<br/><br/>Ob reki Idrijci vodijo poti proti <strong><a href=\"http://www.slovenia.info/si/-ctg-kraji/Cerkno.htm?_ctg_kraji=2923&amp;lng=1\" target=\"_self\">Cerknem</a></strong> in <strong><a href=\"http://www.slovenia.info/si/-ctg-kraji/Idrija.htm?_ctg_kraji=2569&amp;lng=1\" target=\"_self\">Idriji</a></strong>. V bli&#382;ini Cerknega je lepo urejeno smu&#269;arsko sredi&#353;&#269;e in nedavno vnovi&#269; odprta prenovljena partizanska <strong><a href=\"http://www.slovenia.info/si/kul-zgod-znamenitosti/Dolenji-Novaki,-Bolni&#353;nica-Franja.htm?kul_zgod_znamenitosti=6684&amp;lng=1\" target=\"_self\">bolni&#353;nica Franja</a></strong>, muzej na prostem v skriti in te&#382;ko dostopni re&#269;ni soteski.&#160;<br/><br/>V Idriji je doma slovita &#269;ipkarska tradicija, sem vabita na oglede nekdaj svetovno pomemben <strong><a href=\"http://www.slovenia.info/si/muzej/Antonijev-rov-Rudnik-&#382;ivega-srebra.htm?muzej=4210&amp;lng=1\" target=\"_self\">rudnik &#382;ivega srebra</a></strong> ter <strong><a href=\"http://www.slovenia.info/si/kul-zgod-znamenitosti/Grad-Gewerkenegg.htm?kul_zgod_znamenitosti=6250&amp;lng=1\" target=\"_self\">grad Gewerkenegg</a></strong> z muzejskimi zbirkami .<br/><br/>Eno izmed slovenskih vinorodnih obmo&#269;ij, kjer pridelujejo najbolj okusna in kakovostna vina so slikovita <strong>Gori&#353;ka Brda</strong> severno od <strong><a href=\"http://www.slovenia.info/si/-ctg-kraji/Nova-Gorica.htm?_ctg_kraji=2898&amp;lng=1\" target=\"_self\">Nove Gorice</a></strong>. Med zanimivej&#353;imi kraji je tudi <strong>Kanal</strong>, kjer vsako leto uprizarjajo skoke v So&#269;o s kamnitega mostu. <br/><br/>Novo Gorico obkro&#382;ajo &#353;e &#353;tevilne druge znamenitosti (<strong><a href=\"http://www.slovenia.info/si/cerkev/Samostan-Kostanjevica.htm?cerkev=3843&amp;lng=1\" target=\"_self\">Samostan Kostanjevica</a></strong>, <strong><a href=\"http://www.slovenia.info/si/cerkev/Sveta-Gora.htm?cerkev=3815&amp;lng=1\" target=\"_self\">Sveta Gora</a></strong>, <strong><a href=\"http://www.slovenia.info/si/grad/Grad-Kromberk.htm?grad=5177&amp;lng=1\" target=\"_self\">Grad Kromberk</a></strong>, <a href=\"http://www.slovenia.info/si/arhitekturne-znamenitosti/Solkan,-Solkanski-most.htm?arhitekturne_znamenitosti=3809&amp;lng=1\" target=\"_self\"><strong>Solkanski</strong> <strong>most</strong></a>). Mesto obdaja <strong><a href=\"http://www.slovenia.info/si/naravne-znamenitosti-jame/Trnovska-in-Banj&#353;ka-planota.htm?naravne_znamenitosti_jame=11520&amp;lng=1\" target=\"_self\">Trnovska in Banj&#353;ka planota</a></strong>, &#269;udovit svet s popolnoma druga&#269;nim podnebjem, poln ljudskega izro&#269;ila in naravnih znamenitosti. Proti vzhodu se razliva vinorodna in zelena <strong>Vipavska dolina</strong>, nad katero krila razpenjajo jadralci in <strong><a href=\"http://www.slovenia.info/si/drugi-sporti/Tandemski-polet-z-Lijaka.htm?drugi_sporti=4439&amp;lng=1\" target=\"_self\">padalci</a></strong> z vsega sveta. Najpomembnej&#353;i mesti v Vipavski dolini sta <strong><a href=\"http://www.slovenia.info/si/-ctg-kraji/Ajdov&#353;&#269;ina-v-Vipavski-dolini.htm?_ctg_kraji=3079&amp;lng=1\" target=\"_self\">Ajdov&#353;&#269;ina</a></strong> in <strong>Vipava</strong>. Na gri&#269;u v bli&#382;ini Vipave je vreden ogleda dvorec <strong>Zemono</strong>.<br/>&#160;<br/>V vseh teh prijaznih krajih je doma odli&#269;no vino, avtohtone sorte, ki se odli&#269;no prilegajo k okusnim vipavskim jedem. Do&#382;ivite jih lahko v gostoljubnih <strong>kleteh</strong>, na <strong>osmicah</strong>, v <strong>turisti&#269;nih kmetijah</strong> in tudi na etnolo&#353;ko obarvanih <strong>prireditvah</strong>. <br/><br/><div style=\"text-align: center\"><object type=\"application/x-shockwave-flash\" width=\"710\" height=\"500\" data=\"http://www.vimeo.com/moogaloop.swf?clip_id=51277144&amp;server=www.vimeo.com&amp;fullscreen=1\"><param name=\"quality\" value=\"best\"/><param name=\"scale\" value=\"showAll\"/><param name=\"allowfullscreen\" value=\"true\"/><param name=\"wmode\" value=\"transparent\"/><param name=\"movie\" value=\"http://www.vimeo.com/moogaloop.swf?clip_id=51277144&amp;server=www.vimeo.com&amp;fullscreen=1\"/></object></div><br/><br/>&#160;<br/></div>&#13;\n",
    "id": 2,
    "link": "http://www.slovenia.info/si/Regije/Gori%C5%A1ka-Smaragdna-pot.htm?_ctg_regije=9&lng=1",
    "name": "Goriška - Smaragdna pot",
    "picture": "http://www.slovenia.info/http://www.slovenia.info/pictures/TB_region/1/2010/046_orig_270469_sml.jpg",
    "timestamp": "2016-11-03 13:28:02.483815"
}


testQueryResult = {
        "0": {
            "destination": "",
            "id": "2234",
            "link": "http://www.slovenia.info/si/arhitekturne-znamenitosti/Tivolski-grad-.htm?arhitekturne_znamenitosti=869&lng=1",
            "name": "Tivolski grad",
            "place": "Ljubljana",
            "regionName": "Osrednjeslovenska",
            "score": 9.563960670702476,
            "type": "Gradovi po Sloveniji",
            "typeID": "attraction"
        },
        "1": {
            "destination": "",
            "id": "2287",
            "link": "http://www.slovenia.info/si/grad/Tivolski-grad-.htm?grad=869&lng=1",
            "name": "Tivolski grad",
            "place": "Ljubljana",
            "regionName": "Osrednjeslovenska",
            "score": 9.563960670702476,
            "type": "Gradovi po Sloveniji",
            "typeID": "attraction"
        },
        "2": {
            "destination": "",
            "id": "2286",
            "link": "http://www.slovenia.info/si/grad/Grad-Fužine-.htm?grad=16495&lng=1",
            "name": "Grad Fužine",
            "place": "Ljubljana",
            "regionName": "Osrednjeslovenska",
            "score": 9.503275499109423,
            "type": "Gradovi po Sloveniji",
            "typeID": "attraction"
        },
        "3": {
            "destination": "",
            "id": "2282",
            "link": "http://www.slovenia.info/si/grad/Ljubljanski-grad-.htm?grad=865&lng=1",
            "name": "Ljubljanski grad",
            "place": "Ljubljana",
            "regionName": "Osrednjeslovenska",
            "score": 5.4778930649391855,
            "type": "Vredno ogleda!",
            "typeID": "attraction"
        }
    }
