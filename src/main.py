import random
from pprint import pprint

from telegram import ChatAction, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import urllib2
import json
import os.path
from functools import wraps

url = 'https://pokeapi.co/api/v2/'

# response = urllib.urlopen(url)
# print(response.read())

opener = urllib2.build_opener()
opener.addheaders = [('User-Agent',
                      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.2 Safari/602.3.12')]


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(*args, **kwargs):
        bot, update = args
        bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(bot, update, **kwargs)

    return command_func


def getPokeInfo(pokemon):
    pokeurl = url + 'pokemon/' + pokemon + '/'
    try:
        poke_response = opener.open(pokeurl)
    except urllib2.HTTPError as e:
        logging.error('Pokemon not found: ' + '\n' + pokeurl)
        raise e

    poke_json = json.load(poke_response)
    sprites = {k: v for k, v in poke_json[u'sprites'].items() if v != None}
    type_urls = []
    for type in poke_json[u'types']: type_urls.append(type[u'type'][u'url'])
    double_damage_types = []
    types = []
    for type in type_urls:
        try:
            type_json = json.load(opener.open(type))
            types.append(type_json[u'name'])
            damage_relations = type_json[u'damage_relations'][u'double_damage_from']
            for dd_type in damage_relations:
                double_damage_types.append(dd_type[u'name'])
        except urllib2.HTTPError as e:
            logging.error('Type not found: ' + '\n' + type)
            raise e

    sprite = sprites[random.choice(sprites.keys())]
    dd_types_str = ', '.join(map(str, list(set(double_damage_types))))
    types_str = ', '.join(map(str, types))
    name_str = str(poke_json[u'name'])
    id_str = str(poke_json[u'id'])

    pprint(sprite)
    pprint(name_str)
    pprint(id_str)
    pprint(types_str)
    pprint(dd_types_str)

    text = name_str + ' #' + id_str + '\n' + types_str + '\nAttack with:\n' + dd_types_str + '\n'

    return text, sprite


@send_typing_action
def info(bot, update):
    pokemon = update.message.text.lower()
    if pokemon in names_dict["pokenames"].keys():
        pokemon = names_dict["pokenames"][pokemon]
    pokemon = pokemon.lower()
    try:
        text, sprite = getPokeInfo(pokemon)
        bot.send_photo(chat_id=update.message.chat_id, photo=sprite, caption=text, parse_mode=ParseMode.MARKDOWN)
    except urllib2.HTTPError:
        bot.send_message(chat_id=update.message.chat_id, text=':( i didn\'t catch that')


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text='/start zeigt diese Liste\n'
                          '/join setzt dich auf die Update-Liste\n'
                          '/leave nimmt dich von der Update-Liste\n'
                          '/status gibt den aktuellen Status')
    print(chats)


if os.path.isfile('./conf.json'):
    with open('conf.json') as f:
        config = json.load(f)
else:
    raise EnvironmentError("Config file not existent or wrong format")

if os.path.isfile('./name_dict.json'):
    with open('name_dict.json') as f:
        names_dict = json.load(f)
else:
    raise EnvironmentError("Names file not existent or wrong format")

if os.path.isfile('./chats.json'):
    print('chats.json existing')
    with open("chats.json", "r") as jsonFile:
        data = json.load(jsonFile)
        chats = data["chats"]
else:
    data = {}
    data["chats"] = {}
    chats = {}
    # debug
    # chats[252269446] = True
    data["chats"] = chats
    print('chats.json existing, creating...')
    with open("chats.json", "w+") as jsonFile:
        json.dump(data, jsonFile)

updater = Updater(token=config["token"])
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# info_handler = CommandHandler('info', info)
poke_handler = MessageHandler(Filters.text, info)
dispatcher.add_handler(poke_handler)

updater.start_polling()
j = updater.job_queue
