import time
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import Constants
import DBAccessor
from Entities import Message, Pokemon
from Entities.Trade import Trade
from MessageBuilders import PokeDisplayBuilder, BagMessageBuilder, MessageHelper, MenuMessageBuilder


def build_msg_trade(bot, chat_id, player_id=None):
    if player_id is None:
        MessageHelper.build_choose_friend_message(bot=bot, chat_id=chat_id, mode=Constants.CHOOSE_FRIEND_MODE.TRADE)
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
            Message.Message(_id=invite_msg.message_id, _title=Constants.MESSAGE_TYPES.TRADE_INVITE_MSG,
                            _time_sent=time.time()))
        query_friend = DBAccessor.get_update_query_player(messages_to_delete=friend.messages_to_delete)
        DBAccessor.update_player(_id=friend.chat_id, update=query_friend)

        player.trade = Trade(partner_id=friend.chat_id)
        query_player = DBAccessor.get_update_query_player(trade=player.trade)
        DBAccessor.update_player(_id=player.chat_id, update=query_player)

        msg = bot.send_message(chat_id=chat_id, text='Choose your Pokemon to trade:')
        BagMessageBuilder.build_msg_bag(bot=bot, chat_id=player.chat_id, page_number=0, trade_mode=True)


def trade_invite_confirm(bot, chat_id, init_player_id):
    player = DBAccessor.get_player(chat_id)
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.TRADE_INVITE_MSG)
    player.trade = Trade(partner_id=init_player_id)
    query_player = DBAccessor.get_update_query_player(trade=player.trade)
    DBAccessor.update_player(_id=player.chat_id, update=query_player)
    BagMessageBuilder.build_msg_bag(bot=bot, chat_id=player.chat_id, page_number=0, trade_mode=True)


def trade_invite_deny(bot, chat_id, init_player_id):
    player = DBAccessor.get_player(chat_id)
    init_player = DBAccessor.get_player(int(init_player_id))
    MessageHelper.delete_messages_by_type(bot, player.chat_id, Constants.MESSAGE_TYPES.TRADE_INVITE_MSG)

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


def trade_pokemon_chosen(bot, chat_id, pokemon_id):
    pokemon_id = int(pokemon_id)
    player = DBAccessor.get_player(_id=chat_id)
    MessageHelper.delete_messages_by_type(bot, player.chat_id, Constants.MESSAGE_TYPES.POKE_DISPLAY_MSG)
    if player.trade is not None:
        player.trade.pokemon = DBAccessor.get_pokemon_by_id(pokemon_id)
        player.pokemon.remove(pokemon_id)
    else:
        bot.send_message(chat_id=player.chat_id, text='Your trade exceeded.')
        return
    if player.trade.pokemon is None:
        bot.send_message(chat_id=player.chat_id, text='Pokemon not found, im getting old :/')
        return
    query = DBAccessor.get_update_query_player(pokemon=player.pokemon, trade=player.trade)
    DBAccessor.update_player(_id=player.chat_id, update=query)
    bot.send_message(chat_id=player.chat_id, text='You chose {} for this trade'.format(player.trade.pokemon.name))
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

    bot.send_message(chat_id=player.chat_id,
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

            player.pokemon.append(partner.trade.pokemon.poke_id)
            partner.pokemon.append(player.trade.pokemon.poke_id)
            player.trade, partner.trade = None, None

            query_player = {'$set': {'pokemon': [i for i in player.pokemon]},
                            '$unset': {'trade': 1}}
            query_partner = {'$set': {'pokemon': [i for i in partner.pokemon]},
                             '$unset': {'trade': 1}}
            DBAccessor.update_player(_id=player.chat_id, update=query_player)
            DBAccessor.update_player(_id=partner.chat_id, update=query_partner)

            PokeDisplayBuilder.build_poke_display(bot=bot, chat_id=player.chat_id, trade_mode=False, page_num=0,
                                                  poke_id=player.pokemon[-1].poke_id)
            PokeDisplayBuilder.build_poke_display(bot=bot, chat_id=partner.chat_id, trade_mode=False, page_num=0,
                                                  poke_id=partner.pokemon[-1].poke_id)
        else:
            player.trade.accepted = True
            query_player = DBAccessor.get_update_query_player(trade=player.trade)
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
        menu_msg_id = player.get_messages(Constants.MESSAGE_TYPES.MENU_MSG)[-1]._id
        MenuMessageBuilder.update_menu_message(bot, chat_id, menu_msg_id)
        bot.send_message(chat_id=partner.chat_id, text='{} has aborted the trade.'.format(player.username))
        bot.send_message(chat_id=player.chat_id, text='The trade will be aborted.')
        partner.trade, player.trade = None, None
        query_player = {'$unset': {'trade': 1}}
        query_partner = {'$unset': {'trade': 1}}
        DBAccessor.update_player(_id=player.chat_id, update=query_player)
        DBAccessor.update_player(_id=partner.chat_id, update=query_partner)
    else:
        bot.send_message(chat_id=chat_id, text='Your trade exceeded anyway.')
        return
