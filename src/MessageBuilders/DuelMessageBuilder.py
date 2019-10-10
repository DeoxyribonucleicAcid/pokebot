import logging
import time
from io import BytesIO

import telegram
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

import Constants
import DBAccessor
from Entities import Message, Duel, Pokemon
from MessageBuilders import MessageHelper, MenuMessageBuilder


def build_current_duel_status(bot, chat_id, duel: Duel.Duel):
    player = DBAccessor.get_player(chat_id)
    friend_id = duel.participant_1.player_id if duel.participant_1.player_id is not chat_id else duel.participant_2.player_id
    img = duel.get_img(player.chat_id)
    bio_player = BytesIO()
    bio_player.name = 'duel_img_' + str(player.chat_id) + '.png'
    img.save(bio_player, 'PNG')
    bio_player.seek(0)
    keys = [[InlineKeyboardButton(text='Attack', callback_data=Constants.CALLBACK.DUEL_ACTION_ATTACK)],
            [InlineKeyboardButton(text='Nominate Champion', callback_data=Constants.CALLBACK.DUEL_ACTION_POKEMON)],
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
        build_msg_duel_active(bot=bot, chat_id=chat_id, duel_id=duel.event_id)
    elif len(player.pokemon_team) + len(player.pokemon) < Constants.DUEL_MIN_POKEMON_PER_TEAM:
        bot.send_message(chat_id=chat_id,
                         text='You have not enough Pok\xe9mon to put a team for a duel. Go on catching!')
        return
    elif len(friend.pokemon_team) + len(friend.pokemon) < Constants.DUEL_MIN_POKEMON_PER_TEAM:
        bot.send_message(chat_id=friend_id,
                         text='Your friend {} challenged you to a duel, but you have not enough '
                              'Pok\xe9mon to put a team for a duel. Go on catching!'.format(player.username))
        bot.send_message(chat_id=chat_id,
                         text='Sadly, {} has not enough Pok\xe9mon to put a team for a duel.'.format(friend.username))
        return
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
    if duel is None:
        return False
    if not (duel.participant_1.player_id == int(chat_id) or duel.participant_2.player_id == int(chat_id)):
        bot.send_message(chat_id=chat_id,
                         text='Wrong duel to be aborted. This should not happen.')
    player = DBAccessor.get_player(int(chat_id))
    friend = DBAccessor.get_player(duel.participant_1.player_id if duel.participant_1
                                   .player_id is not player.chat_id else duel.participant_2.player_id)
    MessageHelper.delete_messages_by_type(bot, player.chat_id, Constants.MESSAGE_TYPES.DUEL_STATUS_MSG)
    MessageHelper.delete_messages_by_type(bot, friend.chat_id, Constants.MESSAGE_TYPES.DUEL_STATUS_MSG)
    MessageHelper.delete_messages_by_type(bot, friend.chat_id, Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG)
    MessageHelper.delete_messages_by_type(bot, friend.chat_id, Constants.MESSAGE_TYPES.DUEL_TEAM_MSG)
    bot.send_message(chat_id=player.chat_id, text='You surrendered. {} wins!'.format(friend.username))
    bot.send_message(chat_id=friend.chat_id, text='{} aborted the duel. You win!'.format(player.username))

    DBAccessor.delete_duel(duel.event_id)
    player.duels.remove(duel.event_id)
    friend.duels.remove(duel.event_id)
    query_player = DBAccessor.get_update_query_player(duels=player.duels)
    query_friend = DBAccessor.get_update_query_player(duels=friend.duels)
    DBAccessor.update_player(_id=player.chat_id, update=query_player)
    DBAccessor.update_player(_id=friend.chat_id, update=query_friend)
    return True


def build_msg_duel_invite_accept(bot, chat_id, init_player_id):
    player = DBAccessor.get_player(int(chat_id))
    friend = DBAccessor.get_player(int(init_player_id))
    new_duel = Duel.Duel(
        participant_1=Duel.Participant(player_id=player.chat_id, action=Duel.ActionExchangePoke()),
        participant_2=Duel.Participant(player_id=friend.chat_id, action=Duel.ActionExchangePoke()), round=0)
    player.duels.append(new_duel.event_id)
    friend.duels.append(new_duel.event_id)
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.DUEL_INVITE_MSG)
    DBAccessor.insert_new_duel(duel=new_duel)
    query_player = DBAccessor.get_update_query_player(duels=player.duels)
    query_friend = DBAccessor.get_update_query_player(duels=friend.duels)
    DBAccessor.update_player(_id=player.chat_id, update=query_player)
    DBAccessor.update_player(_id=friend.chat_id, update=query_friend)
    if player.get_messages(Constants.MESSAGE_TYPES.MENU_MSG) is not None or len(
            player.get_messages(Constants.MESSAGE_TYPES.MENU_MSG)) > 0:
        MenuMessageBuilder.update_menu_message(bot, chat_id,
                                               player.get_messages(Constants.MESSAGE_TYPES.MENU_MSG)[-1]._id)
    if friend.get_messages(Constants.MESSAGE_TYPES.MENU_MSG) is not None or len(
            friend.get_messages(Constants.MESSAGE_TYPES.MENU_MSG)) > 0:
        MenuMessageBuilder.update_menu_message(bot, init_player_id,
                                               friend.get_messages(Constants.MESSAGE_TYPES.MENU_MSG)[-1]._id)
    bot.send_message(chat_id=init_player_id, text='{} accepted the challenge!'.format(player.username))
    start_duel(bot=bot, chat_id=player.chat_id, event_id=new_duel.event_id)
    start_duel(bot=bot, chat_id=friend.chat_id, event_id=new_duel.event_id)


