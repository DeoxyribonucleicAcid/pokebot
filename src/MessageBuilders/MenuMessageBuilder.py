import time

import telegram
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
import Message
import Player
from MessageBuilders import MessageHelper


def send_menu_message(bot, update):
    player = DBAccessor.get_player(update.message.chat_id)
    if player is not None:
        MessageHelper.delete_messages_by_type(bot=bot, player=player, type=Constants.MENU_MSG)
    text, reply_markup = build_msg_menu(player.encounters if player is not None else False)
    msg = bot.send_message(chat_id=update.message.chat_id, text=text,
                           reply_markup=reply_markup)
    if player is None:
        new_player = Player.Player(update.message.chat_id, messages_to_delete=[
            Message.Message(_id=msg.message_id, _title=Constants.MENU_MSG, _time_sent=time.time())], encounters=False)
        DBAccessor.insert_new_player(new_player)
    else:
        player.messages_to_delete.append(
            Message.Message(msg.message_id, _title=Constants.MENU_MSG, _time_sent=time.time()))
        query = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(_id=player.chat_id, update=query)


def update_menu_message(bot, chat_id, msg_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        return False
    # msg_id = len(player.messages_to_delete) - 1 - next(
    #     (i for i, x in enumerate(reversed(player.messages_to_delete)) if x._title == Constants.MENU_MSG),
    #     len(player.messages_to_delete))
    text, reply_markup = build_msg_menu(encounters=player.encounters)
    try:
        bot.edit_message_text(chat_id=chat_id, text=text, message_id=msg_id,
                              reply_markup=reply_markup)
    except telegram.error.BadRequest as e:
        if e.message != 'Message is not modified':
            raise e


def build_msg_menu(encounters: bool):
    if encounters:
        catch_button_text = u'Encounters  ' + emojize(":white_check_mark:", use_aliases=True)  # \U00002713'
    else:
        catch_button_text = u'Encounters  ' + emojize(":x:", use_aliases=True)  # \U0000274C'
    keys = [[InlineKeyboardButton(text='Bag', callback_data='menu-bag'),
             InlineKeyboardButton(text='Trade', callback_data='menu-trade')],
            [InlineKeyboardButton(text=catch_button_text, callback_data='menu-catch'),
             InlineKeyboardButton(text='Items', callback_data='menu-items')],
            [InlineKeyboardButton(text='Friend List', callback_data='menu-friendlist')]]
    text = 'Menu:'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    return text, reply_markup
