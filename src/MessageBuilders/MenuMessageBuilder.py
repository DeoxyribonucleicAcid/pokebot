import time
from typing import List

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
                                              type=Constants.MESSAGE_TYPES.MENU_MSG)
    else:
        msg = bot.send_message(chat_id=update.message.chat_id,
                               text='I do not know you yet. To be recognized next time, type /catch\n'
                                    'This will enable encounters as well.')
        return

    text, reply_markup = build_msg_menu(player.chat_id, player.encounters if player is not None else False,
                                        trade=player.trade, duels=player.duels)
    msg = bot.send_message(chat_id=update.message.chat_id, text=text,
                           reply_markup=reply_markup)
    if player is None:
        new_player = Player.Player(update.message.chat_id, messages_to_delete=[
            Message.Message(_id=msg.message_id, _title=Constants.MESSAGE_TYPES.MENU_MSG, _time_sent=time.time())],
                                   encounters=False)
        DBAccessor.insert_new_player(new_player)
    else:
        MessageHelper.append_message_to_player(player.chat_id, msg.message_id, Constants.MESSAGE_TYPES.MENU_MSG)


def update_menu_message(bot, chat_id, msg_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        return False
    # msg_id = len(player.messages_to_delete) - 1 - next(
    #    (i for i, x in enumerate(reversed(player.messages_to_delete)) if x._title == Constants.MESSAGE_TYPES.MENU_MSG),
    #     len(player.messages_to_delete))
    text, reply_markup = build_msg_menu(player.chat_id, encounters=player.encounters, trade=player.trade,
                                        duels=player.duels)
    try:
        bot.edit_message_text(chat_id=chat_id, text=text, message_id=msg_id,
                              reply_markup=reply_markup)
    except telegram.error.BadRequest as e:
        if e.message != 'Message is not modified':
            raise e


def build_msg_menu(chat_id, encounters: bool, trade: Trade, duels: List[int]):
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
            text='View trade with {}'.format(DBAccessor.get_player(int(trade.partner_id)).username),
            callback_data=Constants.CALLBACK.TRADE_STATUS)])
    if duels is not None:
        for duel_id in duels:
            duel = DBAccessor.get_duel_by_id(int(duel_id))
            if duel is None:
                player = DBAccessor.get_player(chat_id)
                player.duels.remove(duel_id)
                DBAccessor.update_player(chat_id, DBAccessor.get_update_query_player(duels=player.duels))
                continue
            friend = DBAccessor.get_player(int(duel.get_counterpart_by_id(chat_id).player_id))
            if friend is None: continue
            keys.append([InlineKeyboardButton(
                text='View duel with {}'.format(friend.username),
                callback_data=Constants.CALLBACK.DUEL_ACTIVE(duel.event_id))])
    text = 'Menu:'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    return text, reply_markup


def send_settings_menu(bot, update):
    player = DBAccessor.get_player(update.message.chat_id)
    if player is not None:
        MessageHelper.delete_messages_by_type(bot=bot, chat_id=update.message.chat_id,
                                              type=Constants.MESSAGE_TYPES.SETTINGS_MSG)
    else:
        msg = bot.send_message(chat_id=update.message.chat_id,
                               text='I do not know you yet. To be recognized next time, update your /username or type /catch\n'
                                    'Latter will enable encounters as well.')
        return
    text, reply_markup = build_msg_settings_menu()
    msg = bot.send_message(chat_id=update.message.chat_id, text=text,
                           reply_markup=reply_markup)
    MessageHelper.append_message_to_player(player.chat_id, msg.message_id, Constants.MESSAGE_TYPES.SETTINGS_MSG)


def build_msg_settings_menu():
    keys = [[InlineKeyboardButton(text='Update Username', callback_data=Constants.CALLBACK.SETTINGS_USERNAME)],
            [InlineKeyboardButton(text='Change Language', callback_data=Constants.CALLBACK.SETTINGS_LANG)]]
    text = 'Settings:'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    return text, reply_markup


def toggle_encounter(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id,
                                          type=Constants.MESSAGE_TYPES.MENU_INFO_MSG)
    if player.encounters:
        ToggleCatchMessageBuilder.build_no_catch_message(bot=bot, chat_id=chat_id)
    else:
        ToggleCatchMessageBuilder.build_catch_message(bot=bot, chat_id=chat_id)
    if player.get_messages(Constants.MESSAGE_TYPES.MENU_MSG) is not None or len(
            player.get_messages(Constants.MESSAGE_TYPES.MENU_MSG)) > 0:
        menu_msg_id = player.get_messages(Constants.MESSAGE_TYPES.MENU_MSG)[-1]._id
        update_menu_message(bot, chat_id, menu_msg_id)
