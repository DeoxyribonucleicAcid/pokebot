import argparse
import json
import logging
import math
import os
import random
import setproctitle
import sys
import time
import urllib.request
from functools import wraps

import telegram
from telegram import ChatAction, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

from src import Pokemon
from src.EichState import EichState
from src.Player import Player


def prepare_environment():
    setproctitle.setproctitle("ProfessorEich")
    logging.basicConfig(filename='.log', level=logging.DEBUG, filemode='w')
    parser = argparse.ArgumentParser(description='Basic pokemon bot.')
    parser.set_defaults(which='no_arguments')
    parser.add_argument('-d', '--debug', action='store_true', required=False, help='Debug mode')

    if os.path.isfile('./conf.json'):
        with open('conf.json') as f:
            config = json.load(f)
    else:
        raise EnvironmentError("Config file not existent or wrong format")
    args = parser.parse_args()
    if args.debug is None:
        EichState.DEBUG = False
        EichState.token = config['token']
    else:
        EichState.DEBUG = True
        EichState.token = config['test_token']

    if os.path.isfile('./name_dict.json'):
        with open('name_dict.json') as f:
            EichState.names_dict = json.load(f)
    else:
        raise EnvironmentError("Names file not existent or wrong format")
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(*args, **kwargs):
        bot, update = args
        bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(bot, update, **kwargs)

    return command_func


def get_poke_info(pokemon):
    poke_json = Pokemon.get_pokemon_json(pokemon)
    sprites = {k: v for k, v in poke_json[u'sprites'].items() if v is not None}
    type_urls = []
    for poke_type in poke_json[u'types']:
        type_urls.append(poke_type[u'type'][u'url'])
    double_damage_types = []
    half_damage_types = []
    no_damage_types = []
    types = []
    for poke_type in type_urls:
        try:
            type_json = json.load(EichState.opener.open(poke_type))
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
            logging.error('Type not found: ' + '\n' + poke_type)
            raise e

    sprite = sprites[random.choice(list(sprites.keys()))]
    dd_types_str = ', '.join(map(str, list(set(double_damage_types))))
    hd_types_str = ', '.join(map(str, list(set(half_damage_types))))
    nd_types_str = ', '.join(map(str, list(set(no_damage_types))))
    types_str = ', '.join(map(str, types))
    name_str = str(poke_json[u'name'])
    id_str = str(poke_json[u'id'])

    text = name_str + ' #' + id_str + '\n' + types_str + '\nAttack with:\n' + dd_types_str + '\nDon\'t use:\n' + hd_types_str
    if len(no_damage_types) != 0:
        text += '\nor worse:\n' + nd_types_str
    return text, sprite


def build_msg_info(bot, update):
    pokemon = update.message.text.lower()
    if pokemon in EichState.names_dict["pokenames"].keys():
        pokemon = EichState.names_dict["pokenames"][pokemon]
    pokemon = pokemon.lower()
    try:
        text, sprite = get_poke_info(pokemon)
        bot.send_photo(chat_id=update.message.chat_id,
                       photo=sprite,  # open(Pokemon.get_sprite_dir(pokemon), 'rb'),
                       caption=text,
                       parse_mode=ParseMode.MARKDOWN)
    except urllib.request.HTTPError as e:
        bot.send_message(chat_id=update.message.chat_id, text=':( i didn\'t catch that')
    except ConnectionResetError as e:
        logging.error(e)


def build_msg_start(bot, update):
    sprite = 'https://cdn.bulbagarden.net/upload/3/3e/Lets_Go_Pikachu_Eevee_Professor_Oak.png'
    bot.send_photo(chat_id=update.message.chat_id,
                   photo=sprite,
                   caption='Hello there! Welcome to the world of Pokémon! My name is Oak!'
                           ' People call me the Pokémon Prof!\n'
                           'I will give you some hints in battle, just type the name of your'
                           ' opponent\'s pokemon in english or german.\n'
                           'Type /start to show this message.')


def build_msg_restart(bot, update):
    if EichState.DEBUG:
        bot.send_message(chat_id=update.message.chat_id, text='bot restarted')
        os.execl(sys.executable, sys.executable, *sys.argv)