def start_duel(bot, chat_id, event_id):
    keys = [[]]
    player = DBAccessor.get_player(chat_id)
    if len(player.pokemon_team) >= Constants.DUEL_MIN_POKEMON_PER_TEAM:
        keys[0].append(
            InlineKeyboardButton(text='Default', callback_data=Constants.CALLBACK.DUEL_START_DEFAULT(event_id)))
        text = 'Do you want to use your default team or a custom one?'
    elif len(player.pokemon_team) + len(player.pokemon) < Constants.DUEL_MIN_POKEMON_PER_TEAM:
        bot.send_message(chat_id=chat_id,
                         text='You have not enough Pok\xe9mon to put a team for a duel. Go on catching!')
        return
    else:
        text = 'Your default team is not big enough, set up a custom team!'
    keys[0].append(
        InlineKeyboardButton(text='Custom', callback_data=Constants.CALLBACK.DUEL_START_CUSTOM(event_id)))
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.MESSAGE_TYPES.DUEL_TEAM_DEFAULT_CUSTOM,
                        _time_sent=time.time()))
    query = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(chat_id, query)


def start_default_team(bot, chat_id, event_id):
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.DUEL_TEAM_DEFAULT_CUSTOM)
    build_msg_duel_action_pokemon(bot=bot, chat_id=chat_id, duel_id=event_id)


def start_custom_team(bot, chat_id, event_id):
    MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.DUEL_TEAM_DEFAULT_CUSTOM)
    send_team_selection(bot, chat_id, event_id, 0)


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
        result1 = duel.participant_1.action.perform(bot, duel.participant_1, duel.participant_1.action.target)
        result2 = duel.participant_2.action.perform(bot, duel.participant_2, duel.participant_2.action.target)
        pass
    elif duel.participant_1.action.initiative < duel.participant_2.action.initiative:
        # handle participant 1 first
        # TODO: Target has to be known to action -> no needed as parameter
        result1 = duel.participant_1.action.perform(bot, duel.participant_1, duel.participant_1.action.target)
        result2 = duel.participant_2.action.perform(bot, duel.participant_2, duel.participant_2.action.target)
    else:
        # handle participant 2 first
        # TODO: Target has to be known to action -> no needed as parameter
        result1 = duel.participant_2.action.perform(bot, duel.participant_2, duel.participant_2.action.target)
        result2 = duel.participant_1.action.perform(bot, duel.participant_1, duel.participant_1.action.target)
    duel.participant_1.action, duel.participant_2.action = None, None
    duel.round += 1

    DBAccessor.update_duel(duel_id, update=DBAccessor.get_update_query_duel(duel.participant_1, duel.participant_2))
    bot.send_message(chat_id=duel.participant_1.player_id, text=result1 + '\n' + result2)
    bot.send_message(chat_id=duel.participant_2.player_id, text=result1 + '\n' + result2)
    build_msg_duel_active(bot, chat_id=duel.participant_1.player_id, duel_id=duel.event_id)
    build_msg_duel_active(bot, chat_id=duel.participant_2.player_id, duel_id=duel.event_id)
    return


