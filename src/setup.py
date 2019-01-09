import argparse
import json
import logging
import os
import setproctitle

import pymongo

from src.EichState import EichState

logger = logging.getLogger(__name__)


def prepare_environment():
    setproctitle.setproctitle("ProfessorEich")
    parser = argparse.ArgumentParser(description='Basic pokemon bot.')
    parser.set_defaults(which='no_arguments')
    parser.add_argument('-d', '--debug', action='store_true', required=False, help='Debug mode')

    if os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + '/conf.json'):
        with open(os.path.dirname(os.path.abspath(__file__)) + '/conf.json') as f:
            config = json.load(f)
    else:
        raise EnvironmentError("Config file not existent or wrong format")
    args = parser.parse_args()
    if not args.debug:
        EichState.DEBUG = False
        EichState.token = config['token']
    else:
        EichState.DEBUG = True
        EichState.token = config['test_token']

    if os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + '/name_dict.json'):
        with open(os.path.dirname(os.path.abspath(__file__)) + '/name_dict.json') as f:
            EichState.names_dict = json.load(f)
    else:
        raise EnvironmentError("Names file not existent or wrong format")

    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/res/tmp'
    if not os.path.exists(directory):
        os.makedirs(directory)

    db_setup()

    # logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG,
    #                     handlers=[logging.FileHandler('.log', 'w', 'utf-8')])


def db_setup():
    if os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + '/conf.json'):
        with open(os.path.dirname(os.path.abspath(__file__)) + '/conf.json') as f:
            config = json.load(f)
    else:
        raise EnvironmentError("Config file not existent or wrong format")
    client = pymongo.MongoClient(config["mongo_db_srv"])
    test = client.test

    if EichState.DEBUG:
        if "database_debug" in client.list_database_names():
            logging.info("The database exists.")
        else:
            raise EnvironmentError('Debug database does not exist!')

        db = client["database_debug"]
    else:
        if "database" in client.list_database_names():
            logging.info("The database exists.")
        else:
            raise EnvironmentError('Database does not exist!')

        db = client["database"]

    if "player" in db.list_collection_names():
        logging.info("The collection exists.")
    else:
        raise EnvironmentError('Collection does not exist!')

    player_collection = db["player"]
    EichState.db = db
    EichState.player_col = player_collection
