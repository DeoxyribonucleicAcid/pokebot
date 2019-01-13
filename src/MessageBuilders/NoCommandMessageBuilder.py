import Constants
import DBAccessor
from MessageBuilders import PokeInfoMessageBuilder, FriendlistMessageBuilder, MessageHelper


def build_nc_msg(bot, update):
    player = DBAccessor.get_player(update.message.chat_id)
    if player is None or player.nc_msg_state == Constants.NC_MSG_States.INFO.value:
        PokeInfoMessageBuilder.build_msg_info(bot=bot, update=update)
    elif player.nc_msg_state == Constants.NC_MSG_States.USERNAME.value:
        FriendlistMessageBuilder.search_friend_in_players(bot=bot, update=update)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Invalid Message State')
        MessageHelper.reset_states(bot, update)
