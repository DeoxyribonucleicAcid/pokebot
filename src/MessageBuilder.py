import json
import logging
import math
import os
import random
import sys
import time
import urllib.request
from functools import wraps

import telegram
from emoji import emojize
from telegram import ChatAction, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import src.Constants as Constants
import src.DBAccessor as DBAccessor
import src.Message as Message
import src.Player as Player
import src.Pokemon as Pokemon
from src.EichState import EichState

logger = logging.getLogger(__name__)


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

    if random.random() > 0.90:
        sprite = poke_json['sprites']['front_shiny']
    else:
        sprite = poke_json['sprites']['front_default']

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
        directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/res/tmp/'
        filename = directory + 'image_info_' + str(update.message.chat_id) + '.png'

        Pokemon.get_pokemon_portrait_image(sprite).save(filename, 'PNG')
        bot.send_photo(chat_id=update.message.chat_id,
                       photo=open(filename, 'rb'),
                       caption=text,
                       parse_mode=ParseMode.MARKDOWN)
        os.remove(filename)
    except urllib.request.HTTPError as e:
        bot.send_message(chat_id=update.message.chat_id, text=':( i didn\'t catch that')
    except ConnectionResetError as e:
        logging.error(e)


def build_msg_start(bot, update):
    sprite = 'https://cdn.bulbagarden.net/upload/3/3e/Lets_Go_Pikachu_Eevee_Professor_Oak.png'
    bot.send_photo(chat_id=update.message.chat_id,
                   photo=sprite,
                   caption='Hello there! Welcome to the world of Pok\xe9mon! My name is Oak!'
                           ' People call me the Pok\xe9mon Prof!\n'
                           'I will give you some hints in battle, just type the name of your'
                           ' opponent\'s pokemon in english or german.\n'
                           'Type /start to show this message.\n'
                           'Try the /help and /menu commands')


def build_msg_help(bot, chat_id):
    bot.send_message(chat_id=chat_id, text='Available commands:\n'
                                           '/start : Introduction\n'
                                           '/help : This message\n'
                                           '/menu : Shows menu\n'
                                           '/catch & /nocatch : Toggles encounters\n'
                                           '/bag : Shows pok\xe9mon pouch\n'
                                           '/items : Shows item pouch\n'
                                           '/trade : Shows trade menu\n'
                                           '/chance : Shows encounter chance')


def build_msg_restart(bot, update):
    if EichState.DEBUG:
        bot.send_message(chat_id=update.message.chat_id, text='bot restarted')
        os.execl(sys.executable, sys.executable, *sys.argv)


