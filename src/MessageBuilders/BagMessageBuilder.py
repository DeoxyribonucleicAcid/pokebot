import logging
import time
from io import BytesIO

from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
import Texter
from Entities import Pokemon, Message
from MessageBuilders import MessageHelper


def build_msg_bag(bot, chat_id, trade_mode, page_number):
    page_number = int(page_number)
    trade_mode = bool(int(trade_mode))
    pokecount = 8
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text=Texter.get_text(player, 'new_player_msg'))
        return
    pokelist = player.pokemon_team + player.pokemon
    pokemon_sprite_list = []
    caption = ''
    if len(pokelist) > pokecount:
        caption = '*Page Number: *' + str(page_number) + '  Pok\xe9 ' + str(
            (page_number * pokecount) + 1) + '-' + (
                      str((page_number + 1) * pokecount) if (page_number + 1) * pokecount <= len(
                          pokelist) else str(len(pokelist))) + '/' + str(len(pokelist)) + '\n'
    list_start = pokecount * page_number
    list_end = pokecount * (page_number + 1) if len(pokelist) >= pokecount * (page_number + 1) else len(
        pokelist)
    page_list = pokelist[list_start:list_end]
    keys = []
    for pokemon_id in page_list:
        pokemon = DBAccessor.get_pokemon_by_id(pokemon_id)
        if pokemon is None:
            logging.error('Pokemon with id {} None!'.format(pokemon))
            pokelist.remove(pokemon_id)
            DBAccessor.update_player(chat_id, DBAccessor.get_update_query_player(pokelist))
        keys.append([InlineKeyboardButton(text=pokemon.name,
                                          callback_data=Constants.CALLBACK.POKE_DISPLAY_CONFIG(trade_mode=trade_mode,
                                                                                               page_number=page_number,
                                                                                               pokemon_id=pokemon.poke_id))
                     ])
        pokemon_sprite_list.append(pokemon.sprites['front'])
    image = Pokemon.build_pokemon_bag_image(pokemon_sprite_list)
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.POKE_DISPLAY_MSG)
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.BAG_MSG)
    if image is not None:
        bio = BytesIO()
        bio.name = 'image_bag_' + str(chat_id) + '.png'
        image.save(bio, 'PNG')
        bio.seek(0)

        keys.append([])
        if page_number > 0:
            keys[-1].append(InlineKeyboardButton(text='\u2190',
                                                 callback_data=Constants.CALLBACK.BAG_PAGE(trade_mode,
                                                                                           page_number - 1)))
        if len(pokelist) > list_end:
            keys[-1].append(InlineKeyboardButton(text='\u2192',
                                                 callback_data=Constants.CALLBACK.BAG_PAGE(trade_mode,
                                                                                           page_number + 1)))

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)

        msg = bot.send_photo(chat_id=chat_id,
                             photo=bio,
                             reply_markup=reply_markup,
                             caption=caption, parse_mode=ParseMode.MARKDOWN)
    else:
        msg = bot.send_message(chat_id=chat_id,
                               text=Texter.get_text(player, 'empty_bag_msg'))
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.MESSAGE_TYPES.BAG_MSG, _time_sent=time.time()))
    update = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=update)
