import time
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
from Entities import Message, Pokemon
from Entities.Trade import Trade
from MessageBuilders import PokeDisplayBuilder, BagMessageBuilder, MessageHelper


def build_msg_trade(bot, chat_id, player_id=None):
    if player_id is None:
        build_choose_friend_message(bot=bot, chat_id=chat_id)
        return
    else:
        player = DBAccessor.get_player(chat_id)
        friend = DBAccessor.get_player(int(player_id))
        if player.trade is not None:
            bot.send_message(chat_id=player.chat_id,
                             text='You are currently trading with {}'.format(
                                 DBAccessor.get_player(int(player.trade.partner_id)).username))
            return
        if friend.trade is not None:
            bot.send_message(chat_id=player.chat_id,
                             text='Your friend is currently trading with somebody else')
            return
        keys = [[
            InlineKeyboardButton(text='Yes', callback_data=Constants.CALLBACK.TRADE_IVITE_CONFIRM(player.chat_id)),
            InlineKeyboardButton(text='No', callback_data=Constants.CALLBACK.TRADE_INVITE_DENY(player.chat_id))
        ]]
        reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
        invite_msg = bot.send_message(chat_id=player_id,
                                      text='Your friend ' + str(
                                          player.username) + ' wants to trade. Are you interested?',
                                      reply_markup=reply_keyboard)
        friend.messages_to_delete.append(
            Message.Message(_id=invite_msg.message_id, _title=Constants.TRADE_INVITE_MSG, _time_sent=time.time()))
        query_friend = DBAccessor.get_update_query(chat_id=friend.chat_id, messages_to_delete=friend.messages_to_delete)
        DBAccessor.update_player(_id=friend.chat_id, update=query_friend)

        player.trade = Trade(partner_id=friend.chat_id)
        query_player = DBAccessor.get_update_query(chat_id=player.chat_id, trade=player.trade)
        DBAccessor.update_player(_id=player.chat_id, update=query_player)

        msg = bot.send_message(chat_id=chat_id, text='Choose your Pokemon to trade:')
        BagMessageBuilder.build_msg_bag(bot=bot, chat_id=player.chat_id, page_number=0, trade_mode=True)


def trade_invite_confirm(bot, chat_id, init_player_id):
    player = DBAccessor.get_player(chat_id)
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.TRADE_INVITE_MSG)
    player.trade = Trade(partner_id=init_player_id)
    query_player = DBAccessor.get_update_query(chat_id=player.chat_id, trade=player.trade)
    DBAccessor.update_player(_id=player.chat_id, update=query_player)
    BagMessageBuilder.build_msg_bag(bot=bot, chat_id=player.chat_id, page_number=0, trade_mode=True)


def trade_invite_deny(bot, chat_id, init_player_id):
    player = DBAccessor.get_player(chat_id)
    init_player = DBAccessor.get_player(int(init_player_id))
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.TRADE_INVITE_MSG)

    bot.send_message(chat_id=player.chat_id,
                     text='Trade cancelled')
    bot.send_message(chat_id=init_player.chat_id,
                     text='Your friend is currently not interested in trading cute Pok\xe9mon.')


def trade_callback_handler(bot, update):
    data = update.callback_query.data
    player = DBAccessor.get_player(_id=update.effective_message.chat_id)
    if data.startswith('trade-invite-confirm-'):
        init_player_id = int(data[21:])
        trade_invite_confirm(bot=bot, chat_id=update.effective_message.chat_id, init_player_id=init_player_id)
    elif data.startswith('trade-invite-deny-'):
        init_player_id = int(data[18:])
        trade_invite_deny(bot=bot, chat_id=update.effective_message.chat_id, init_player_id=init_player_id)
    elif data.startswith('trade-choose-'):
        if data.startswith('trade-choose-page-'):
            page_num = int(data[18:])
            BagMessageBuilder.build_msg_bag(bot=bot, chat_id=player.chat_id, page_number=page_num, trade_mode=True)
        elif data.startswith('trade-choose-pokemon-'):
            # TODO
            pass
    elif data.startswith('trade-inspect-pokemon-'):
        page_num = int(data[22:].split('-')[0])
        poke_id = int(data[22:].split('-')[1])
        PokeDisplayBuilder.build_poke_display(bot=bot, chat_id=player.chat_id, poke_id=poke_id,
                                              page_num=page_num, trade_mode=True)


def build_choose_friend_message(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='You are not registered.\nType /username or /register to register.')
        return
    elif player.friendlist is None or len(player.friendlist) is 0:
        keys = [[InlineKeyboardButton(text='Add friend',
                                      callback_data=Constants.CALLBACK.FRIEND_ADD)]]
        reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
        bot.send_message(chat_id=chat_id,
                         text='You con only trade with friends. Sadly, you got no friends :('
                              ' Add some with their usernames using /addfriend.',
                         reply_markup=reply_keyboard)
        return
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.TRADE_FRIENDLIST_MSG)
    keys = []
    for friend_id in player.friendlist:
        friend = DBAccessor.get_player(friend_id)
        if friend is None:
            continue
        else:
            keys.append([InlineKeyboardButton(text=DBAccessor.get_player(friend_id).username,
                                              callback_data=Constants.CALLBACK.FRIEND_TRADE(friend_id))], )
    reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
    msg = bot.send_message(chat_id=player.chat_id, text='Choose one of your friends to trade with:',
                           reply_markup=reply_keyboard)

    player.messages_to_delete.append(
        Message.Message(msg.message_id, _title=Constants.TRADE_FRIENDLIST_MSG, _time_sent=time.time()))
    query = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=query)


