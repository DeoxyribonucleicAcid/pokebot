import logging
import time
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

import Constants
import DBAccessor
from Entities import Message, Duel, Pokemon, Move
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
        Message.Message(_id=msg.message_id, _title=Constants.MESSAGE_TYPES.DUEL_STATUS_MSG, _time_sent=time.time()))
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
            Message.Message(_id=invite_msg.message_id, _title=Constants.MESSAGE_TYPES.DUEL_INVITE_MSG,
                            _time_sent=time.time()))
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
    if not (duel.participant_1.player_id == int(chat_id) or duel.participant_2.player_id == int(chat_id)):
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
    if len(friend.pokemon_team) < 3:
        bot.send_message(chat_id=player.chat_id,
                         text='Your Pokemon-Team is too small for a duel.'
                              ' Choose at least 3 Champions before continuing your duel!')
        return
    new_duel = Duel.Duel(
        participant_1=Duel.Participant(player_id=player.chat_id, action=Duel.ActionExchangePoke()),
        participant_2=Duel.Participant(player_id=friend.chat_id, action=Duel.ActionExchangePoke()), round=0)
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
    MessageHelper.delete_messages_by_type(bot, player.chat_id, Constants.MESSAGE_TYPES.DUEL_INVITE_MSG)
    bot.send_message(chat_id=player.chat_id,
                     text='Duel cancelled')
    bot.send_message(chat_id=init_player.chat_id,
                     text='Your friend is currently not interested in a challenge.')


def calc_round(bot, duel_id: int):
    # Floor( ½ * Power * \frac{Atk}{Def} * Multipliers) + 1
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    logging.info('Calculating round {} of duel {}'.format(duel.round, duel.event_id))
    poke_part_1_id = duel.participant_1.pokemon
    poke_part_2_id = duel.participant_1.pokemon
    if duel.participant_1.action.initiative == duel.participant_2.action.initiative:
        # handle simultaneous actions
        pass
    elif duel.participant_1.action.initiative < duel.participant_2.action.initiative:
        # handle participant 1 first
        # TODO: Target has to be known to action -> no needed as parameter
        duel.participant_1.action.perform(bot, duel.participant_1, duel.participant_1.action.target)
        duel.participant_2.action.perform(bot, duel.participant_2, duel.participant_2.action.target)
    else:
        # handle participant 2 first
        # TODO: Target has to be known to action -> no needed as parameter
        duel.participant_2.action.perform(bot, duel.participant_2, duel.participant_2.action.target)
        duel.participant_1.action.perform(bot, duel.participant_1, duel.participant_1.action.target)


def build_msg_duel_action_chosen_source(bot, chat_id, duel_id, source_id):
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG)
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    if chat_id == duel.participant_1.player_id:
        duel.participant_1.action.set_source(bot, duel.participant_1, source_id)
        query = DBAccessor.get_update_query_duel(participant_1=duel.participant_1)
    elif chat_id == duel.participant_2.player_id:
        duel.participant_2.action.set_source(bot, duel.participant_2, source_id)
        query = DBAccessor.get_update_query_duel(participant_2=duel.participant_2)
    else:
        raise AttributeError('Duel Participants incorrect: Duel_id: {}'.format(duel.event_id))
    DBAccessor.update_duel(_id=duel.event_id, update=query)
    if duel.participant_1.action.completed and duel.participant_2.action.completed:
        calc_round(bot, duel_id)


def build_msg_duel_action_chosen_target(bot, chat_id, duel_id, target_id):
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG)
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    if chat_id == duel.participant_1.player_id:
        duel.participant_1.action.perform(bot, duel.participant_1, target_id)
        query = DBAccessor.get_update_query_duel(participant_1=duel.participant_1)
    elif chat_id == duel.participant_2.player_id:
        duel.participant_2.action.perform(bot, duel.participant_2, target_id)
        query = DBAccessor.get_update_query_duel(participant_2=duel.participant_2)
    else:
        raise AttributeError('Duel Participants incorrect: Duel_id: {}'.format(duel.event_id))
    DBAccessor.update_duel(_id=duel.event_id, update=query)
    if duel.participant_1.action.completed and duel.participant_2.action.completed:
        calc_round(bot, duel_id)


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
    build_choose_from_team(bot, chat_id, duel_id)


