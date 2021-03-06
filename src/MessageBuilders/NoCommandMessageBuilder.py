import Constants
import DBAccessor
from MessageBuilders import PokeInfoMessageBuilder, FriendlistMessageBuilder, MessageHelper, PokeDisplayBuilder


def build_nc_msg(bot, update):
    player = DBAccessor.get_player(update.message.chat_id)
    if player is None or player.nc_msg_state == Constants.NC_MSG_States.INFO.value:
        PokeInfoMessageBuilder.build_msg_info(bot=bot, update=update)
    elif player.nc_msg_state == Constants.NC_MSG_States.USERNAME.value:
        FriendlistMessageBuilder.search_friend_in_players(bot=bot, update=update)
    elif player.nc_msg_state == Constants.NC_MSG_States.DISPLAY_EDIT_NAME.value:
        PokeDisplayBuilder.poke_change_name(bot=bot, chat_id=update.message.chat_id, new_name=update.message.text)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Invalid Message State, Please Try Again!')
        MessageHelper.reset_states(bot, update.message.chat_id)
