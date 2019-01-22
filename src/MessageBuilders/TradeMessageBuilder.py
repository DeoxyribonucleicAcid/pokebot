import logging
import time
from io import BytesIO

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

import Constants
import DBAccessor
import Message
import Player
import Pokemon
from MessageBuilders import PokeDisplayBuilder


def build_msg_trade(bot, chat_id, player_id=None):
    if player_id is None:
        build_choose_friend_message(bot=bot, chat_id=chat_id)
        return
    else:
        player = DBAccessor.get_player(chat_id)
        friend = DBAccessor.get_player(player_id)
        keys = [[
            InlineKeyboardButton(text='Yes', callback_data='trade-invite-confirm-' + str(player.chat_id)),
            InlineKeyboardButton(text='No', callback_data='trade-invite-deny-' + str(player.chat_id))
        ]]
        replyKeyboard = InlineKeyboardMarkup(inline_keyboard=keys)
        invite_msg = bot.send_message(chat_id=friend.chat_id,
                                      text='Your friend ' + str(
                                          player.username) + ' wants to trade. Are you interested?',
                                      reply_markup=replyKeyboard)
        friend.messages_to_delete.append(
            Message.Message(_id=invite_msg.message_id, _title=Constants.TRADE_INVITE_MSG, _time_sent=time.time()))

        bot.send_message(chat_id=chat_id,
                         text='Choose your Pokemon to trade:')

        bot.send_message(chat_id=chat_id,
                         text='Trading Pok\xe9mon is currently under development. Please try again later.')


def trade_callback_handler(bot, update):
    data = update.callback_query.data
    player = DBAccessor.get_player(_id=update.effective_message.chat_id)
    if data.startswith('trade-invite-confirm-'):
        init_player = DBAccessor.get_player(int(data[21:]))
        for i in player.get_messages(Constants.TRADE_INVITE_MSG):
            try:
                bot.delete_message(chat_id=player.chat_id, message_id=i._id)
            except telegram.error.BadRequest as e:
                logging.error(e)

    elif data.startswith('trade-invite-deny-'):
        init_player = DBAccessor.get_player(int(data[18:]))
        for i in player.get_messages(Constants.TRADE_INVITE_MSG):
            try:
                bot.delete_message(chat_id=player.chat_id, message_id=i._id)
            except telegram.error.BadRequest as e:
                logging.error(e)
        bot.send_message(chat_id=player.chat_id,
                         text='Trade cancelled')
        bot.send_message(chat_id=init_player.chat_id,
                         text='Your friend is currently not interested in trading cute Pok\xe9mon.')
    elif data.startswith('trade-choose-'):
        if data.startswith('trade-choose-page-'):
            page_num = int(data[18:])
            build_trade_display(bot=bot, player=player, page_number=page_num)
        elif data.startswith('trade-choose-pokemon'):
            pass
    elif data.startswith('trade-inspect-pokemon-'):
        poke_id = int(data[22:])
        PokeDisplayBuilder.build_poke_display(bot=bot, chat_id=player.chat_id,
                                              pokemon=player.get_pokemon(pokemon_id=poke_id))


def build_choose_friend_message(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='You are not registered.\nType /username or /register to register.')
        return
    elif player.friendlist is None or len(player.friendlist) is 0:
        keys = [[InlineKeyboardButton(text='Add friend',
                                      callback_data='friend-add')]]
        replyKeyboard = InlineKeyboardMarkup(inline_keyboard=keys)
        bot.send_message(chat_id=chat_id,
                         text='You con only trade with friends. Sadly, you got no friends :('
                              ' Add some with their usernames using /addfriend.',
                         reply_markup=replyKeyboard)
        return
    for i in player.get_messages(Constants.TRADE_FRIENDLIST_MSG):
        try:
            bot.delete_message(chat_id=player.chat_id, message_id=i._id)
        except telegram.error.BadRequest as e:
            logging.error(e)
    keys = []
    for friend_id in player.friendlist:
        friend = DBAccessor.get_player(friend_id)
        if friend is None:
            continue
        else:
            keys.append([InlineKeyboardButton(text=DBAccessor.get_player(friend_id).username,
                                              callback_data='friend-trade-' + str(friend_id))], )
    replyKeyboard = InlineKeyboardMarkup(inline_keyboard=keys)
    msg = bot.send_message(chat_id=player.chat_id, text='Choose one of your friends to trade with:',
                           reply_markup=replyKeyboard)

    player.messages_to_delete.append(
        Message.Message(msg.message_id, _title=Constants.TRADE_FRIENDLIST_MSG, _time_sent=time.time()))
    query = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=query)


def build_trade_display(bot, player: Player.Player, page_number):
    pokecount = 10

    pokemon_sprite_list = []
    caption = '*Choose your Pokemon to trade:*\n'
    if len(player.pokemon) > pokecount:
        caption += '*Page Number: *' + str(page_number) + '\n'
    keys = []
    list_start = pokecount * page_number
    list_end = pokecount * (page_number + 1) if len(player.pokemon) >= pokecount * (page_number + 1) else len(
        player.pokemon)
    page_list = player.pokemon[list_start:list_end]
    for pokemon in page_list:
        keys.append([InlineKeyboardButton(text=pokemon.name,
                                          callback_data='trade-inspect-pokemon-' + str(pokemon._id))])
        pokemon_sprite_list.append(pokemon.sprites['front'])
    image = Pokemon.build_pokemon_bag_image(pokemon_sprite_list)

    for i in player.get_messages(Constants.TRADE_CHOOSE_MSG):
        try:
            bot.delete_message(chat_id=player.chat_id, message_id=i._id)
        except telegram.error.BadRequest as e:
            logging.error(e)
    if image is not None:
        bio = BytesIO()
        bio.name = 'image_bag_' + str(player.chat_id) + '.png'
        image.save(bio, 'PNG')
        bio.seek(0)

        keys.append([])
        if page_number > 0:
            keys[-1].append(InlineKeyboardButton(text='\u2190',
                                                 callback_data='trade-choose-page-' + str(page_number - 1)))
        if len(player.pokemon) > list_end:
            keys[-1].append(InlineKeyboardButton(text='\u2192',
                                                 callback_data='trade-choose-page-' + str(page_number + 1)))

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)

        msg = bot.send_photo(chat_id=player.chat_id,
                             photo=bio,
                             reply_markup=reply_markup,
                             caption=caption, parse_mode=ParseMode.MARKDOWN)
    else:
        msg = bot.send_message(chat_id=player.chat_id,
                               text='Your bag is empty, catch some pokemon!')
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.TRADE_CHOOSE_MSG, _time_sent=time.time()))
    update = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=update)
