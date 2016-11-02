from peewee import *
import datetime



def connectDB():
    db = PostgresqlDatabase(
        'slovenia_db',
        user='adminslo',
        password='slo',
        host='localhost',
    )

    return db


def initDB(db):

    # create tables
    db.create_tables([Region, Attraction, Town])

    return


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
    topResult = BooleanField()
    timestamp = DateTimeField(default=datetime.datetime.now)


class Town(BaseModel):
    name = CharField()
    link = CharField()
    webpage = CharField()
    population = IntegerField()
    altitude = CharField()
    position = CharField()
    tempSummer = CharField()
    tempWinter = CharField()
    sunnyDays = IntegerField()
    rainyDays = IntegerField()
    tags = CharField()
    type = CharField()
    description = TextField()
    picture = CharField()
    regionName = CharField()
    region = ForeignKeyField(Region, related_name='towns')
    destination = CharField()
    place = CharField()
    gpsX = DoubleField()
    gpsY = DoubleField()
    topResult = BooleanField()
    timestamp = DateTimeField(default=datetime.datetime.now)