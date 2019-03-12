import time
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

import Constants
import DBAccessor
from Entities import Message, Duel, Pokemon
from MessageBuilders import MessageHelper


def build_current_duel_status(bot, chat_id, duel: Duel.Duel):
    player = DBAccessor.get_player(chat_id)
    friend_id = duel.participant_1.player_id if duel.participant_1.player_id is not chat_id else duel.participant_2.player_id
    img = duel.get_img(player.chat_id)
    bio_player = BytesIO()
    bio_player.name = 'duel_img_' + str(player.chat_id) + '.png'
    img.save(bio_player, 'PNG')
    bio_player.seek(0)
    keys = [[InlineKeyboardButton(text='Attack', callback_data=Constants.CALLBACK.DUEL_ACTION_ATTACK)],
            [InlineKeyboardButton(text='Exchange Pokemon', callback_data=Constants.CALLBACK.DUEL_ACTION_POKEMON)],
            [InlineKeyboardButton(text='Use Item', callback_data=Constants.CALLBACK.DUEL_ACTION_ITEM)]]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)

    msg = bot.send_photo(chat_id=player.chat_id, text='Choose your action!',
                         photo=bio_player, reply_markup=reply_markup)
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.DUEL_STATUS_MSG, _time_sent=time.time()))
    query = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=query)


def build_msg_duel_start_nofriend(bot, chat_id):
    MessageHelper.build_choose_friend_message(bot=bot, chat_id=chat_id, mode=Constants.CHOOSE_FRIEND_MODE.DUEL)


def build_msg_duel_start_friend(bot, chat_id, friend_id):
    player = DBAccessor.get_player(chat_id)
    friend = DBAccessor.get_player(int(friend_id))
    duel = DBAccessor.get_duel_by_participants(chat_id, friend_id)
    if duel is not None:
        bot.send_message(chat_id=player.chat_id,
                         text='You are already dueling with {}'.format(friend.username))
        build_current_duel_status(bot=bot, chat_id=chat_id, duel=duel)
    else:
        keys = [[
            InlineKeyboardButton(text='Yes', callback_data=Constants.CALLBACK.DUEL_INVITE_ACCEPT(player.chat_id)),
            InlineKeyboardButton(text='No', callback_data=Constants.CALLBACK.DUEL_INVITE_DENY(player.chat_id))
        ]]
        reply_keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
        invite_msg = bot.send_message(chat_id=friend_id,
                                      text='Your friend ' + str(
                                          player.username) + ' challenges you to a duel. Are you interested?',
                                      reply_markup=reply_keyboard)
        friend.messages_to_delete.append(
            Message.Message(_id=invite_msg.message_id, _title=Constants.DUEL_INVITE_MSG, _time_sent=time.time()))
        query_friend = DBAccessor.get_update_query_player(messages_to_delete=friend.messages_to_delete)
        DBAccessor.update_player(_id=friend.chat_id, update=query_friend)
        bot.send_message(chat_id=chat_id, text='...Awaiting {}\'s response...'.format(friend.username))

    # if len(player.duels) is not 0:
    #     bot.send_message(chat_id=player.chat_id,
    #                      text='You are currently dueling with {}'
    #                      .format(' '.join([DBAccessor.get_player(int())
    #                                       .username for duel in player.duels])))
    #     # build_choose_duel_message(bot=bot, chat_id=player.chat_id)
    # if friend.trade is not None:
    #     bot.send_message(chat_id=player.chat_id,
    #                      text='Your friend is currently trading with somebody else')
    #     return


def abort_duel(bot, chat_id, duel_id):
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    if not (duel.participant_1.player_id is chat_id or duel.participant_2.player_id is chat_id):
        bot.send_message(chat_id=chat_id,
                         text='Wrong duel to be aborted. This should not happen.')
    player = DBAccessor.get_player(int(chat_id))
    friend = DBAccessor.get_player(duel.participant_1.player_id if duel.participant_1
                                   .player_id is not player.chat_id else duel.participant_2.player_id)
    DBAccessor.delete_duel(duel.event_id)
    player.duels.remove(duel.event_id)
    friend.duels.remove(duel.event_id)
    query_player = DBAccessor.get_update_query_player(duels=player.duels)
    query_friend = DBAccessor.get_update_query_player(duels=friend.duels)
    DBAccessor.update_player(_id=player.chat_id, update=query_player)
    DBAccessor.update_player(_id=friend.chat_id, update=query_friend)


