import logging
import random
from enum import Enum
from typing import List

import Constants
import DBAccessor
import Entities.Pokemon as Pokemon
from Entities import Move, Message
from Entities.EventType import EventType


class DuelAction:
    def __init__(self, duel_id=None, source=None, initiative=None, target=None, completed: bool = None):
        self.duel_id = duel_id
        self.source = source
        self.initiative = initiative
        self.target = target
        self.completed: bool = completed

    def set_source(self, bot, participant, source_id, initiative):
        raise NotImplementedError

    def perform(self, bot, participant, target_id):
        raise NotImplementedError

    def serialize(self):
        return {'duel_id': self.duel_id,
                'action_type': None,
                'source': self.source,
                'initiative': self.initiative.value if type(self.initiative) == Enum else self.initiative,  # FIXME
                'target': self.target,
                'completed': self.completed}

    @staticmethod
    def deserialize(json):
        try:
            duel_id = json['duel_id']
        except KeyError as e:
            duel_id = None
            logging.error(e)
        try:
            action_type = json['action_type']
        except KeyError as e:
            action_type = None
            logging.error(e)
        try:
            source = json['source']
        except KeyError as e:
            source = None
            logging.error(e)
        try:
            initiative = json['initiative']
        except KeyError as e:
            initiative = None
            logging.error(e)
        try:
            target = json['target']
        except KeyError as e:
            target = None
            logging.error(e)
        try:
            completed = json['completed']
        except KeyError as e:
            completed = None
            logging.error(e)
        if action_type == Constants.ACTION_TYPES.EXCHANGEPOKE:
            return ActionExchangePoke(duel_id=duel_id, source=source, initiative=initiative,
                                      target=target, completed=completed)
        elif action_type == Constants.ACTION_TYPES.ATTACK:
            return ActionAttack(duel_id=duel_id, source=source, initiative=initiative,
                                target=target, completed=completed)
        elif action_type == Constants.ACTION_TYPES.USEITEM:
            return ActionUseItem(duel_id=duel_id, source=source, initiative=initiative,
                                 target=target, completed=completed)


class ActionAttack(DuelAction):
    def set_source(self, bot, participant, attack_id, initiative=None):
        attack_id = int(attack_id)
        poke = DBAccessor.get_pokemon_by_id(participant.pokemon)
        move = next((x for x in poke.moves if x.move_id == attack_id), None)
        if move is not None:
            if move.target not in ['selected-pokemon', 'all-opponents']:
                bot.send_message(chat_id=participant.player_id, text='This attack is not supported yet, '
                                                                     'please choose another one (and blame the devs!)')
                # FIXME
                bot.send_message(chat_id=252269446, text='#target {}'.format(move.target))
                # return
                # raise NotImplementedError('Move type {} is not known'.format(move.target))# specific-move
            else:
                bot.send_message(chat_id=participant.player_id, text='{} will use {} against {}'.format(
                    poke.name, move.name, DBAccessor.get_pokemon_by_id(DBAccessor.get_duel_by_id(
                        self.duel_id).get_counterpart_by_id(participant.player_id).pokemon).name))
            self.completed = True
            self.source = move.move_id
            self.initiative = poke.speed

    # FIXME Target is None
    def perform(self, bot, participant, target_id=None):
        if participant.pokemon is None:
            return '{} has no champion competing in this round!'.format(
                DBAccessor.get_player(participant.player_id).username)
        elif DBAccessor.get_pokemon_by_id(int(participant.pokemon)).health <= 0:
            return '{} has to leave the battlefield'.format(DBAccessor.get_pokemon_by_id(participant.pokemon).name)
        move = Move.Move.get_move(Move.Move.get_move_url(self.source))
        # get target id (which should be none)
        if self.duel_id is None:
            raise ValueError("duel id is none!")
        else:
            duel = DBAccessor.get_duel_by_id(self.duel_id)
        if target_id is not None:
            self.target = target_id
        else:
            if move.target == 'selected-pokemon' or move.target == 'all-opponents':
                self.target = duel.get_counterpart_by_id(participant.player_id).pokemon
                # CHANGEME when multiple champions are on the field
                # elif move.target == 'all-opponents':
                target_id = duel.get_counterpart_by_id(participant.player_id).pokemon
            elif move.target == 'specific-move':
                # TODO
                raise ValueError("specific-move is not supported!")

        target_pokemon = DBAccessor.get_pokemon_by_id(int(self.target))
        if target_pokemon.health <= 0:
            return '{} has no champion competing in this round!'.format(
                DBAccessor.get_player(duel.get_counterpart_by_id(participant.player_id)).username)

        if move.accuracy is None or random.random() < move.accuracy / 100:
            damage = 0
            if move.power is not None:
                if target_pokemon.health - move.power <= 0:
                    # Pokemon sleep now
                    damage = target_pokemon.health
                    target_pokemon.health = 0
                else:
                    damage = move.power
                    target_pokemon.health -= damage

            query = DBAccessor.get_update_query_pokemon(health=target_pokemon.health)
            DBAccessor.update_pokemon(_id=target_id, update=query)
            return '{} retrieved {} damage. {} health left.'.format(target_pokemon.name, damage, target_pokemon.health)
        else:
            return 'Attack missed!'

    def serialize(self):
        super_ser = super().serialize()
        super_ser['action_type'] = Constants.ACTION_TYPES.ATTACK
        super_ser['initiative'] = self.initiative.value if type(self.initiative) == Enum else self.initiative  # FIXME
        return super_ser