def build_msg_catch(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        player = Player.Player(chat_id, encounters=True)
        DBAccessor.insert_new_player(player=player)
        bot.send_message(chat_id=chat_id, text='I will poke you, if you stumble over a pokemon.')
    elif not player.encounters:
        update = DBAccessor.get_update_query(encounters=True)
        DBAccessor.update_player(player.chat_id, update)
        bot.send_message(chat_id=chat_id, text='You are on the watch again. Type /nocatch to ignore encounters.')
    elif player.encounters:
        bot.send_message(chat_id=chat_id, text='I will notify as promised. Type /nocatch to ignore encounters.')
    else:
        raise ('Data Error: Corrupt Player')


def build_msg_no_catch(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id, text='You\'re not on the list. Type /catch to get encounters.')
    elif not player.encounters:
        bot.send_message(chat_id=chat_id, text='You\'re not on the list. Type /catch to get encounters.')
    elif player.encounters:
        update = DBAccessor.get_update_query(encounters=False)
        DBAccessor.update_player(player.chat_id, update)
        bot.send_message(chat_id=chat_id, text='You\'re no longer on the list. Type /catch to get encounters.')
    else:
        raise ('Data Error: Corrupt Player')


def build_msg_trade(bot, chat_id):
    bot.send_message(chat_id=chat_id, text='Trading Pok\xe9mon is currently under development. Please try again later.')


def build_msg_encounter(bot):
    logging.info('Encounter')
    cursor = DBAccessor.get_encounter_players_cursor()
    for player in cursor:
        draw = random.random()
        now = time.time()
        last_enc = float(player.last_encounter)
        if player.in_encounter:
            if now - last_enc >= 900:
                # Reset player's catch state
                for i in player.get_messages(Constants.ENCOUNTER_MSG):
                    try:
                        bot.delete_message(chat_id=player.chat_id, message_id=i._id)
                    except telegram.error.BadRequest as e:
                        logging.error(e)
                update = DBAccessor.get_update_query(last_encounter=now,
                                                     in_encounter=False,
                                                     pokemon_direction=None,
                                                     catch_message_id=None,
                                                     catch_pokemon=None)
                DBAccessor.update_player(_id=player.chat_id, update=update)
                logging.info('reset encounter for player ' + str(player.chat_id))
            continue
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
            directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/res/tmp/'
            filename = directory + 'catch_img_' + str(player.chat_id) + '.png'
            Pokemon.build_pokemon_catch_img(pokemon_sprite=sprite,
                                            direction=pokemon_direction).save(filename, 'PNG')
            try:
                for i in player.get_messages(Constants.ENCOUNTER_MSG):
                    try:
                        bot.delete_message(chat_id=player.chat_id, message_id=i._id)
                    except telegram.error.BadRequest as e:
                        logging.error(e)
                msg = bot.send_photo(chat_id=player.chat_id, text='catch Pokemon!',
                                     photo=open(filename, 'rb'),
                                     reply_markup=reply_markup)
                player.messages_to_delete.append(Message.Message(_id=msg.message_id,
                                                                 _title=Constants.ENCOUNTER_MSG,
                                                                 _time_sent=now))
                update = DBAccessor.get_update_query(last_encounter=now,
                                                     in_encounter=True,
                                                     pokemon_direction=pokemon_direction,
                                                     catch_message_id=msg.message_id,
                                                     catch_pokemon=pokemon,
                                                     messages_to_delete=player.messages_to_delete)
            except telegram.error.Unauthorized as e:
                update = DBAccessor.get_update_query(last_encounter=now,
                                                     in_encounter=False,
                                                     pokemon_direction=None,
                                                     catch_message_id=None,
                                                     catch_pokemon=None,
                                                     encounters=False)
                logging.error(e)
            os.remove(filename)
            DBAccessor.update_player(_id=player.chat_id, update=update)

        # bot.send_message(chat_id=player.chat_id, text='current chance: ' + str(chance) + ' draw: ' + str(draw))


def build_msg_bag(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='I have not met you yet. Want to be a Pok\xe9mon trainer? Type /catch.')
        return
    pokemon_sprite_list = []
    caption = ''
    for i in player.pokemon:
        # sprites = [v[1] for v in i.sprites.items() if v[1] is not None]
        caption += '#' + str(i.id) + ' ' + str(i.name) + ' ' + str(int(i.level)) + '\n'
        # pokemon_sprite_list.append(sprites[random.randint(0, len(sprites) - 1)])
        pokemon_sprite_list.append(i.sprites['front'])

    image = Pokemon.build_pokemon_bag_image(pokemon_sprite_list)
    if image is not None:
        directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/res/tmp/'
        filename = directory + 'image_bag_' + str(chat_id) + '.png'
        image.save(filename, 'PNG')

        bot.send_photo(chat_id=chat_id,
                       photo=open(filename, 'rb'),
                       caption=caption, parse_mode=ParseMode.MARKDOWN)
        os.remove(filename)
    else:
        bot.send_message(chat_id=chat_id,
                         text='Your bag is empty, catch some pokemon!')


def build_msg_item_bag(bot, chat_id):
    bot.send_message(chat_id=chat_id, text='Items are currently under development. Please try again later.')
    # bot.send_message(chat_id=chat_id, text=player.items.keys())


def send_menu_message(bot, update):
    player = DBAccessor.get_player(update.message.chat_id)
    if player is None:
        return
    delete_messages_by_type(bot=bot, player=player, type=Constants.MENU_MSG)
    text, reply_markup = build_msg_menu(player)
    msg = bot.send_message(chat_id=update.message.chat_id, text=text,
                           reply_markup=reply_markup)
    player.messages_to_delete.append(Message.Message(msg.message_id, _title=Constants.MENU_MSG, _time_sent=time.time()))
    query = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=query)


