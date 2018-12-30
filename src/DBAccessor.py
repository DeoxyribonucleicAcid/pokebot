import json
import os

import pymongo

if os.path.isfile('./conf.json'):
    with open('conf.json') as f:
        config = json.load(f)
else:
    raise EnvironmentError("Config file not existent or wrong format")
client = pymongo.MongoClient(config["MongoDB_SRV"])
db = client.test
print(db)
