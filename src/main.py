import random
import sys
from pprint import pprint

from telegram import ChatAction, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
import urllib.request
import json
import os.path
from functools import wraps
import argparse
import setproctitle


class EichState:
    DEBUG = False
    url = 'https://pokeapi.co/api/v2/'
    names_dict = {}
    opener = urllib.request.build_opener()
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
    pokeurl = EichState.url + 'pokemon/' + pokemon + '/'
    try:
        poke_response = EichState.opener.open(pokeurl)
    except urllib.request.HTTPError as e:
        logging.error('Pokemon not found: ' + '\n' + pokeurl)
        raise e

    poke_json = json.load(poke_response)
    sprites = {k: v for k, v in poke_json[u'sprites'].items() if v != None}
    type_urls = []
    for type in poke_json[u'types']: type_urls.append(type[u'type'][u'url'])
    double_damage_types = []
    half_damage_types = []
    no_damage_types = []
    types = []
    for type in type_urls:
        try:
            type_json = json.load(EichState.opener.open(type))
            types.append(type_json[u'name'])
            dd_relations = type_json[u'damage_relations'][u'double_damage_from']
            hd_relations = type_json[u'damage_relations'][u'half_damage_from']
            nd_relations = type_json[u'damage_relations'][u'no_damage_from']
            for dd_type in dd_relations:
                double_damage_types.append(dd_type[u'name'])
            for hd_type in hd_relations:
                half_damage_types.append(hd_type[u'name'])
            for nd_type in nd_relations:
                no_damage_types.append(nd_type[u'name'])
        except urllib.request.HTTPError as e:
            logging.error('Type not found: ' + '\n' + type)
            raise e

    sprite = sprites[random.choice(list(sprites.keys()))]
    dd_types_str = ', '.join(map(str, list(set(double_damage_types))))
    hd_types_str = ', '.join(map(str, list(set(half_damage_types))))
    nd_types_str = ', '.join(map(str, list(set(no_damage_types))))
    types_str = ', '.join(map(str, types))
    name_str = str(poke_json[u'name'])
    id_str = str(poke_json[u'id'])

    pprint(sprite)
    pprint(name_str)
    pprint(id_str)
    pprint(types_str)
    pprint(dd_types_str)

    text = name_str + ' #' + id_str + '\n' + types_str + '\nAttack with:\n' + dd_types_str + '\nDon\'t use:\n' + hd_types_str
    if no_damage_types != []:
        text += '\nor worse:\n' + nd_types_str
    return text, sprite


@send_typing_action
def info(bot, update):
    pokemon = update.message.text.lower()
    if pokemon in EichState.names_dict["pokenames"].keys():
        pokemon = EichState.names_dict["pokenames"][pokemon]
    pokemon = pokemon.lower()
    try:
        text, sprite = getPokeInfo(pokemon)
        bot.send_photo(chat_id=update.message.chat_id, photo=sprite, caption=text, parse_mode=ParseMode.MARKDOWN)
    except urllib.request.HTTPError:
        bot.send_message(chat_id=update.message.chat_id, text=':( i didn\'t catch that')


@send_typing_action
def start(bot, update):
    sprite = 'https://cdn.bulbagarden.net/upload/3/3e/Lets_Go_Pikachu_Eevee_Professor_Oak.png'
    bot.send_photo(chat_id=update.message.chat_id,
                   photo=sprite,
                   caption='Hello there! Welcome to the world of Pokémon! My name is Oak! People call me the Pokémon Prof!\n'
                           'I will give you some hints in battle, just type the name of your opponent\'s pokemon in english or german.\n'
                           'Type /start to show this message.')


def restart(bot, update):
    if EichState.DEBUG:
        os.execl(sys.executable, sys.executable, *sys.argv)
        bot.send_message(chat_id=update.message.chat_id, text='bot restarted')


def main():
    setproctitle.setproctitle("ProfessorEich")
    logging.basicConfig(filename='.log', level=logging.DEBUG, filemode='w')
    parser = argparse.ArgumentParser(description='Basic pokemon bot.')
    parser.set_defaults(which='no_arguments')
    parser.add_argument('-d', '--debug', action='store_true', required=False, help='Debug mode')

    args = parser.parse_args()
    if args.debug == None:
        EichState.DEBUG = False
    else:
        EichState.DEBUG = True
    print(EichState.DEBUG)

    if os.path.isfile('./conf.json'):
        with open('conf.json') as f:
            config = json.load(f)
    else:
        raise EnvironmentError("Config file not existent or wrong format")

    if os.path.isfile('./name_dict.json'):
        with open('name_dict.json') as f:
            EichState.names_dict = json.load(f)
    else:
        raise EnvironmentError("Names file not existent or wrong format")

    updater = Updater(token=config["token"])
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # info_handler = CommandHandler('info', info)
    poke_handler = MessageHandler(Filters.text, info)
    start_handler = CommandHandler('start', start)
    restart_handler = CommandHandler('restart', restart)
    dispatcher.add_handler(poke_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(restart_handler)

    updater.start_polling()
    j = updater.job_queue


main()