class ActionExchangePoke(DuelAction):
    def set_source(self, bot, participant, pokemon_id, initiative=None):
        pokemon_id = int(pokemon_id)
        player = DBAccessor.get_player(participant.player_id)
        champion_id = next((x for x in participant.team if x == pokemon_id), None)
        if champion_id is not None:
            champion = DBAccessor.get_pokemon_by_id(champion_id)
            self.source = champion.poke_id
            self.initiative = Constants.INITIATIVE_LEVEL.CHOOSE_POKE
            self.completed = True
            self.target = participant.player_id
            bot.send_message(chat_id=player.chat_id,
                             text='You nominated {} as your champion!'.format(champion.name))

    def perform(self, bot, participant, target_id=None):
        # TODO: Switch to ID
        result = '{} switches{} to {}'.format(
            DBAccessor.get_player(participant.player_id).username,
            ' from ' + DBAccessor.get_pokemon_by_id(
                participant.pokemon).name if participant.pokemon is not None else '',
            DBAccessor.get_pokemon_by_id(self.source if self.source is not None else 'None').name)
        participant.pokemon = self.source if self.source in participant.team else None
        return result

    def serialize(self):
        super_ser = super().serialize()
        super_ser['action_type'] = Constants.ACTION_TYPES.EXCHANGEPOKE
        super_ser['initiative'] = self.initiative.value if type(self.initiative) == Enum else self.initiative  # FIXME
        return super_ser


class ActionUseItem(DuelAction):
    def set_source(self, bot, participant, item_id, initiative=None):
        raise NotImplementedError  # TODO

    def perform(self, bot, participant, target_id):
        raise NotImplementedError  # TODO

    def serialize(self):
        return {'action_type': Constants.ACTION_TYPES.USEITEM,
                'source': self.source,
                'initiative': self.initiative.value if self.initiative is not None else None,
                'target': self.target,
                'completed': self.completed}


