import logging
import time
from io import BytesIO

from emoji import emojize
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
from Entities import Pokemon, Message
from MessageBuilders import MessageHelper


def build_poke_display(bot, chat_id, trade_mode, page_num, poke_id):
    page_num = int(page_num)
    trade_mode = bool(int(trade_mode))
    player = DBAccessor.get_player(chat_id)
    pokemon = player.get_pokemon(int(poke_id))
    # Delete msgs
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.BAG_MSG)
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.POKE_DISPLAY_MSG)

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
            Message.Message(_id=msg.message_id, _title=Constants.MESSAGE_TYPES.POKE_DISPLAY_MSG,
                            _time_sent=time.time()))
        update = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
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


def poke_edit_name(bot, chat_id, pokemon_id):
    pokemon_id = int(pokemon_id)
    player = DBAccessor.get_player(int(chat_id))
    pokemon = player.get_pokemon(int(pokemon_id))
    logging.info(str(pokemon_id) + ' ' + str(chat_id))
    if pokemon is None:
        bot.send_message(chat_id=chat_id, text='An error occurred! Couldn\'t find requested pokemon!')
        return
    query = DBAccessor.get_update_query_player(nc_msg_state=Constants.NC_MSG_States.DISPLAY_EDIT_NAME,
                                               edit_pokemon_id=pokemon_id)
    DBAccessor.update_player(_id=chat_id, update=query)
    bot.send_message(chat_id=chat_id, text='Send me the new name of ' + str(pokemon.name))


def poke_change_name(bot, chat_id, new_name):
    player = DBAccessor.get_player(chat_id)
    pokemon = player.get_pokemon(int(player.edit_pokemon_id))
    if pokemon is None:
        bot.send_message(chat_id=player.chat_id, text='Couldn\'t find editing pokemon. Blame the devs pls')
        # MessageHelper.reset_states(bot=bot, chat_id=player.chat_id) # TODO: do this (remove comment)
        return
    pokemon.name = new_name
    player.update_pokemon(pokemon=pokemon)
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.POKE_DISPLAY_MSG)
    query = DBAccessor.get_update_query_player(pokemon=player.pokemon, edit_pokemon_id=None)
    DBAccessor.update_player(_id=chat_id, update=query)
    build_poke_display(bot=bot, chat_id=chat_id, trade_mode=False, page_num=0, poke_id=pokemon._id)


def poke_edit_team(bot, chat_id, poke_id):
    player = DBAccessor.get_player(chat_id)
    if len(player.pokemon_team) >= 6:
        bot.send_message(chat_id=chat_id,
                         text='Your team is full, remove some first!')
    else:
        new_team_pokemon = player.remove_pokemon(pokemon_id=int(poke_id))
        player.pokemon_team.append(new_team_pokemon)
        query = DBAccessor.get_update_query_player(pokemon=player.pokemon, pokemon_team=player.pokemon_team)
        DBAccessor.update_player(_id=chat_id, update=query)
        bot.send_message(chat_id=chat_id, text='Added ' + str(new_team_pokemon.name) + ' to your team!')