def build_msg_duel_action_chosen_source(bot, chat_id, duel_id, source_id):
    duel_id = int(duel_id)
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG)
    duel = DBAccessor.get_duel_by_id(int(duel_id))

    duel.get_participant_by_id(chat_id).action.set_source(bot, duel.get_participant_by_id(chat_id), source_id)
    duel.update_participant(chat_id)
    if duel.participant_1.action.completed and duel.participant_2.action.completed:
        calc_round(bot, duel_id)
    else:
        build_msg_duel_active(bot, chat_id=chat_id, duel_id=duel.event_id)


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
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    if duel is None:
        raise ValueError('Duel {} is None! ChatId: {}'.format(duel_id, chat_id))
    if duel.get_participant_by_id(chat_id) is not None and player.pokemon_team is not None and len(
            player.pokemon_team) >= Constants.DUEL_MIN_POKEMON_PER_TEAM:
        duel.get_participant_by_id(chat_id).team = player.pokemon_team
        duel.update_participant(chat_id)
    if duel.get_participant_by_id(chat_id).team is None or len(duel.get_participant_by_id(chat_id).team) < 3:
        bot.send_message(chat_id=player.chat_id,
                         text='Your pokemon-team is too small. '
                              'This should not happen at this time. Blame the devs and choose again!!')
        send_team_selection(bot, chat_id, duel_id, 0)
        return
    if duel.get_participant_by_id(chat_id).action is None:
        duel.get_participant_by_id(chat_id).action = Duel.ActionExchangePoke()
        duel.update_participant(chat_id)
    build_choose_from_team(bot, chat_id, duel_id)