def build_msg_duel_action_attack(bot, chat_id, duel_id):
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    participant_player = duel.get_participant_by_id(chat_id)
    # participant = duel.get_counterpart_by_id(chat_id)
    poke1 = DBAccessor.get_pokemon_by_id(participant_player.pokemon)
    # poke2 = DBAccessor.get_pokemon_by_id(participant.pokemon)
    if participant_player.pokemon is None:
        bot.send_message(chat_id=participant_player.player_id,
                         text='Your pokemon-champion is somehow not set! You have to choose again')
        raise AttributeError('Champion is None: Duel_id: {}'.format(duel.event_id))
    elif poke1.moves is None or len(poke1.moves) is 0:
        bot.send_message(chat_id=participant_player.player_id,
                         text='Your pokemon-champion has not enough attack moves!')
        raise AttributeError('Champion has no moves: Duel_id: {} Poke_id: {}'
                             .format(duel.event_id, participant_player.pokemon))

    keys = []
    for m in poke1.moves:
        # id
        # accuracy
        # power
        # pp
        # priority
        # target
        # type.name
        # names[find language.name == 'en'].name
        move = Move.Move.get_move(m['url'])
        keys.append([InlineKeyboardButton(text='{} Acc:{} Pow:{} Prio:{}'.format(move.name, move.accuracy,
                                                                                 move.power, move.priority),
                                          callback_data=Constants.CALLBACK.DUEL_ACTION_CHOSEN(event_id=duel.event_id,
                                                                                              source_id=move.move_id))])
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG)
    image = Pokemon.get_pokemon_portrait_image(pokemon_sprite=poke1.sprites['front'])
    if image is not None:
        bio = BytesIO()
        bio.name = 'image_duel_choose_attack_' + str(chat_id) + '.png'
        image.save(bio, 'PNG')
        bio.seek(0)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
        msg = bot.send_photo(chat_id=chat_id,
                             photo=bio,
                             reply_markup=reply_markup,
                             caption='Choose {}\'s attack'.format(poke1.name),
                             parse_mode=ParseMode.MARKDOWN)
    else:
        msg = bot.send_message(chat_id=chat_id,
                               text='Your team is empty, nominate some pokemon!')
    player = DBAccessor.get_player(int(chat_id))
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG, _time_sent=time.time()))
    update = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=update)


def build_msg_duel_action_item(bot, chat_id, duel_id):
    bot.send_message(chat_id=chat_id, text='Method not implemented yet.')


def build_msg_duel_active(bot, chat_id, duel_id):
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    poke_opponent = DBAccessor.get_pokemon_by_id(duel.get_counterpart_by_id(chat_id).pokemon)

    bot.send_message(chat_id=chat_id, text='Method not implemented yet.')


def build_choose_from_team(bot, chat_id, duel_id):
    player = DBAccessor.get_player(chat_id)
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    friend_id = duel.participant_1.player_id if duel.participant_1.player_id is not chat_id else duel.participant_2.player_id
    friend = DBAccessor.get_player(int(friend_id))
    # If the Player should be informed about other participant's poke team
    # caption=''
    # for poke in friend.pokemon_team:
    #     caption += '{} Lvl: {} HP: {}/{}\n'.format(poke.name, poke.level, poke.health, poke.max_health)
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
    for pokemon_id in player.pokemon_team:
        pokemon = DBAccessor.get_pokemon_by_id(pokemon_id)
        keys.append([InlineKeyboardButton(text='{} Level:{} Health:{}/{}'.format(pokemon.name, pokemon.level,
                                                                                 pokemon.health, pokemon.max_health),
                                          callback_data=Constants.CALLBACK.DUEL_ACTION_CHOSEN(event_id=duel.event_id,
                                                                                              source_id=pokemon.poke_id))])
        pokemon_sprite_list.append(pokemon.sprites['front'])
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG)
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
                             caption='Choose your champion in battle against {}!'.format(friend.username),
                             parse_mode=ParseMode.MARKDOWN)
    else:
        msg = bot.send_message(chat_id=chat_id,
                               text='Your team is empty, nominate some pokemon!')
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG, _time_sent=time.time()))
    update = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=update)
