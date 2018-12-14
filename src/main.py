from telegram.ext import Updater, CommandHandler
import logging
import urllib.request
import json
import os.path



if os.path.isfile('./conf.json'):
    with open('conf.json') as f:
        config = json.load(f)
else:
    raise EnvironmentError("Config file not existent or wrong format")

updater = Updater(token=config["token"])
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater.start_polling()
j = updater.job_queue