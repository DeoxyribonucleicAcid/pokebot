import logging
import time

import telegram
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
from Entities import Message
from MessageBuilders import TradeMessageBuilder


def build_friendlist_message(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='You are not registered.\nType /username or /register to register.')
        return
    elif player.friendlist is None or len(player.friendlist) is 0:
        keys = [[InlineKeyboardButton(text='Add friend',
                                      callback_data=Constants.CALLBACK.FRIEND_ADD)]]
        reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
        bot.send_message(chat_id=chat_id,
                         text='You got no friends :( Add some with their usernames using /addfriend.',
                         reply_markup=reply_keyboard)
        return
    for i in player.get_messages(Constants.FRIENDLIST_MSG):
        try:
            bot.delete_message(chat_id=player.chat_id, message_id=i._id)
        except telegram.error.BadRequest as e:
            logging.error(e)
    x_mark = emojize(":x:", use_aliases=True)
    keys = []
    for friend_id in player.friendlist:
        friend = DBAccessor.get_player(friend_id)
        if friend is None:
            continue
        else:
            keys.append([InlineKeyboardButton(text=DBAccessor.get_player(friend_id).username,
                                              callback_data=Constants.CALLBACK.FRIEND_NAME),
                         InlineKeyboardButton(text='Trade',
                                              callback_data=Constants.CALLBACK.FRIEND_TRADE(friend_id)),
                         InlineKeyboardButton(text='Duel',
                                              callback_data=Constants.CALLBACK.FRIEND_DUEL(friend_id)),
                         InlineKeyboardButton(text=x_mark,
                                              callback_data=Constants.CALLBACK.FRIEND_DELETE(friend_id))], )
    keys.append([InlineKeyboardButton(text='Add friend', callback_data=Constants.CALLBACK.FRIEND_ADD)])
    reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
    msg = bot.send_message(chat_id=player.chat_id, text='Your friends:', reply_markup=reply_keyboard)

    player.messages_to_delete.append(
        Message.Message(msg.message_id, _title=Constants.FRIENDLIST_MSG, _time_sent=time.time()))
    query = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=query)


def delete_friend(bot, chat_id, friend_to_be_deleted):
    keys = [
        [InlineKeyboardButton(text='Sure, i dont like him/her anyway',
                              callback_data=Constants.CALLBACK.FRIEND_CONFIRM_DELETE_YES(friend_to_be_deleted))],
        [InlineKeyboardButton(text='No, just joking',
                              callback_data=Constants.CALLBACK.FRIEND_CONFIRM_DELETE_NO)]
    ]
    reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
    msg = bot.send_message(chat_id=chat_id, text='You dont really want to loose a friend? o.o',
                           reply_markup=reply_keyboard)
    player = DBAccessor.get_player(chat_id)
    player.messages_to_delete.append(
        Message.Message(msg.message_id, _title=Constants.FRIEND_CONFIRM_DELETE_MSG, _time_sent=time.time()))
    query = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=query)


def delete_friend_confirm(bot, chat_id, friend_to_be_deleted):
    friend_to_be_deleted = int(friend_to_be_deleted)
    player = DBAccessor.get_player(chat_id)
    for i in player.get_messages(Constants.FRIEND_CONFIRM_DELETE_MSG):
        try:
            bot.delete_message(chat_id=player.chat_id, message_id=i._id)
        except telegram.error.BadRequest as e:
            logging.error(e)
    if friend_to_be_deleted in player.friendlist:
        player.friendlist.remove(friend_to_be_deleted)
        DBAccessor.update_player(player.chat_id, DBAccessor.get_update_query(friendlist=player.friendlist))
        bot.send_message(chat_id=chat_id, text='I wont tell him/her that you dont like him/her anymore.')
    else:
        bot.send_message(chat_id=chat_id, text='I couldn\'t find him/her in your list.')


