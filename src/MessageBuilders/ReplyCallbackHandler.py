import logging

import telegram

import Constants
import DBAccessor
from MessageBuilders import BagMessageBuilder, TradeMessageBuilder, ToggleCatchMessageBuilder, ItemBagMessageBuilder, \
    MenuMessageBuilder, MessageHelper


def process_callback(bot, update):
    data = update.callback_query.data
    player = DBAccessor.get_player(update.effective_chat.id)
    if data.startswith('catch-'):
        option = int(data[6:])
        if option == player.pokemon_direction:
            bot.send_message(chat_id=player.chat_id, text='captured ' + player.catch_pokemon.name + '!')
            for i in player.get_messages(Constants.ENCOUNTER_MSG):
                try:
                    bot.delete_message(chat_id=player.chat_id, message_id=i._id)
                except telegram.error.BadRequest as e:
                    logging.error(e)
            # Reset Player's encounter
            player.pokemon.append(player.catch_pokemon)
            update = DBAccessor.get_update_query(pokemon=player.pokemon, in_encounter=False, pokemon_direction=None,
                                                 catch_message_id=None, catch_pokemon=None)
            DBAccessor.update_player(_id=player.chat_id, update=update)
    elif data.startswith('catchmenu-'):
        if data == 'menu-item':
            pass
        elif data == 'menu-escape':
            pass

    elif data.startswith('menu-'):
        if data == 'menu-bag':
            BagMessageBuilder.build_msg_bag(bot, update.effective_message.chat_id)
        elif data == 'menu-trade':
            TradeMessageBuilder.build_msg_trade(bot=bot, chat_id=update.effective_message.chat_id)
        elif data == 'menu-catch':
            MessageHelper.delete_messages_by_type(bot=bot, player=player, type=Constants.MENU_INFO_MSG)
            if player.encounters:
                ToggleCatchMessageBuilder.build_no_catch_message(bot=bot, chat_id=update.effective_message.chat_id)
            else:
                ToggleCatchMessageBuilder.build_catch_message(bot=bot, chat_id=update.effective_message.chat_id)
            MenuMessageBuilder.update_menu_message(bot, update.effective_message.chat_id, update.effective_message.message_id)
        elif data == 'menu-items':
            ItemBagMessageBuilder.build_msg_item_bag(bot=bot, chat_id=update.effective_message.chat_id)
    else:
        raise ValueError('Invalid callback data: ' + data)