def update_menu_message(bot, chat_id, msg_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        return False
    # msg_id = len(player.messages_to_delete) - 1 - next(
    #     (i for i, x in enumerate(reversed(player.messages_to_delete)) if x._title == Constants.MENU_MSG),
    #     len(player.messages_to_delete))
    text, reply_markup = build_msg_menu(player=player)
    try:
        bot.edit_message_text(chat_id=chat_id, text=text, message_id=msg_id,
                              reply_markup=reply_markup)
    except telegram.error.BadRequest as e:
        if e.message != 'Message is not modified':
            raise e


def build_msg_menu(player):
    if player is None:
        return
    if player.encounters:
        catch_button_text = u'Encounters  ' + emojize(":white_check_mark:", use_aliases=True)  # \U00002713'
    else:
        catch_button_text = u'Encounters  ' + emojize(":x:", use_aliases=True)  # \U0000274C'
    keys = [[InlineKeyboardButton(text='Bag', callback_data='menu-bag'),
             InlineKeyboardButton(text='Trade', callback_data='menu-trade')],
            [InlineKeyboardButton(text=catch_button_text, callback_data='menu-catch'),
             InlineKeyboardButton(text='Items', callback_data='menu-items')]]
    text = 'Menu:'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    return text, reply_markup


def process_callback(bot, update):
    data = update.callback_query.data
    player = DBAccessor.get_player(update.effective_chat.id)
    if data.startswith('catch-'):
        option = int(data[6:])
        if option == player.pokemon_direction:
            bot.send_message(chat_id=player.chat_id, text='captured ' + player.catch_pokemon.name + '!')
            for i in player.get_messages(Constants.ENCOUNTER_MSG):
                try:
                    bot.delete_message(chat_id=player.chat_id, message_id=i._id)
                except telegram.error.BadRequest as e:
                    logging.error(e)
            # Reset Player's encounter
            player.pokemon.append(player.catch_pokemon)
            update = DBAccessor.get_update_query(pokemon=player.pokemon,
                                                 in_encounter=False,
                                                 pokemon_direction=None,
                                                 catch_message_id=None,
                                                 catch_pokemon=None)
            DBAccessor.update_player(_id=player.chat_id, update=update)
    elif data.startswith('catchmenu-'):
        if data == 'menu-item':
            pass
        elif data == 'menu-escape':
            pass

    elif data.startswith('menu-'):
        if data == 'menu-bag':
            build_msg_bag(bot, update.effective_message.chat_id)
        elif data == 'menu-trade':
            build_msg_trade(bot=bot, chat_id=update.effective_message.chat_id)
        elif data == 'menu-catch':
            if player.encounters:
                build_msg_no_catch(bot=bot, chat_id=update.effective_message.chat_id)
            else:
                build_msg_catch(bot=bot, chat_id=update.effective_message.chat_id)
            update_menu_message(bot, update.effective_message.chat_id, update.effective_message.message_id)
        elif data == 'menu-items':
            build_msg_item_bag(bot=bot, chat_id=update.effective_message.chat_id)
    else:
        raise ValueError('Invalid callback data: ' + data)


def adjust_encounter_chance(bot, chat_id, chance):
    if EichState.DEBUG:
        if chance is None:
            now = time.time()
            player = DBAccessor.get_player(chat_id)
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
            DBAccessor.update_player(_id=chat_id, update=DBAccessor.get_update_query(last_encounter=adjusted_time))
            # sqrt(86400^e * 0.2, e)
            chance = pow(1 / (24 * 60 * 60) * (now - adjusted_time), math.e)
            msg = bot.send_message(chat_id=chat_id,
                                   text='Updated chance to encounter to ' + str(int(chance * 100)) + '%')
        else:
            msg = bot.send_message(chat_id=chat_id, text='Bad Input')
    else:
        now = time.time()
        player = DBAccessor.get_player(chat_id)
        chance = pow(1 / (24 * 60 * 60) * (now - player.last_encounter), math.e)
        msg = bot.send_message(chat_id=chat_id, text='Current chance is ' + str(int(chance * 100)) + '%')


def delete_messages_by_type(bot, player, type):
    if type is (not Constants.ENCOUNTER_MSG or not Constants.BAG_MSG or not Constants.MENU_MSG):
        return False
    else:
        for i in player.messages_to_delete:
            # duplicate in Player.Player.delete_message() but more efficient
            if i._title == type:
                bot.delete_message(chat_id=player.chat_id, message_id=i._id)
                player.messages_to_delete.remove(i)

        update = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(_id=player.chat_id, update=update)
