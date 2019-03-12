import time

import Constants
import DBAccessor
from Entities import Player, Message


def build_catch_message(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        player = Player.Player(chat_id, encounters=True)
        msg = bot.send_message(chat_id=chat_id, text='I will poke you, if you stumble over a pokemon.')
        player.messages_to_delete.append(
            Message.Message(_id=msg.message_id, _title=Constants.MENU_INFO_MSG, _time_sent=time.time()))
        DBAccessor.insert_new_player(player=player)
    elif not player.encounters:
        msg = bot.send_message(chat_id=chat_id, text='You are on the watch again. Type /nocatch to ignore encounters.')
        player.messages_to_delete.append(
            Message.Message(_id=msg.message_id, _title=Constants.MENU_INFO_MSG, _time_sent=time.time()))
        update = DBAccessor.get_update_query_player(encounters=True, messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(player.chat_id, update)
    elif player.encounters:
        msg = bot.send_message(chat_id=chat_id, text='I will notify as promised. Type /nocatch to ignore encounters.')
        player.messages_to_delete.append(
            Message.Message(_id=msg.message_id, _title=Constants.MENU_INFO_MSG, _time_sent=time.time()))
        update = DBAccessor.get_update_query_player(encounters=True, messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(player.chat_id, update)
    else:
        raise ('Data Error: Corrupt Player')


def build_no_catch_message(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        msg = bot.send_message(chat_id=chat_id, text='You\'re not on the list. Type /catch to get encounters.')
    elif not player.encounters:
        msg = bot.send_message(chat_id=chat_id, text='You\'re not on the list. Type /catch to get encounters.')
        player.messages_to_delete.append(
            Message.Message(_id=msg.message_id, _title=Constants.MENU_INFO_MSG, _time_sent=time.time()))
        update = DBAccessor.get_update_query_player(encounters=False, messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(player.chat_id, update)
    elif player.encounters:
        msg = bot.send_message(chat_id=chat_id, text='You\'re no longer on the list. Type /catch to get encounters.')
        player.messages_to_delete.append(
            Message.Message(_id=msg.message_id, _title=Constants.MENU_INFO_MSG, _time_sent=time.time()))
        update = DBAccessor.get_update_query_player(encounters=False, messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(player.chat_id, update)
    else:
        raise ('Data Error: Corrupt Player')
