import logging

import Constants
import DBAccessor
import Entities.Pokemon as Pokemon
from Entities.EventType import EventType


class DuelAction:
    def __init__(self, source=None, initiative=None, target=None):
        self.source = source
        self.initiative = initiative
        self.target = target

    def set_source(self, player_id: int, source_id, initiative):
        raise NotImplementedError

    def perform(self, target):
        raise NotImplementedError

    def serialize(self):
        return {'source': self.source,
                'initiative': self.initiative,
                'target': self.target}

    @staticmethod
    def deserialize(json):
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
        return DuelAction(source=source, initiative=initiative, target=target)


class ActionAttack(DuelAction):
    def set_source(self, player_id: int, attack_id, initiative):
        raise NotImplementedError

    def perform(self, target):
        raise NotImplementedError


class ActionExchangePoke(DuelAction):
    def set_source(self, player_id: int, pokemon_id, initiative):
        player = DBAccessor.get_player(player_id)
        champion = next((x for x in player.pokemon_team if x._id == pokemon_id), None)
        if champion is not None:
            self.source = champion
            self.initiative = Constants.INITIATIVE_LEVEL.CHOOSE_POKE

    def perform(self, target):
        raise NotImplementedError


class ActionUseItem(DuelAction):
    def set_source(self, player_id: int, item_id, initiative):
        raise NotImplementedError

    def perform(self, target):
        raise NotImplementedError


class Participant:
    def __init__(self, player_id: int = None, action: DuelAction = None, pokemon: Pokemon.Pokemon = None):
        self.player_id: int = player_id
        self.action: DuelAction = action
        self.pokemon: Pokemon.Pokemon = pokemon

    def serialize(self):
        return {'player_id': self.player_id,
                'action': self.action.serialize(),
                'pokemon': self.pokemon}

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
