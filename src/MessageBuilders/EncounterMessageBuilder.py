import logging
import math
import random
import time
from io import BytesIO

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
from Entities import Pokemon, Message
from Entities.Encounter import Encounter
from MessageBuilders import MessageHelper
from src.EichState import EichState


def build_encounter_message(bot):
    logging.info('Encounter')
    cursor = DBAccessor.get_encounter_players_cursor()
    for player in cursor:
        draw = random.random()
        now = time.time()
        last_enc = float(player.last_encounter)
        if player.encounter is not None:
            if now - last_enc >= 900:
                # Reset player's catch state
                for i in player.get_messages(Constants.ENCOUNTER_MSG):
                    try:
                        bot.delete_message(chat_id=player.chat_id, message_id=i._id)
                    except telegram.error.BadRequest as e:
                        logging.error(e)
                query = {'$set': {'last_encounter': now}, '$unset': {'encounter': 1}}
                DBAccessor.update_player(_id=player.chat_id, update=query)
                logging.info('reset encounter for player ' + str(player.chat_id))
            continue
        chance = pow(1 / (24 * 60 * 60) * (now - last_enc), math.e)
        if 0 < draw < chance:
            pokemon_name = EichState.names_dict['pokenames'][
                random.choice(list(EichState.names_dict['pokenames'].keys()))]
            pokemon_direction = random.randint(0, 8)
            pokemon = Pokemon.get_random_poke(Pokemon.get_pokemon_json(pokemon_name), 10)
            keys = [[InlineKeyboardButton(text='\u2196', callback_data=Constants.CALLBACK.CATCH(0)),
                     InlineKeyboardButton(text='\u2191', callback_data=Constants.CALLBACK.CATCH(1)),
                     InlineKeyboardButton(text='\u2197', callback_data=Constants.CALLBACK.CATCH(2))],
                    [InlineKeyboardButton(text='\u2190', callback_data=Constants.CALLBACK.CATCH(3)),
                     InlineKeyboardButton(text='o', callback_data=Constants.CALLBACK.CATCH(4)),
                     InlineKeyboardButton(text='\u2192', callback_data=Constants.CALLBACK.CATCH(5))],
                    [InlineKeyboardButton(text='\u2199', callback_data=Constants.CALLBACK.CATCH(6)),
                     InlineKeyboardButton(text='\u2193', callback_data=Constants.CALLBACK.CATCH(7)),
                     InlineKeyboardButton(text='\u2198', callback_data=Constants.CALLBACK.CATCH(8))]]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
            sprites = {k: v for k, v in pokemon.sprites.items() if v is not None}
            sprite = pokemon.sprites[random.choice(list(sprites.keys()))]
            image = Pokemon.build_pokemon_catch_img(pokemon_sprite=sprite, direction=pokemon_direction)
            bio = BytesIO()
            bio.name = 'catch_img_' + str(player.chat_id) + '.png'
            image.save(bio, 'PNG')
            bio.seek(0)
            try:
                MessageHelper.delete_messages_by_type(bot, chat_id=player.chat_id, type=Constants.ENCOUNTER_MSG)
                msg = bot.send_photo(chat_id=player.chat_id, text='catch Pokemon!',
                                     photo=bio,
                                     reply_markup=reply_markup)
                player.messages_to_delete.append(Message.Message(_id=msg.message_id,
                                                                 _title=Constants.ENCOUNTER_MSG,
                                                                 _time_sent=now))
                encounter = Encounter(pokemon_direction=pokemon_direction, pokemon=pokemon)
                query = {'$set': {'last_encounter': now,
                                  'messages_to_delete': [i.serialize_msg() for i in player.messages_to_delete],
                                  'encounter': encounter.serialize()}}
            except telegram.error.Unauthorized as e:
                query = {'$set': {'last_encounter': now, 'encounters': False}, '$unset': {'encounter': 1}}
                logging.error(e)
            DBAccessor.update_player(_id=player.chat_id, update=query)


def catch(bot, chat_id, option):
    player = DBAccessor.get_player(chat_id)
    option = int(option)
    if option == player.encounter.pokemon_direction:
        if player.encounter.pokemon._id == player.pokemon[-1]._id:
            return
        bot.send_message(chat_id=player.chat_id, text='captured ' + player.encounter.pokemon.name + '!')
        for i in player.get_messages(Constants.ENCOUNTER_MSG):
            try:
                bot.delete_message(chat_id=player.chat_id, message_id=i._id)
            except telegram.error.BadRequest as e:
                logging.error(e)
        # Reset Player's encounter
        player.pokemon.append(player.encounter.pokemon)
        update = DBAccessor.get_update_query(pokemon=player.pokemon, encounter=None)
        DBAccessor.update_player(_id=player.chat_id, update=update)
