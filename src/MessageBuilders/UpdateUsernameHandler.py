import DBAccessor
import Player


def update_username(bot, update):
    player = DBAccessor.get_player(update.message.chat_id)
    if update.message.from_user.username is None:
        bot.send_message(chat_id=update.message.chat_id, text="You have not set a telegram username. Do so to proceed.")
    elif player is None:
        DBAccessor.insert_new_player(Player.Player(update.message.chat_id, username=update.message.from_user.username))
        bot.send_message(chat_id=update.message.chat_id, text="You have been registered")
    elif player.username is not None and player.username == update.message.from_user.username:
        bot.send_message(chat_id=player.chat_id, text='Your username is already registered.')
    else:
        query = DBAccessor.get_update_query(username=update.message.from_user.username)
        DBAccessor.update_player(_id=player.chat_id, update=query)
        bot.send_message(chat_id=update.message.chat_id, text="Your username has been updated!")