def build_msg_duel_action_attack(bot, chat_id, duel_id):
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    duel.get_participant_by_id(chat_id).action = Duel.ActionAttack(duel_id=duel.event_id)
    duel.update_participant(chat_id)
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
    cross = emojize(":x:", use_aliases=True)
    for move in poke1.moves:
        # id
        # accuracy
        # power
        # pp
        # priority
        # target
        # type.name
        # names[find language.name == 'en'].name
        # move = Move.Move.get_move(m['url'])
        blocked = cross if move.target not in ['selected-pokemon', 'all-opponents'] else ''
        keys.append([InlineKeyboardButton(text='{}{} Acc:{} Pow:{} Prio:{}'.format(blocked, move.name, move.accuracy,
                                                                                   move.power, move.priority),
                                          callback_data=Constants.CALLBACK.DUEL_ACTION_CHOSEN(event_id=duel.event_id,
                                                                                              source_id=move.move_id))])
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG)
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.DUEL_STATUS_MSG)
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
    if duel is not None and duel.participant_1.action is not None and duel.participant_2.action is not None and duel.participant_1.action.completed and duel.participant_2.action.completed:
        calc_round(bot, duel_id)

    if duel.get_participant_by_id(chat_id).team is not None:
        poke_player = [DBAccessor.get_pokemon_by_id(i) for i in duel.get_participant_by_id(chat_id).team]
    else:
        poke_player = None
    if duel.get_participant_by_id(chat_id).pokemon is not None:
        champion_player = DBAccessor.get_pokemon_by_id(duel.get_participant_by_id(chat_id).pokemon)
    else:
        champion_player = None
    if duel.get_counterpart_by_id(chat_id).pokemon is not None:
        champion_opponent = DBAccessor.get_pokemon_by_id(duel.get_counterpart_by_id(chat_id).pokemon)
    else:
        champion_opponent = None
    if duel.get_participant_by_id(chat_id).pokemon is not None:
        # Display Champion first
        for i, poke in enumerate(poke_player):
            if poke.poke_id == int(duel.get_participant_by_id(chat_id).pokemon):
                poke_player[0], poke_player[i] = poke_player[i], poke_player[0]
                break
    img = Pokemon.build_pokemon_duel_info_image(poke_player, champion_player, champion_opponent)
    keys = []

    # keys = [[InlineKeyboardButton(text='Attack', callback_data=Constants.CALLBACK.DUEL_ACTION_ATTACK)],
    #         [InlineKeyboardButton(text='Exchange Pokemon', callback_data=Constants.CALLBACK.DUEL_ACTION_POKEMON)],
    #         [InlineKeyboardButton(text='Use Item', callback_data=Constants.CALLBACK.DUEL_ACTION_ITEM)]]
    caption = ''
    if duel.get_participant_by_id(chat_id).team is None:
        # TODO: Should this happen? Probably the team has to be chosen at this point already.
        keys.append([InlineKeyboardButton(text='Choose Team',
                                          callback_data=Constants.CALLBACK.DUEL_TEAM_PAGE(duel.event_id, 0))])
    elif duel.get_participant_by_id(chat_id).action is None:
        if duel.get_participant_by_id(chat_id).team is None or len(
                duel.get_participant_by_id(chat_id).team) < Constants.DUEL_MIN_POKEMON_PER_TEAM:
            keys.append(
                InlineKeyboardButton(text='Set up team',
                                     callback_data=Constants.CALLBACK.DUEL_START_CUSTOM(duel.event_id)))
            caption += 'You have to choose a team first!'
        else:
            if duel.get_participant_by_id(chat_id).pokemon is not None:
                keys.append([InlineKeyboardButton(text='Attack', callback_data=Constants.CALLBACK.DUEL_ACTION_ATTACK(
                    event_id=duel_id))])
            keys.append([InlineKeyboardButton(text='Nominate Champion',
                                              callback_data=Constants.CALLBACK.DUEL_ACTION_POKEMON(
                                                  event_id=duel.event_id))])
            keys.append([InlineKeyboardButton(text='Use Item',
                                              callback_data=Constants.CALLBACK.DUEL_ACTION_ITEM(event_id=duel_id))])
    else:
        keys.append([InlineKeyboardButton(text='Remind {} to choose'.format(
            DBAccessor.get_player(duel.get_counterpart_by_id(chat_id).player_id).username),
            callback_data=Constants.CALLBACK.DUEL_NOTIFY(event_id=duel_id))])
        if type(duel.get_participant_by_id(chat_id).action) == Duel.ActionAttack:
            caption += '\nYou chose to attack'
            if duel.get_participant_by_id(chat_id).action.source is None and not duel.get_participant_by_id(
                    chat_id).action.completed:
                keys.append([InlineKeyboardButton(text='Choose Attack',
                                                  callback_data=Constants.CALLBACK.DUEL_ACTION_ATTACK(
                                                      event_id=duel.event_id))])
                caption += ' but you have not chosen an attack yet!'

        elif type(duel.get_participant_by_id(chat_id).action) == Duel.ActionExchangePoke:
            if duel.get_participant_by_id(chat_id).action.source is None and not duel.get_participant_by_id(
                    chat_id).action.completed:
                keys.append([InlineKeyboardButton(text='Nominate Champion',
                                                  callback_data=Constants.CALLBACK.DUEL_ACTION_POKEMON(
                                                      event_id=duel.event_id))])
                caption += '\nYou chose to switch your champion but you have not chosen a champion yet!'
            else:
                caption += '\nYou chose to switch to {} as champion'.format(
                    DBAccessor.get_pokemon_by_id(duel.get_participant_by_id(chat_id).action.source).name)

        elif type(duel.get_participant_by_id(chat_id).action) == Duel.ActionUseItem:
            caption += '\nYou chose to use an item'
            if duel.get_participant_by_id(chat_id).action.source is None and not duel.get_participant_by_id(
                    chat_id).action.completed:
                keys.append([InlineKeyboardButton(text='Use Item',
                                                  callback_data=Constants.CALLBACK.DUEL_ACTION_ITEM(
                                                      event_id=duel.event_id))])
                caption += ' but you have not chosen a champion yet!'
    keys.append([InlineKeyboardButton(text='Surrender and abort duel',
                                      callback_data=Constants.CALLBACK.DUEL_ABORT(event_id=duel.event_id))])
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    player = DBAccessor.get_player(chat_id)
    MessageHelper.delete_messages_by_type(bot, player.chat_id, Constants.MESSAGE_TYPES.DUEL_STATUS_MSG)
    if img is not None:
        bio = BytesIO()
        bio.name = 'image_duel_info_' + str(chat_id) + '.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        msg = bot.send_photo(chat_id=chat_id,
                             photo=bio,
                             caption='Current Status' + caption,
                             reply_markup=reply_markup,
                             parse_mode=ParseMode.MARKDOWN)
    else:
        msg = bot.send_message(chat_id=chat_id,
                               text='Neither have you chosen your Pokemon team for '
                                    'this duel nor has your opponent nominated a champion.',
                               reply_markup=reply_markup)
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.MESSAGE_TYPES.DUEL_STATUS_MSG, _time_sent=time.time()))
    query = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=query)


