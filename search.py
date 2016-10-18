from whoosh.fields import *

# schema for attribute entries
attrSchema = Schema(id=ID,
                    name=TEXT(stored=True),
                    link=ID(stored=True),
                    address=TEXT,
                    phone=KEYWORD(commas=True),
                    webpage=ID,
                    tags=KEYWORD(commas=True),
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



