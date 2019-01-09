import Constants
import DBAccessor


def delete_messages_by_type(bot, player, type):
    if not (type is Constants.ENCOUNTER_MSG or Constants.BAG_MSG or Constants.MENU_MSG or Constants.MENU_INFO_MSG):
        return False
    else:
        for i in player.messages_to_delete:
            # duplicate in Player.Player.delete_message() but more efficient
            if i._title == type:
                bot.delete_message(chat_id=player.chat_id, message_id=i._id)
                player.messages_to_delete.remove(i)

        update = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
        DBAccessor.update_player(_id=player.chat_id, update=update)
