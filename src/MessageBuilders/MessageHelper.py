import logging

import telegram

import Constants
import DBAccessor


def delete_messages_by_type(bot, chat_id, player, type):
    if not (type is Constants.ENCOUNTER_MSG or Constants.BAG_MSG or Constants.MENU_MSG or Constants.MENU_INFO_MSG):
        return False
    else:
        for i in player.messages_to_delete:
            # duplicate in Player.Player.delete_message() but more efficient
            if i._title == type:
                try:
                    bot.delete_message(chat_id=player.chat_id, message_id=i._id)
                except telegram.error.BadRequest as e:
                    logging.error(e)
                player.messages_to_delete.remove(i)

        update = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(_id=player.chat_id, update=update)


def reset_states(bot, update):
    DBAccessor.update_player(_id=update.message.chat_id,
                             update=DBAccessor.get_update_query(nc_msg_state=Constants.NC_MSG_States.INFO))
