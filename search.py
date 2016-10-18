import os
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from slovenia_info_scra import connectDB, Attraction, Region

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
                    )


# Create index dir if it does not exists.
if not os.path.exists("index"):
    os.mkdir("index")

index = create_in("index", attrSchema)
writer = index.writer()

# fill index from DB
db = connectDB()
db.connect()

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
writer.commit()


# test search
with index.searcher() as searcher:
    query = QueryParser("name", index.schema).parse("bled")
    results = searcher.search(query)
    for result in results:
        print(result)


# TO-DO: add region entries (new index, add to this index?)