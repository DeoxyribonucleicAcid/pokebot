from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
from MessageBuilders import MessageHelper
from src.EichState import EichState


def send_lang_menu(bot, chat_id):
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.LANG_MENU)
    keys = []
    for lang in EichState.string_dicts.keys():
        keys.append([InlineKeyboardButton(text=lang, callback_data=Constants.CALLBACK.CHANGE_LANGUAGE(lang))])
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    msg = bot.send_message(chat_id=chat_id, text=Texter.get_text(player, 'choose_language_msg'), reply_markup=reply_markup)
    MessageHelper.append_message_to_player(chat_id, msg.message_id, Constants.MESSAGE_TYPES.LANG_MENU)


def change_lang(bot, chat_id, chosen_lang):
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.LANG_MENU)
    player = DBAccessor.get_player(chat_id)
    query = DBAccessor.get_update_query_player(lang=chosen_lang)
    DBAccessor.update_player(_id=player.chat_id, update=query)
    bot.send_message(chat_id=chat_id, text=Texter.get_text(player, 'language_updated_msg'))