def delete_friend_deny(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    for i in player.get_messages(Constants.FRIEND_CONFIRM_DELETE_MSG):
        try:
            bot.delete_message(chat_id=player.chat_id, message_id=i._id)
        except telegram.error.BadRequest as e:
            logging.error(e)
    bot.send_message(chat_id=chat_id, text='Friendship4ever <3')


def friend_callback_handler(bot, update):
    data = update.callback_query.data
    if data.startswith('friend-name-'):
        friend_id = int(data[12:])
    elif data.startswith('friend-trade-'):
        friend_id = int(data[13:])
        player = DBAccessor.get_player(update.effective_message.chat_id)
        for i in player.get_messages(Constants.TRADE_FRIENDLIST_MSG):
            try:
                bot.delete_message(chat_id=player.chat_id, message_id=i._id)
            except telegram.error.BadRequest as e:
                logging.error(e)
        TradeMessageBuilder.build_msg_trade(bot=bot, chat_id=update.effective_message.chat_id, player_id=friend_id)
    elif data.startswith('friend-duel-'):
        friend_id = int(data[12:])
        # TODO
    elif data.startswith('friend-delete-'):
        friend_id = int(data[14:])
        delete_friend(bot=bot, chat_id=update.effective_message.chat_id, friend_to_be_deleted=friend_id)
    elif data.startswith('friend-confirm-delete-yes-'):
        friend_id = int(data[26:])
        delete_friend_confirm(bot=bot, chat_id=update.effective_message.chat_id, friend_to_be_deleted=friend_id)
    elif data == 'friend-confirm-delete-no':
        delete_friend_deny(bot=bot, chat_id=update.effective_message.chat_id)
    elif data == 'friend-add':
        build_add_friend_initial_message(bot, update.effective_message.chat_id)
    elif data.startswith('friend-add-notify-yes-'):
        new_friend_name = data[22:]
        add_friend_callback(bot=bot, chat_id=update.effective_message.chat_id, username=new_friend_name)
    elif data == 'friend-add-notify-no':
        add_friend_no_callback(bot=bot, chat_id=update.effective_message.chat_id)


def build_add_friend_initial_message(bot, chat_id):
    player = DBAccessor.get_player(_id=chat_id)
    if player.username is None:
        bot.send_message(chat_id=chat_id, text='Please set a telegram username, this way I will be able to identify '
                                               'you :)\nIf you already did so and have not told me yet, use /username')
        return None
    else:
        query = DBAccessor.get_update_query(nc_msg_state=Constants.NC_MSG_States.USERNAME)
        DBAccessor.update_player(_id=chat_id, update=query)
        bot.send_message(chat_id=chat_id, text='Send me the username of your friend. Use /exit to stop.')


def search_friend_in_players(bot, update):
    username = update.message.text
    player = DBAccessor.get_player(update.message.chat_id)
    if username.startswith('@'):
        username = username[1:]
    username = username.lower()
    new_friend = DBAccessor.get_player_by_name(username=username)
    if new_friend is None:
        bot.send_message(chat_id=player.chat_id,
                         text='I dont know him/her. Maybe you should introduce me to him/her :)')
        query = DBAccessor.get_update_query(nc_msg_state=Constants.NC_MSG_States.INFO)
        DBAccessor.update_player(_id=update.message.chat_id, update=query)
        return None
    elif new_friend.chat_id in player.friendlist:
        bot.send_message(chat_id=player.chat_id, text='You two are already friends')
        query = DBAccessor.get_update_query(nc_msg_state=Constants.NC_MSG_States.INFO)
        DBAccessor.update_player(_id=update.message.chat_id, update=query)
        return None
    else:
        player.friendlist.append(new_friend.chat_id)
        query = DBAccessor.get_update_query(friendlist=player.friendlist,
                                            nc_msg_state=Constants.NC_MSG_States.INFO)
        DBAccessor.update_player(_id=update.message.chat_id, update=query)
        bot.send_message(chat_id=player.chat_id, text='I added and notified him/her.')
        if player.chat_id not in new_friend.friendlist:
            keys = [[InlineKeyboardButton(text='Yes, sure',
                                          callback_data=Constants.CALLBACK.FRIEND_ADD_NOTIFY_YES(player.username)),
                     InlineKeyboardButton(text='No, I don\'t know him/her',
                                          callback_data=Constants.CALLBACK.FRIEND_ADD_NOTIFY_NO)]]
            reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
            bot.send_message(chat_id=new_friend.chat_id,
                             text=player.username + ' just added you to his/her friendlist, do you want to add him/her too?',
                             reply_markup=reply_keyboard)
        else:
            bot.send_message(chat_id=new_friend.chat_id,
                             text=player.username + ' just added you to his/her friendlist, nice, isn\'t it?')


def add_friend_callback(bot, chat_id, username):
    new_friend = DBAccessor.get_player_by_name(username=username)
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id, text='Something went wrong, I cant find you.')
    elif new_friend is None:
        bot.send_message(chat_id=chat_id, text='Something went wrong, I cant find your new friend.')
    else:
        player.friendlist.append(new_friend.chat_id)
        query = DBAccessor.get_update_query(friendlist=player.friendlist)
        DBAccessor.update_player(_id=player.chat_id, update=query)
        bot.send_message(chat_id=chat_id, text='I added him/her.')


def add_friend_no_callback(bot, chat_id):
    bot.send_message(chat_id=chat_id, text='Ok, nevermind.')