def build_choose_from_team(bot, chat_id, duel_id):
    duel_id = int(duel_id)
    player = DBAccessor.get_player(chat_id)
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    friend_id = duel.participant_1.player_id if duel.participant_1.player_id != chat_id else duel.participant_2.player_id
    friend = DBAccessor.get_player(int(friend_id))
    # If the Player should be informed about other participant's poke team
    # caption=''
    # for poke in friend.pokemon_team:
    #     caption += '{} Lvl: {} HP: {}/{}\n'.format(poke.name, poke.level, poke.health, poke.max_health)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='I have not met you yet. Want to be a Pok\xe9mon trainer? Type /catch.')
        return
    elif len(duel.get_participant_by_id(chat_id).team) is 0 or duel.get_participant_by_id(chat_id).team is None:
        bot.send_message(chat_id=chat_id,
                         text='Your Pok\xe9mon team is empty. Choose candidates from your /bag.')
        return
    elif len(duel.get_participant_by_id(chat_id).team) > 6:
        bot.send_message(chat_id=chat_id,
                         text='You somehow managed to add more than 6 Pok\xe9mon to your team. Outrageous! '
                              'Please remove some :) (and blame the devs)')
        return
    pokemon_sprite_list, keys = [], []
    for pokemon_id in duel.get_participant_by_id(chat_id).team:
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


def nominate_team_member(bot, chat_id, event_id: int, page_number: int, poke_id: int):
    chat_id = int(chat_id)
    event_id = int(event_id)
    page_number = int(page_number)
    poke_id = int(poke_id)
    duel = DBAccessor.get_duel_by_id(event_id)
    if duel.get_participant_by_id(chat_id).team is None:
        duel.get_participant_by_id(chat_id).team = [poke_id]
    elif poke_id not in duel.get_participant_by_id(int(chat_id)).team:
        duel.get_participant_by_id(chat_id).team.append(poke_id)
    else:
        duel.get_participant_by_id(chat_id).team.remove(poke_id)

    if chat_id == duel.participant_1.player_id:
        update_duel = DBAccessor.get_update_query_duel(participant_1=duel.participant_1)
    elif chat_id == duel.participant_2.player_id:
        update_duel = DBAccessor.get_update_query_duel(participant_2=duel.participant_2)
    else:
        raise ValueError('Participant not found! Chat_id: {} Event_id: {} '.format(chat_id, event_id))
    DBAccessor.update_duel(event_id, update_duel)
    update_team_selection(bot, chat_id, event_id, page_number)


def send_team_selection(bot, chat_id, event_id: int, page_number: int):
    image, caption, reply_markup = build_team_selection(bot, chat_id, event_id, page_number)
    bio = BytesIO()
    bio.name = 'image_duel_team_' + str(chat_id) + '.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    msg = bot.send_photo(chat_id=chat_id,
                         photo=bio,
                         caption=caption,
                         parse_mode=ParseMode.MARKDOWN,
                         reply_markup=reply_markup)
    player = DBAccessor.get_player(chat_id)
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.MESSAGE_TYPES.DUEL_TEAM_MSG,
                        _time_sent=time.time()))
    update = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(chat_id, update=update)

    duel = DBAccessor.get_duel_by_id(int(event_id))
    duel.get_participant_by_id(chat_id).team_selection = Message.Message(_id=msg.message_id,
                                                                         _title=Constants.MESSAGE_TYPES.DUEL_TEAM_MSG,
                                                                         _time_sent=time.time())
    if chat_id == duel.participant_1.player_id:
        update_duel = DBAccessor.get_update_query_duel(participant_1=duel.participant_1)
    elif chat_id == duel.participant_2.player_id:
        update_duel = DBAccessor.get_update_query_duel(participant_2=duel.participant_2)
    else:
        raise ValueError('Participant not found! Chat_id: {} Event_id: {} '.format(chat_id, event_id))
    DBAccessor.update_duel(event_id, update_duel)