def trade_pokemon_chosen(bot, chat_id, pokemon_id):
    pokemon_id = int(pokemon_id)
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.POKE_DISPLAY_MSG)
    player = DBAccessor.get_player(_id=chat_id)
    if player.trade is not None:
        player.trade.pokemon = player.remove_pokemon(pokemon_id)
    else:
        bot.send_message(chat_id=chat_id, text='Your trade exceeded.')
        return
    if player.trade.pokemon is None:
        bot.send_message(chat_id=chat_id, text='Pokemon not found, im getting old :/')
        return
    query = DBAccessor.get_update_query(chat_id=chat_id, pokemon=player.pokemon, trade=player.trade)
    DBAccessor.update_player(_id=chat_id, update=query)
    bot.send_message(chat_id=chat_id, text='You chose {} for this trade'.format(player.trade.pokemon.name))
    partner = DBAccessor.get_player(int(player.trade.partner_id))

    if partner.trade is not None:
        if partner.trade.pokemon is not None:
            image_player = Pokemon.build_pokemon_trade_image(player.trade.pokemon.sprites['back'],
                                                             partner.trade.pokemon.sprites['front'])
            bio_player = BytesIO()
            bio_player.name = 'trade_img_' + str(player.chat_id) + '.png'
            image_player.save(bio_player, 'PNG')
            bio_player.seek(0)

            image_partner = Pokemon.build_pokemon_trade_image(partner.trade.pokemon.sprites['back'],
                                                              player.trade.pokemon.sprites['front'])
            bio_partner = BytesIO()
            bio_partner.name = 'trade_img_' + str(partner.chat_id) + '.png'
            image_partner.save(bio_partner, 'PNG')
            bio_partner.seek(0)
            keys = [[InlineKeyboardButton(text='Yes', callback_data=Constants.CALLBACK.TRADE_ACCEPT),
                     InlineKeyboardButton(text='Nope', callback_data=Constants.CALLBACK.TRADE_ABORT)]]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)

            msg = bot.send_photo(chat_id=player.chat_id, text='Both of you have chosen. Do you accept this trade?',
                                 photo=bio_player, reply_markup=reply_markup)
            msg = bot.send_photo(chat_id=partner.chat_id, text='Both of you have chosen. Do you accept this trade?',
                                 photo=bio_partner, reply_markup=reply_markup)
            return

    bot.send_message(chat_id=chat_id,
                     text='{} has not chosen yet. I will notify you when he/she is ready.'.format(partner.username))
    bot.send_message(chat_id=partner.chat_id,
                     text='Your trading partner has chosen {} to trade.'.format(player.trade.pokemon.name))


def trade_accept(bot, chat_id):
    player = DBAccessor.get_player(_id=chat_id)
    if player.trade is not None:
        partner = DBAccessor.get_player(player.trade.partner_id)
        if player.trade.accepted:
            bot.send_message(chat_id=chat_id,
                             text='You already accepted the trade. Awaiting {}\'s response'.format(partner.username))
            return
        if partner.trade.accepted:

            bot.send_message(chat_id=player.chat_id,
                             text='Welcome {}. {} will take good care of {}.'.format(partner.trade.pokemon.name,
                                                                                     partner.username,
                                                                                     player.trade.pokemon.name))
            bot.send_message(chat_id=partner.chat_id,
                             text='Welcome {}. {} will take good care of {}.'.format(player.trade.pokemon.name,
                                                                                     player.username,
                                                                                     partner.trade.pokemon.name))

            player.pokemon.append(partner.trade.pokemon)
            partner.pokemon.append(player.trade.pokemon)

            player.trade, partner.trade = None, None
            query_player = DBAccessor.get_update_query(chat_id=player.chat_id, trade=player.trade,
                                                       pokemon=player.pokemon)
            query_partner = DBAccessor.get_update_query(chat_id=partner.chat_id, trade=partner.trade,
                                                        pokemon=partner.pokemon)

            DBAccessor.update_player(_id=player.chat_id, update=query_player)
            DBAccessor.update_player(_id=partner.chat_id, update=query_partner)

            PokeDisplayBuilder.build_poke_display(bot=bot, chat_id=player.chat_id, trade_mode=False, page_num=0,
                                                  poke_id=player.pokemon[-1]._id)
            PokeDisplayBuilder.build_poke_display(bot=bot, chat_id=partner.chat_id, trade_mode=False, page_num=0,
                                                  poke_id=partner.pokemon[-1]._id)


        else:
            player.trade.accepted = True
            query_player = DBAccessor.get_update_query(chat_id=player.chat_id, trade=player.trade)
            DBAccessor.update_player(_id=player.chat_id, update=query_player)
            bot.send_message(chat_id=chat_id,
                             text='You accepted the trade. Awaiting {}\'s response'.format(partner.username))
    else:
        bot.send_message(chat_id=chat_id, text='Your trade exceeded somehow. Please blame the devs start a new one.')
        return


def trade_abort(bot, chat_id):
    player = DBAccessor.get_player(_id=chat_id)
    if player.trade is not None:
        partner = DBAccessor.get_player(player.trade.partner_id)
        bot.send_message(chat_id=partner.chat_id, text='{} has aborted the trade.'.format(player.username))
        bot.send_message(chat_id=partner.chat_id, text='The trade will be aborted.')
        partner.trade, player.trade = None, None
        query_player = DBAccessor.get_update_query(chat_id=player.chat_id, trade=player.trade)
        query_partner = DBAccessor.get_update_query(chat_id=partner.chat_id, trade=partner.trade)
        DBAccessor.update_player(_id=player.chat_id, update=query_player)
        DBAccessor.update_player(_id=partner.chat_id, update=query_partner)
    else:
        bot.send_message(chat_id=chat_id, text='Your trade exceeded anyway.')
        return