def build_msg_catch(bot, chat_id):
    player = EichState.fileAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id, text='I will poke you, if you stumble over a pokemon.')
        player = Player(chat_id, encounters=True)
        EichState.fileAccessor.commit_player(player)
        EichState.fileAccessor.persist_players()
    elif not player.encounters:
        EichState.fileAccessor.commit_player(Player.update_player(player, encounters=True))
        EichState.fileAccessor.persist_players()
        bot.send_message(chat_id=chat_id, text='You are on the watch again. Type /nocatch to ignore encounters.')
    elif player.encounters:
        bot.send_message(chat_id=chat_id, text='I will notify as promised. Type /nocatch to ignore encounters.')
    else:
        raise ('Data Error: Corrupt Player')


def build_msg_no_catch(bot, chat_id):
    player = EichState.fileAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id, text='You\'re not on the list. Type /catch to get encounters.')
    elif not player.encounters:
        bot.send_message(chat_id=chat_id, text='You\'re not on the list. Type /catch to get encounters.')
    elif player.encounters:
        EichState.fileAccessor.commit_player(Player.update_player(player, encounters=False))
        EichState.fileAccessor.persist_players()
        bot.send_message(chat_id=chat_id, text='You\'re no longer on the list. Type /catch to get encounters.')
    else:
        raise ('Data Error: Corrupt Player')


def build_msg_encounter(bot):
    players = EichState.fileAccessor.get_players()
    if players is not None:
        for player in players:
            if player.encounters is False:
                continue
            draw = random.random()
            now = time.time()
            last_enc = float(player.last_encounter)
            if player.in_encounter:
                if now - last_enc >= 900:
                    # Reset player's catch state
                    msg_id = player.catch_message_id
                    try:
                        bot.delete_message(chat_id=player.chat_id, message_id=msg_id)
                    except telegram.error.BadRequest as e:
                        logging.error(e)
                    player = Player(chat_id=player.chat_id, items=player.items, pokemon=player.pokemon,
                                    last_encounter=now, in_encounter=False, pokemon_direction=None,
                                    catch_message_id=None, catch_pokemon=None, encounters=player.encounters)
                    EichState.fileAccessor.commit_player(player)
                    EichState.fileAccessor.persist_players()
                    print('reset encounter for player ' + str(player.chat_id))
                continue
            print('encounter')
            chance = pow(1 / (24 * 60 * 60) * (now - last_enc), math.e)
            if 0 < draw < chance:
                pokemon_name = EichState.names_dict['pokenames'][
                    random.choice(list(EichState.names_dict['pokenames'].keys()))]
                pokemon_direction = random.randint(0, 8)
                pokemon = Pokemon.get_random_poke(Pokemon.get_pokemon_json(pokemon_name), 10)
                keys = [[InlineKeyboardButton(text='\u2196', callback_data='catch-0'),
                         InlineKeyboardButton(text='\u2191', callback_data='catch-1'),
                         InlineKeyboardButton(text='\u2197', callback_data='catch-2')],
                        [InlineKeyboardButton(text='\u2190', callback_data='catch-3'),
                         InlineKeyboardButton(text='o', callback_data='catch-4'),
                         InlineKeyboardButton(text='\u2192', callback_data='catch-5')],
                        [InlineKeyboardButton(text='\u2199', callback_data='catch-6'),
                         InlineKeyboardButton(text='\u2193', callback_data='catch-7'),
                         InlineKeyboardButton(text='\u2198', callback_data='catch-8')]]
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
                sprites = {k: v for k, v in pokemon.sprites.items() if v is not None}
                sprite = pokemon.sprites[random.choice(list(sprites.keys()))]
                Pokemon.build_pokemon_catch_img(pokemon_sprite=sprite,
                                                direction=pokemon_direction).save('catch_img.png')
                msg = bot.send_photo(chat_id=player.chat_id, text='catch Pokemon!',
                                     photo=open('catch_img.png', 'rb'), reply_markup=reply_markup)
                # Todo: last_encounter=time.time()
                player = Player(chat_id=player.chat_id, items=player.items, pokemon=player.pokemon,
                                last_encounter=last_enc, in_encounter=True, pokemon_direction=pokemon_direction,
                                catch_message_id=msg.message_id, catch_pokemon=pokemon, encounters=player.encounters)
                EichState.fileAccessor.commit_player(player)
                EichState.fileAccessor.persist_players()

            # bot.send_message(chat_id=player.chat_id, text='current chance: ' + str(chance) + ' draw: ' + str(draw))
    else:
        return


