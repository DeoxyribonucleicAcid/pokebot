import time

import telegram
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
from Entities import Player, Message
from Entities.Trade import Trade
from MessageBuilders import MessageHelper, ToggleCatchMessageBuilder


def send_menu_message(bot, update):
    player = DBAccessor.get_player(update.message.chat_id)
    if player is not None:
        MessageHelper.delete_messages_by_type(bot=bot, chat_id=update.message.chat_id,
                                              type=Constants.MENU_MSG)
    text, reply_markup = build_msg_menu(player.encounters if player is not None else False, trade=player.trade)
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
    text, reply_markup = build_msg_menu(encounters=player.encounters, trade=player.trade)
    try:
        bot.edit_message_text(chat_id=chat_id, text=text, message_id=msg_id,
                              reply_markup=reply_markup)
    except telegram.error.BadRequest as e:
        if e.message != 'Message is not modified':
            raise e


def build_msg_menu(encounters: bool, trade: Trade):
    x = None
    if encounters:
        catch_button_text = u'Encounters  ' + emojize(":white_check_mark:", use_aliases=True)  # \U00002713'
    else:
        x = emojize(":x:", use_aliases=True) if x is None else x
        catch_button_text = u'Encounters  {}'.format(x)  # \U0000274C'
    keys = [[InlineKeyboardButton(text='Bag', callback_data=Constants.CALLBACK.MENU_BAG),
             InlineKeyboardButton(text='Trade', callback_data=Constants.CALLBACK.MENU_TRADE)],
            [InlineKeyboardButton(text=catch_button_text, callback_data=Constants.CALLBACK.MENU_CATCH),
             InlineKeyboardButton(text='Items', callback_data=Constants.CALLBACK.MENU_ITEMS)],
            [InlineKeyboardButton(text='Friend List', callback_data=Constants.CALLBACK.MENU_FRIENDLIST)]]
    if trade is not None:
        x = emojize(":x:", use_aliases=True) if x is None else x
        keys.append([InlineKeyboardButton(
            text='{} Abort trade with {} {}'.format(x, DBAccessor.get_player(int(trade.partner_id)).username, x),
            callback_data=Constants.CALLBACK.TRADE_ABORT)])
    text = 'Menu:'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    return text, reply_markup


def toggle_encounter(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    menu_msg_id = player.get_messages(Constants.MENU_MSG)[-1]._id
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id,
                                          type=Constants.MENU_INFO_MSG)
    if player.encounters:
        ToggleCatchMessageBuilder.build_no_catch_message(bot=bot, chat_id=chat_id)
    else:
        ToggleCatchMessageBuilder.build_catch_message(bot=bot, chat_id=chat_id)
    update_menu_message(bot, chat_id, menu_msg_id)
