import logging
import os
import sys
import time
from functools import wraps
from io import BytesIO

import math
from telegram import ChatAction

import DBAccessor as DBAccessor
from Entities import Pokemon
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
            DBAccessor.update_player(_id=chat_id,
                                     update=DBAccessor.get_update_query_player(last_encounter=adjusted_time))
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


def test(bot, update):
    player = DBAccessor.get_player(update.effective_message.chat_id)
    if len(player.pokemon) < 5:
        msg = bot.send_message(chat_id=player.chat_id,
                               text='Not enough pokemon!')
        return

    pokemon_player = [DBAccessor.get_pokemon_by_id(i) for i in player.pokemon[:3]]
    pokemon_enemy = DBAccessor.get_pokemon_by_id(player.pokemon[4])
    champion_player = DBAccessor.get_pokemon_by_id(player.pokemon[5])
    img = Pokemon.build_pokemon_duel_info_image(pokemon_player, champion_player, pokemon_enemy)
    if img is not None:
        bio = BytesIO()
        bio.name = 'image_duel_info_' + str(player.chat_id) + '.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        msg = bot.send_photo(chat_id=player.chat_id,
                             photo=bio,
                             caption='Current Status')
    else:
        msg = bot.send_message(chat_id=player.chat_id,
                               text='Something went wrong!')
