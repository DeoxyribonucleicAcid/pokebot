import logging

import Constants
import DBAccessor
import Entities.Pokemon as Pokemon
from Entities.EventType import EventType


class DuelAction:
    def __init__(self, source=None, initiative=None, target=None, completed: bool = None):
        self.source = source
        self.initiative = initiative
        self.target = target
        self.completed: bool = completed

    def set_source(self, bot, player_id: int, source_id, initiative):
        raise NotImplementedError

    def perform(self, bot, target_id):
        raise NotImplementedError

    def serialize(self):
        return {'action_type': None,
                'source': self.source,
                'initiative': self.initiative.value if self.initiative is not None else None,
                'target': self.target,
                'completed': self.completed}

    @staticmethod
    def deserialize(json):
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
            return ActionExchangePoke(source=source, initiative=initiative, target=target, completed=completed)
        elif action_type == Constants.ACTION_TYPES.ATTACK:
            return ActionAttack(source=source, initiative=initiative, target=target, completed=completed)
        elif action_type == Constants.ACTION_TYPES.USEITEM:
            return ActionUseItem(source=source, initiative=initiative, target=target, completed=completed)


class ActionAttack(DuelAction):
    def set_source(self, bot, player_id: int, attack_id, initiative):
        raise NotImplementedError  # TODO

    def perform(self, bot, target_id):
        raise NotImplementedError  # TODO

    def serialize(self):
        return {'action_type': Constants.ACTION_TYPES.ATTACK,
                'source': self.source,
                'initiative': self.initiative.value if self.initiative is not None else None,
                'target': self.target,
                'completed': self.completed}


class ActionExchangePoke(DuelAction):
    def set_source(self, bot, player_id: int, pokemon_id, initiative=None):
        pokemon_id = int(pokemon_id)
        player = DBAccessor.get_player(player_id)
        champion = next((x for x in player.pokemon_team if x._id == pokemon_id), None)
        if champion is not None:
            self.source = champion._id
            self.initiative = Constants.INITIATIVE_LEVEL.CHOOSE_POKE
            self.completed = True
            bot.send_message(chat_id=player.chat_id,
                             text='You nominated {} as your champion!'.format(champion.name))

    def perform(self, bot, target_id):
        raise NotImplementedError

    def serialize(self):
        return {'action_type': Constants.ACTION_TYPES.EXCHANGEPOKE,
                'source': self.source,
                'initiative': self.initiative.value if self.initiative is not None else None,
                'target': self.target,
                'completed': self.completed}


class ActionUseItem(DuelAction):
    def set_source(self, bot, player_id: int, item_id, initiative):
        raise NotImplementedError  # TODO

    def perform(self, bot, target_id):
        raise NotImplementedError  # TODO

    def serialize(self):
        return {'action_type': Constants.ACTION_TYPES.USEITEM,
                'source': self.source,
                'initiative': self.initiative.value if self.initiative is not None else None,
                'target': self.target,
                'completed': self.completed}


class Participant:
    def __init__(self, player_id: int = None, action: DuelAction = None, pokemon: Pokemon.Pokemon = None):
        self.player_id: int = player_id
        self.action: DuelAction = action
        self.pokemon: Pokemon.Pokemon = pokemon

    def serialize(self):
        return {'player_id': self.player_id,
                'action': self.action.serialize() if self.action is not None else None,
                'pokemon': self.pokemon.serialize() if self.pokemon is not None else None}

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
            pokemon = Pokemon.deserialize_pokemon(
                json['pokemon']
            ) if json['pokemon'] is not None else None
        except KeyError as e:
            pokemon = None
            logging.error(e)
        return Participant(player_id=player_id, action=action, pokemon=pokemon)


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
        if self.participant_1.player_id == player_id:
            return Pokemon.build_pokemon_trade_image(self.participant_1.pokemon.sprites['back'],
                                                     self.participant_2.pokemon.sprites['front'])
        elif self.participant_2.player_id == player_id:
            return Pokemon.build_pokemon_trade_image(self.participant_2.pokemon.sprites['back'],
                                                     self.participant_1.pokemon.sprites['front'])
        else:
            return None

    def get_participant_by_id(self, participant_id: int):
        return self.participant_1 if participant_id == self.participant_1.player_id else self.participant_2

    def get_counterpart_by_id(self, participant_id: int):
        return self.participant_1 if participant_id != self.participant_1.player_id else self.participant_2
