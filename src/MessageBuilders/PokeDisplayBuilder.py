import logging
import time
from io import BytesIO

import telegram
from emoji import emojize
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
import Message
import Pokemon


def build_poke_display(bot, chat_id, trade_mode, page_num, poke_id):
    page_num = int(page_num)
    trade_mode = bool(int(trade_mode))
    player = DBAccessor.get_player(chat_id)
    pokemon = player.get_pokemon(int(poke_id))
    for i in player.get_messages(Constants.BAG_MSG) + player.get_messages(Constants.POKE_DISPLAY_MSG):
        try:
            bot.delete_message(chat_id=player.chat_id, message_id=i._id)
        except telegram.error.BadRequest as e:
            logging.error(e)

    text = 'Pokedex ID: ' + str(pokemon.pokedex_id) + '\n' + \
           'Name: ' + str(pokemon.name) + '\n' + \
           'Level: ' + str(pokemon.level) + '\n'

    bio = BytesIO()
    bio.name = 'image_displ_' + str(chat_id) + '.png'
    image = Pokemon.get_pokemon_portrait_image(pokemon_sprite=pokemon.sprites['front'])
    image.save(bio, 'PNG')
    bio.seek(0)
    reply_keyboard = get_display_keyboard_editing(
        poke_id=pokemon._id, page_num=page_num) if not trade_mode else get_display_keyboard_trading(
        poke_id=pokemon._id, page_num=page_num)
    try:
        msg = bot.send_photo(chat_id=chat_id,
                             photo=bio,
                             caption=text,
                             parse_mode=ParseMode.MARKDOWN,
                             reply_markup=reply_keyboard)
        player.messages_to_delete.append(
            Message.Message(_id=msg.message_id, _title=Constants.POKE_DISPLAY_MSG, _time_sent=time.time()))
        update = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(_id=player.chat_id, update=update)
    except ConnectionResetError as e:
        logging.error(e)


def get_display_keyboard_editing(poke_id, page_num):
    keys = [
        [InlineKeyboardButton(text='Edit Name', callback_data=Constants.CALLBACK.POKE_DISPLAY_EDIT_NAME(poke_id))],
        [InlineKeyboardButton(text='Add to Team', callback_data=Constants.CALLBACK.POKE_DISPLAY_EDIT_TEAM(poke_id))],
        [InlineKeyboardButton(text='\u2190 Back', callback_data=Constants.CALLBACK.BAG_PAGE(False, page_num))]
    ]
    reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
    return reply_keyboard


def get_display_keyboard_trading(poke_id, page_num):
    keys = [
        [InlineKeyboardButton(text=emojize(":white_check_mark:", use_aliases=True) + 'Choose',
                              callback_data=Constants.CALLBACK.TRADE_CHOOSE_POKEMON(poke_id))],
        [InlineKeyboardButton(text='\u2190 Back',
                              callback_data=Constants.CALLBACK.BAG_PAGE(True, page_num))]
    ]
    reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
    return reply_keyboard
