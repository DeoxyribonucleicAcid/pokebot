import logging
import time

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
from Entities import Message
from MessageBuilders import DuelMessageBuilder


def delete_messages_by_type(bot, chat_id, type):
    player = DBAccessor.get_player(chat_id)
    if not (type in [getattr(Constants.MESSAGE_TYPES, attr) for attr in dir(Constants.MESSAGE_TYPES) if
                     not callable(getattr(Constants.MESSAGE_TYPES, attr)) and not attr.startswith("__")]):
        return False
    else:
        for i in player.get_messages(type):
            try:
                bot.delete_message(chat_id=player.chat_id, message_id=i._id)
            except telegram.error.BadRequest as e:
                logging.error(e)
            player.messages_to_delete.remove(i)
        update = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(_id=player.chat_id, update=update)


def append_message_to_player(chat_id, message_id, type):
    player = DBAccessor.get_player(chat_id)
    player.messages_to_delete.append(Message.Message(message_id, type, time.time()))
    DBAccessor.update_player(chat_id, DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete))


def reset_states(bot, chat_id: int):
    DBAccessor.update_player(_id=chat_id,
                             update=DBAccessor.get_update_query_player(nc_msg_state=Constants.NC_MSG_States.INFO))
    bot.send_message(chat_id=chat_id, text='States have been reset')


def build_choose_friend_message(bot, chat_id, mode: Constants.CHOOSE_FRIEND_MODE):
    player = DBAccessor.get_player(chat_id)
    text_no_friends_base = 'Sadly, you got no friends :( Add some with their usernames using /addfriend.'
    if mode is Constants.CHOOSE_FRIEND_MODE.TRADE:
        type = Constants.MESSAGE_TYPES.TRADE_FRIENDLIST_MSG
        text_no_friends = 'You con only trade with friends.' + text_no_friends_base
        callback_build_function = Constants.CALLBACK.FRIEND_TRADE
        text_heading = 'Choose one of your friends to trade with:'
    elif mode is Constants.CHOOSE_FRIEND_MODE.DUEL:
        type = Constants.MESSAGE_TYPES.DUEL_FRIENDLIST_MSG
        text_no_friends = 'You con only challenge your friends.' + text_no_friends_base
        callback_build_function = Constants.CALLBACK.FRIEND_DUEL
        text_heading = 'Challenge one of your friends:'

    else:
        bot.send_message(chat_id=player.chat_id, text='Invalid friendlist mode, blame the devs!')
        raise ValueError('Invalid CHOOSE_FRIEND_MODE given!')

    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='You are not registered.\nType /username or /register to register.')
        return
    elif player.friendlist is None or len(player.friendlist) is 0:
        keys = [[InlineKeyboardButton(text='Add friend',
                                      callback_data=Constants.CALLBACK.FRIEND_ADD)]]
        reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
        bot.send_message(chat_id=player.chat_id,
                         text=text_no_friends,
                         reply_markup=reply_keyboard)
        return

    delete_messages_by_type(bot, player.chat_id, type=type)
    keys = []
    for friend_id in player.friendlist:
        friend = DBAccessor.get_player(friend_id)
        if friend is None:
            continue
        else:
            keys.append([InlineKeyboardButton(text=DBAccessor.get_player(friend_id).username,
                                              callback_data=callback_build_function(friend_id))], )
    reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
    msg = bot.send_message(chat_id=player.chat_id, text=text_heading,
                           reply_markup=reply_keyboard)

    player.messages_to_delete.append(Message.Message(msg.message_id, _title=type, _time_sent=time.time()))
    query = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=query)


def clear_duels(bot, update):
    player = DBAccessor.get_player(update.message.chat_id)
    for duel_id in player.duels:
        DuelMessageBuilder.abort_duel(bot=bot, chat_id=player.chat_id, duel_id=duel_id)
    bot.send_message(chat_id=player.chat_id, text='Aborted all your duels')