def build_msg_bag(bot, chat_id):
    player = EichState.fileAccessor.get_player(chat_id)
    pokemon_sprite_list = []
    caption = ''
    for i in player.pokemon:
        sprites = [v[1] for v in i.sprites.items() if v[1] is not None]
        caption += '#' + str(i.id) + ' ' + str(i.name) + ' ' + str(int(i.level)) + '\n'

        pokemon_sprite_list.append(sprites[random.randint(0, len(sprites) - 1)])
    Pokemon.build_pokemon_bag_image(pokemon_sprite_list).save('/tmp/image_bag_' + str(chat_id) + '.png')

    bot.send_photo(chat_id=chat_id,
                   photo=open('/tmp/image_bag_' + str(chat_id) + '.png', 'rb'),
                   caption=caption, parse_mode=ParseMode.MARKDOWN)


def build_msg_item_bag(bot, update):
    chat_id = update.message.chat_id
    player = EichState.fileAccessor.get_player(chat_id)
    bot.send_message(chat_id=chat_id, text=player.items.keys())


def build_msg_menu(bot, update):
    keys = [[InlineKeyboardButton(text='Bag', callback_data='menu-bag'),
             InlineKeyboardButton(text='Trade', callback_data='menu-trade')],
            [InlineKeyboardButton(text='Catch', callback_data='menu-catch'),
             InlineKeyboardButton(text='Items', callback_data='menu-items')]]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    msg = bot.send_message(chat_id=update.message.chat_id, text='catch Pokemon!',
                           reply_markup=reply_markup)


def process_callback(bot, update):
    print('Callback!')
    data = update.callback_query.data
    if data.startswith('catch-'):
        player = EichState.fileAccessor.get_player(update.effective_chat.id)
        option = int(data[6:])
        if option == player.pokemon_direction:
            bot.send_message(chat_id=player.chat_id, text='captured Pokemon!')
            bot.delete_message(chat_id=player.chat_id, message_id=update.effective_message.message_id)
            # Todo: last_encounter=time.time()
            # Reset Player's encounter
            player.pokemon.append(player.catch_pokemon)
            player = Player(chat_id=player.chat_id, items=player.items, pokemon=player.pokemon,
                            last_encounter=player.last_encounter, in_encounter=False, pokemon_direction=None,
                            catch_message_id=None, catch_pokemon=None, encounters=player.encounters)
            EichState.fileAccessor.commit_player(player)
            EichState.fileAccessor.persist_players()
    elif data.startswith('menu-'):
        if data == 'menu-item':
            pass
        elif data == 'menu-escape':
            pass
        elif data == 'menu-trade':
            pass
        elif data == 'menu-catch':
            build_msg_catch(bot=bot, chat_id=update.effective_message.chat_id)
        elif data == 'menu-bag':
            build_msg_bag(bot, update.effective_message.chat_id)
    else:
        raise ValueError('Invalid callback data: ' + data)


def adjust_encounter_chance(bot, chat_id, chance):
    if chance is None:
        now = time.time()
        player = EichState.fileAccessor.get_player(chat_id)
        chance = pow(1 / (24 * 60 * 60) * (now - player.last_encounter), math.e)
        msg = bot.send_message(chat_id=chat_id, text='Current chance is ' + str(int(chance * 100)) +
                                                     '%\nAppend a number like /chance 80 to set it')
        return
    if 1 < chance <= 100:
        chance = chance / 100
    if 0 <= chance <= 1:
        time_elapsed = float((86400 ** math.e * chance)) ** float((1 / math.e))
        now = time.time()
        adjusted_time = now - time_elapsed
        player = Player.update_player(player=EichState.fileAccessor.get_player(chat_id), last_encounter=adjusted_time)
        EichState.fileAccessor.commit_player(player=player)
        EichState.fileAccessor.persist_players()
        # sqrt(86400^e * 0.2, e)
        chance = pow(1 / (24 * 60 * 60) * (now - adjusted_time), math.e)
        msg = bot.send_message(chat_id=chat_id, text='Updated chance to encounter to ' + str(int(chance * 100)) + '%')
        print(now, adjusted_time, chance)
    else:
        msg = bot.send_message(chat_id=chat_id, text='Bad Input')