def update_team_selection(bot, chat_id, event_id: int, page_number: int):
    # TODO: dont really need the img here -> performance issue
    _, caption, reply_markup = build_team_selection(bot, chat_id, event_id, page_number)
    player = DBAccessor.get_player(int(chat_id))
    duel = DBAccessor.get_duel_by_id(int(event_id))
    if duel.get_participant_by_id(int(chat_id)).team_selection is None:
        raise ValueError()
    nomination_msg_id = int(duel.get_participant_by_id(int(chat_id)).team_selection._id)
    if player is None:
        return False

    try:
        bot.edit_message_caption(chat_id=chat_id, caption=caption, message_id=nomination_msg_id,
                                 reply_markup=reply_markup)
    except telegram.error.BadRequest as e:
        if e.message != 'Message is not modified':
            raise e


def build_team_selection(bot, chat_id, duel_id, page_number):
    player = DBAccessor.get_player(chat_id)
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    page_number = int(page_number)
    pokecount = 8
    pokemon_sprite_list = []
    caption = ''
    if len(player.pokemon) > pokecount:
        if (page_number + 1) * pokecount <= len(player.pokemon):
            caption = '*Page Number: * {}  Pok\xe9 {}-{}'.format(str(page_number), str((page_number * pokecount) + 1),
                                                                 (str((page_number + 1) * pokecount)))
        else:
            caption = '{}/{}\n'.format(str(len(player.pokemon)), str(len(player.pokemon)))
    list_start = pokecount * page_number
    list_end = pokecount * (page_number + 1) if len(player.pokemon) >= pokecount * (page_number + 1) else len(
        player.pokemon)
    page_list = player.pokemon[list_start:list_end]
    keys = []
    checkmark = emojize(":white_check_mark:", use_aliases=True)
    skeleton = emojize(":skeleton:", use_aliases=True)
    for pokemon_id in page_list:
        pokemon = DBAccessor.get_pokemon_by_id(pokemon_id)
        if pokemon.health > 0:
            keys.append([InlineKeyboardButton(
                text=checkmark + ' ' + pokemon.name + ' ' + checkmark if duel.get_participant_by_id(
                    chat_id).team is not None and pokemon_id in duel.get_participant_by_id(
                    chat_id).team else pokemon.name,
                callback_data=Constants.CALLBACK.DUEL_TEAM_NOMINATE(
                    event_id=duel_id,
                    page_number=page_number,
                    poke_id=pokemon_id
                ))
            ])
        else:
            keys.append([InlineKeyboardButton(text=skeleton + ' ' + pokemon.name + ' ' + skeleton)])
        pokemon_sprite_list.append(pokemon.sprites['front'])
    image = Pokemon.build_pokemon_bag_image(pokemon_sprite_list)
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.POKE_DISPLAY_MSG)
    MessageHelper.delete_messages_by_type(bot=bot, chat_id=chat_id, type=Constants.MESSAGE_TYPES.BAG_MSG)
    if image is None:
        msg = bot.send_message(chat_id=chat_id,
                               text='Your bag is empty, catch some pokemon!')
        return

    page_keys = []
    if page_number > 0:
        page_keys.append(InlineKeyboardButton(text='\u2190',
                                              callback_data=Constants.CALLBACK.DUEL_TEAM_PAGE(duel_id,
                                                                                              page_number - 1)))
    if len(player.pokemon) > list_end:
        page_keys.append(InlineKeyboardButton(text='\u2192',
                                              callback_data=Constants.CALLBACK.DUEL_TEAM_PAGE(duel_id,
                                                                                              page_number + 1)))

    control_keys = [
        InlineKeyboardButton(text='Abort', callback_data=Constants.CALLBACK.DUEL_TEAM_ABORT(event_id=duel_id))]
    if duel.get_participant_by_id(chat_id).team is not None and len(
            duel.get_participant_by_id(chat_id).team) >= Constants.DUEL_MIN_POKEMON_PER_TEAM:
        control_keys.append(InlineKeyboardButton(text='Accept Team',
                                                 callback_data=Constants.CALLBACK.DUEL_TEAM_ACCEPT(
                                                     event_id=duel_id)))
    keys.append(page_keys)
    keys.append(control_keys)

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keys)
    return image, caption, reply_markup


