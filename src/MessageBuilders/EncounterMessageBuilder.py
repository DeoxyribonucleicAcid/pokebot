import logging
import math
import random
import time
from io import BytesIO

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
import Message
import Pokemon
from src.EichState import EichState


def build_encounter_message(bot):
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
            image = Pokemon.build_pokemon_catch_img(pokemon_sprite=sprite, direction=pokemon_direction)
            bio = BytesIO()
            bio.name = 'catch_img_' + str(player.chat_id) + '.png'
            image.save(bio, 'PNG')
            bio.seek(0)
            try:
                for i in player.get_messages(Constants.ENCOUNTER_MSG):
                    try:
                        bot.delete_message(chat_id=player.chat_id, message_id=i._id)
                    except telegram.error.BadRequest as e:
                        logging.error(e)
                msg = bot.send_photo(chat_id=player.chat_id, text='catch Pokemon!',
                                     photo=bio,
                                     reply_markup=reply_markup)
                player.messages_to_delete.append(Message.Message(_id=msg.message_id,
                                                                 _title=Constants.ENCOUNTER_MSG,
                                                                 _time_sent=now))
                update = DBAccessor.get_update_query(last_encounter=now,
                                                     in_encounter=True,
                                                     pokemon_direction=pokemon_direction,
                                                     catch_pokemon=pokemon,
                                                     messages_to_delete=player.messages_to_delete)
            except telegram.error.Unauthorized as e:
                update = DBAccessor.get_update_query(last_encounter=now,
                                                     in_encounter=False,
                                                     pokemon_direction=None,
                                                     catch_pokemon=None,
                                                     encounters=False)
                logging.error(e)
            DBAccessor.update_player(_id=player.chat_id, update=update)