def build_msg_duel_invite_accept(bot, chat_id, init_player_id):
    player = DBAccessor.get_player(int(chat_id))
    friend = DBAccessor.get_player(int(init_player_id))
    new_duel = Duel.Duel(participant_1=Duel.Participant(player_id=player.chat_id, action=Duel.ActionExchangePoke()),
                         participant_2=Duel.Participant(player_id=friend.chat_id, action=Duel.ActionExchangePoke()))
    player.duels.append(new_duel.event_id)
    friend.duels.append(new_duel.event_id)
    DBAccessor.insert_new_duel(duel=new_duel)
    query_player = DBAccessor.get_update_query_player(duels=player.duels)
    query_friend = DBAccessor.get_update_query_player(duels=friend.duels)
    DBAccessor.update_player(_id=player.chat_id, update=query_player)
    DBAccessor.update_player(_id=friend.chat_id, update=query_friend)
    build_msg_duel_action_pokemon(bot=bot, chat_id=player.chat_id, duel_id=new_duel.event_id)
    build_msg_duel_action_pokemon(bot=bot, chat_id=friend.chat_id, duel_id=new_duel.event_id)


def build_msg_duel_invite_deny(bot, chat_id, init_player_id):
    player = DBAccessor.get_player(int(chat_id))
    init_player = DBAccessor.get_player(int(init_player_id))
    MessageHelper.delete_messages_by_type(bot, player.chat_id, Constants.DUEL_INVITE_MSG)
    bot.send_message(chat_id=player.chat_id,
                     text='Duel cancelled')
    bot.send_message(chat_id=init_player.chat_id,
                     text='Your friend is currently not interested in a challenge.')


def build_msg_duel_action_chosen(bot, chat_id, duel_id, source_id):
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    if chat_id is duel.participant_1.player_id:
        duel.participant_1.action.set_source(source=source_id)
        query = DBAccessor.get_update_query_duel(participant_1=duel.participant_1)
    elif chat_id is duel.participant_2.player_id:
        duel.participant_2.action.set_source(source=source_id)
        query = DBAccessor.get_update_query_duel(participant_2=duel.participant_2)
    else:
        raise AttributeError('Duel Participants incorrect: Duel_id: {}'.format(duel.event_id))
    DBAccessor.update_duel(_id=duel.event_id, update=query)


def build_msg_duel_action_pokemon(bot, chat_id, duel_id):
    player = DBAccessor.get_player(int(chat_id))
    if len(player.pokemon_team) < 3:
        bot.send_message(chat_id=player.chat_id,
                         text='Your pokemon-team is too small. '
                              'This should not happen at this time. Duel will be aborted!')
        duel = DBAccessor.get_duel_by_id(int(duel_id))
        friend = DBAccessor.get_player(duel.participant_1.player_id if duel.participant_1
                                       .player_id is not player.chat_id else duel.participant_2.player_id)
        bot.send_message(chat_id=friend.chat_id,
                         text='An error occurred. Aborted your duel with {}!'.format(player.username))
        bot.send_message(chat_id=player.chat_id,
                         text='Aborted your duel with {}! You loose!'.format(friend.username))
        abort_duel(bot=bot, chat_id=chat_id, duel_id=duel_id)
        return
    build_choose_from_team(bot, chat_id)


def build_msg_duel_action_attack(bot, chat_id, ):
    bot.send_message(chat_id=chat_id, text='Method not implemented yet.')


def build_msg_duel_action_item(bot, chat_id, ):
    bot.send_message(chat_id=chat_id, text='Method not implemented yet.')


def build_msg_duel_active(bot, chat_id, duel_id):
    bot.send_message(chat_id=chat_id, text='Method not implemented yet.')


def build_choose_from_team(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='I have not met you yet. Want to be a Pok\xe9mon trainer? Type /catch.')
        return
    elif len(player.pokemon_team) is 0 or None:
        bot.send_message(chat_id=chat_id,
                         text='Your Pok\xe9mon team is empty. Choose candidates from your /bag.')
        return
    elif len(player.pokemon_team) > 6:
        bot.send_message(chat_id=chat_id,
                         text='You somehow managed to add more than 6 Pok\xe9mon to your team. Outrageous! '
                              'Please remove some :) (and blame the devs)')
        return
    pokemon_sprite_list, keys = [], []
    for pokemon in player.pokemon_team:
        keys.append([InlineKeyboardButton(text='{} Level:{} Health:{}/{}'.format(pokemon.name, pokemon.level,
                                                                                 pokemon.health, pokemon.max_health),
                                          callback_data=Constants.CALLBACK.DUEL_ACTION_CHOSEN(event_id=pokemon._id,
                                                                                              source_id=pokemon._id))])
        pokemon_sprite_list.append(pokemon.sprites['front'])
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.DUEL_CHOOSE_MSG)
    image = Pokemon.build_pokemon_bag_image(pokemon_sprite_list=pokemon_sprite_list, max_row_len=3)
    if image is not None:
        bio = BytesIO()
        bio.name = 'image_duel_choose_' + str(chat_id) + '.png'
        image.save(bio, 'PNG')
        bio.seek(0)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
        msg = bot.send_photo(chat_id=chat_id,
                             photo=bio,
                             reply_markup=reply_markup,
                             caption='Choose your champion!', parse_mode=ParseMode.MARKDOWN)
    else:
        msg = bot.send_message(chat_id=chat_id,
                               text='Your team is empty, nominate some pokemon!')
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.DUEL_CHOOSE_MSG, _time_sent=time.time()))
    update = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=update)