def abort_team_selection(bot, chat_id, duel_id):
    duel_id = int(duel_id)
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    player = DBAccessor.get_player(int(chat_id))
    try:
        bot.delete_message(chat_id=chat_id, message_id=duel.get_participant_by_id(chat_id).team_selection._id)
    except telegram.error.BadRequest as e:
        logging.error(e)
    player.messages_to_delete.remove(duel.get_participant_by_id(chat_id).team_selection._id)
    duel.get_participant_by_id(chat_id).team_selection = None
    duel.get_participant_by_id(chat_id).team = None
    update_player = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)

    if chat_id == duel.participant_1.player_id:
        update_duel = DBAccessor.get_update_query_duel(participant_1=duel.participant_1)
    elif chat_id == duel.participant_2.player_id:
        update_duel = DBAccessor.get_update_query_duel(participant_2=duel.participant_2)
    else:
        raise ValueError('Participant not found! Chat_id: {} Event_id: {} '.format(chat_id, duel_id))
    DBAccessor.update_player(_id=player.chat_id, update=update_player)
    DBAccessor.update_duel(_id=duel_id, update=update_duel)


def accept_team_selection(bot, chat_id, duel_id):
    duel_id = int(duel_id)
    duel = DBAccessor.get_duel_by_id(duel_id)
    if len(duel.get_participant_by_id(chat_id).team) < Constants.DUEL_MIN_POKEMON_PER_TEAM:
        msg = bot.send_message(text='Cannot accept team, it\'s too small', chat_id=chat_id)
        return
    elif len(duel.get_participant_by_id(chat_id).team) > Constants.DUEL_MAX_POKEMON_PER_TEAM:
        duel.get_participant_by_id(chat_id).team = duel.get_participant_by_id(chat_id).team[
                                                   :Constants.DUEL_MAX_POKEMON_PER_TEAM]
        msg = bot.send_message(text='Accepted team, but it was too big. Removed last champion', chat_id=chat_id)

    player = DBAccessor.get_player(chat_id)

    try:
        bot.delete_message(chat_id=chat_id, message_id=duel.get_participant_by_id(chat_id).team_selection._id)
    except telegram.error.BadRequest as e:
        logging.error(e)
    if duel.get_participant_by_id(chat_id).team_selection._id in player.messages_to_delete:
        player.messages_to_delete.remove(duel.get_participant_by_id(chat_id).team_selection._id)
    duel.get_participant_by_id(chat_id).team_selection = None

    update_player = DBAccessor.get_update_query_player(messages_to_delete=player.messages_to_delete)
    if chat_id == duel.participant_1.player_id:
        update_duel = DBAccessor.get_update_query_duel(participant_1=duel.participant_1)
    elif chat_id == duel.participant_2.player_id:
        update_duel = DBAccessor.get_update_query_duel(participant_2=duel.participant_2)
    else:
        raise ValueError('Participant not found! Chat_id: {} Event_id: {} '.format(chat_id, duel_id))
    DBAccessor.update_player(_id=player.chat_id, update=update_player)
    DBAccessor.update_duel(_id=duel_id, update=update_duel)
    build_msg_duel_action_pokemon(bot=bot, chat_id=chat_id, duel_id=duel_id)


def notify_opponent(bot, chat_id, duel_id):
    duel = DBAccessor.get_duel_by_id(int(duel_id))
    if duel is None:
        bot.send_message(chat_id=duel.get_counterpart_by_id(chat_id).player_id,
                         text='The fight is over, go home\n(or start a new one)')
        MessageHelper.delete_messages_by_type(bot, chat_id, Constants.MESSAGE_TYPES.DUEL_STATUS_MSG)
    msg_ping = bot.send_message(chat_id=duel.get_counterpart_by_id(chat_id).player_id,
                                text='Your opponent for you to take action and is getting impatient.')
    MessageHelper.append_message_to_player(duel.get_counterpart_by_id(chat_id).player_id,
                                           message_id=msg_ping.message_id,
                                           type=Constants.MESSAGE_TYPES.DUEL_CHOOSE_MSG)
    build_msg_duel_active(bot, duel.get_counterpart_by_id(chat_id).player_id, duel_id)
