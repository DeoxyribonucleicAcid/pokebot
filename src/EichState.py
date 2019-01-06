import json
import logging
import os
import urllib.request

import pymongo


#from src.FileAccessor import FileAccessor


def db_setup():
    if os.path.isfile(os.path.dirname(os.path.abspath(__file__))+'/conf.json'):
        with open(os.path.dirname(os.path.abspath(__file__))+'/conf.json') as f:
            config = json.load(f)
    else:
        raise EnvironmentError("Config file not existent or wrong format")
    client = pymongo.MongoClient(config["mongo_db_srv"])
    test = client.test
    db = client["database"]

    player_collection = db["player"]
    #player_collection.insert_one({"_id": 00000000})

    if "database" in client.list_database_names():
        logging.info("The database exists.")
    else:
        raise EnvironmentError('Database does not exist!')
    if "player" in db.list_collection_names():
        logging.info("The collection exists.")
    else:
        raise EnvironmentError('Collection does not exist!')
    return db, player_collection


class EichState:
    DEBUG = False
    token = None
    url = 'https://pokeapi.co/api/v2/'
    names_dict = {}
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent',
                          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.2 Safari/602.3.12')]
    #fileAccessor = FileAccessor()
    db, player_col = db_setup()
