import logging

import telegram

import Constants
import DBAccessor


def delete_messages_by_type(bot, chat_id, type):
    player = DBAccessor.get_player(chat_id)
    if not (type is
            Constants.ENCOUNTER_MSG or
            Constants.MENU_MSG or
            Constants.BAG_MSG or
            Constants.MENU_INFO_MSG or
            Constants.FRIENDLIST_MSG or
            Constants.FRIEND_CONFIRM_DELETE_MSG or
            Constants.TRADE_FRIENDLIST_MSG or
            Constants.TRADE_CHOOSE_MSG or
            Constants.TRADE_CONFIRM_MSG or
            Constants.TRADE_INVITE_MSG or
            Constants.POKE_DISPLAY_MSG):
        return False
    else:
        for i in player.get_messages(type):
            try:
                bot.delete_message(chat_id=player.chat_id, message_id=i._id)
            except telegram.error.BadRequest as e:
                logging.error(e)
            player.messages_to_delete.remove(i)
        update = DBAccessor.get_update_query(chat_id=chat_id, messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(_id=player.chat_id, update=update)


def reset_states(bot, update):
    DBAccessor.update_player(_id=update.message.chat_id,
                             update=DBAccessor.get_update_query(nc_msg_state=Constants.NC_MSG_States.INFO))