class Participant:
    def __init__(self, player_id: int = None, action: DuelAction = None, team: List[int] = None,
                 team_selection: Message.Message = None, pokemon: int = None):
        self.player_id: int = player_id
        self.action: DuelAction = action
        self.team: List[int] = team
        self.team_selection: Message.Message = team_selection
        self.pokemon: int = pokemon

    def serialize(self):
        return {'player_id': self.player_id,
                'action': self.action.serialize() if self.action is not None else None,
                'team': [i for i in self.team] if self.team is not None else None,
                'team_selection': self.team_selection.serialize_msg() if self.team_selection is not None else None,
                'pokemon': self.pokemon if self.pokemon is not None else None}

    @staticmethod
    def deserialize(json):
        try:
            player_id = json['player_id']
        except KeyError as e:
            player_id = None
            logging.error(e)
        try:
            action = DuelAction.deserialize(
                json['action']
            ) if json['action'] is not None else None
        except KeyError as e:
            action = None
            logging.error(e)
        try:
            team = [i for i in json['team']] if json['team'] is not None else None
        except KeyError as e:
            team = None
            logging.error(e)
        try:
            team_selection = Message.deserialize_msg(
                json['team_selection']) if json['team_selection'] is not None else None
        except KeyError as e:
            team_selection = None
            logging.error(e)
        try:
            pokemon = json['pokemon'] if json['pokemon'] is not None else None
        except KeyError as e:
            pokemon = None
            logging.error(e)
        return Participant(player_id=player_id, action=action, team=team, team_selection=team_selection,
                           pokemon=pokemon)


class Duel(EventType):
    def __init__(self, event_id=None, start_time=None, active=None, round=None,
                 participant_1: Participant = None, participant_2: Participant = None, accepted=None):
        super().__init__(event_id, start_time, active)
        self.round = round
        self.participant_1 = participant_1
        self.participant_2 = participant_2
        self.accepted: bool = accepted

    def serialize(self):
        return {'event_id': self.event_id,
                'start_time': self.start_time,
                'round': self.round,
                'participant_1': self.participant_1.serialize(),
                'participant_2': self.participant_2.serialize(),
                'accepted': self.accepted}

    @staticmethod
    def deserialize(json):
        # FIXME: ugly code
        try:
            event_id = json['event_id']
        except KeyError as e:
            event_id = None
            logging.error(e)
        try:
            start_time = json['start_time']
        except KeyError as e:
            start_time = None
            logging.error(e)
        try:
            active = json['active']
        except KeyError as e:
            active = None
            logging.error(e)
        try:
            round = json['round']
        except KeyError as e:
            round = None
            logging.error(e)
        try:
            participant_1 = Participant.deserialize(
                json['participant_1']
            ) if json['participant_1'] is not None else None
        except KeyError as e:
            participant_1 = None
            logging.error(e)
        try:
            participant_2 = Participant.deserialize(
                json['participant_2']
            ) if json['participant_2'] is not None else None
        except KeyError as e:
            participant_2 = None
            logging.error(e)
        try:
            accepted = json['accepted']
        except KeyError as e:
            accepted = None
            logging.error(e)

        duel = Duel(event_id=event_id,
                    start_time=start_time,
                    active=active,
                    round=round,
                    participant_1=participant_1,
                    participant_2=participant_2,
                    accepted=accepted)
        return duel

    def get_img(self, player_id: int):
        poke1 = DBAccessor.get_pokemon_by_id(self.participant_1.pokemon)
        poke2 = DBAccessor.get_pokemon_by_id(self.participant_2.pokemon)
        if self.participant_1.player_id == player_id:
            return Pokemon.build_pokemon_trade_image(poke1.sprites['back'],
                                                     poke2.sprites['front'])
        elif self.participant_2.player_id == player_id:
            return Pokemon.build_pokemon_trade_image(poke2.sprites['back'],
                                                     poke1.sprites['front'])
        else:
            return None

    def get_participant_by_id(self, participant_id: int):
        return self.participant_1 if participant_id == self.participant_1.player_id else self.participant_2

    def get_counterpart_by_id(self, participant_id: int):
        return self.participant_1 if participant_id != self.participant_1.player_id else self.participant_2

    def update_participant(self, chat_id):
        if chat_id == self.participant_1.player_id:
            query = DBAccessor.get_update_query_duel(participant_1=self.participant_1)
        elif chat_id == self.participant_2.player_id:
            query = DBAccessor.get_update_query_duel(participant_2=self.participant_2)
        else:
            raise AttributeError('Duel Participants incorrect: Duel_id: {}'.format(self.event_id))
        DBAccessor.update_duel(self.event_id, query)
