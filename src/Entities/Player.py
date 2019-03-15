import logging
import time
from typing import List

from Entities import Pokemon as Pokemon, Message as Message
from Entities.Encounter import Encounter
from Entities.Trade import Trade

logger = logging.getLogger(__name__)


class Player:
    def __init__(self, chat_id, username: str = None, friendlist=None, items=None, pokemon=None, pokemon_team=None,
                 last_encounter=None, edit_pokemon_id=None, nc_msg_state=None, encounters=False,
                 messages_to_delete=None, encounter=None, trade=None, duels=None):
        self.chat_id: int = chat_id
        self.username = username.lower() if username is not None else None
        self.friendlist: List[int] = [] if friendlist is None else friendlist
        self.items = {} if items is None else items
        self.pokemon: List[Pokemon.Pokemon] = [] if pokemon is None else pokemon
        self.pokemon_team: List[Pokemon.Pokemon] = [] if pokemon_team is None else pokemon_team

        self.nc_msg_state: int = nc_msg_state
        self.edit_pokemon_id = edit_pokemon_id
        self.messages_to_delete: List[Message.Message] = [] if messages_to_delete is None else messages_to_delete

        self.encounters: bool = encounters
        self.last_encounter: float = time.time() if last_encounter is None else last_encounter
        self.encounter: Encounter = encounter
        self.trade: Trade = trade

        self.duels: List[int] = [] if duels is None else duels

    def get_messages(self, identifier: str):
        return [i for i in self.messages_to_delete if i._title == identifier]

    def delete_message_from_list(self, msg_id):
        for i in self.messages_to_delete:
            if i._id == msg_id:
                self.messages_to_delete.remove(i)
                return True
        return False

    def get_pokemon(self, pokemon_id):
        for pokemon in self.pokemon:
            if pokemon_id == pokemon._id:
                return pokemon
        return None

    def remove_pokemon(self, pokemon_id):
        # Idea: next((poke for poke in self.pokemon if poke._id == pokemon_id), None)
        for i, poke in enumerate(self.pokemon):
            if pokemon_id == poke._id:
                self.pokemon.remove(poke)
                logger.debug('{} was removed from {}\'s pokemon list'.format(pokemon_id, self.chat_id))
                return poke
        return None

    def update_pokemon(self, pokemon: Pokemon):
        for i, poke in enumerate(self.pokemon):
            if pokemon._id == poke._id:
                self.pokemon[i] = pokemon
                return True
        return False

    def serialize(self):
        serial = {'_id': self.chat_id,
                  'username': self.username,
                  'firendlist': [i for i in self.friendlist],
                  'items': self.items,
                  'pokemon': [i.serialize() for i in self.pokemon],
                  'pokemon_team': [i.serialize() for i in self.pokemon_team],
                  'last_encounter': self.last_encounter,
                  'nc_msg_state': self.nc_msg_state,
                  'edit_pokemon_id': self.edit_pokemon_id,
                  'encounters': self.encounters,
                  'messages_to_delete': [i.serialize_msg() for i in self.messages_to_delete],
                  'encounter': self.encounter.serialize() if self.encounter is not None else None,
                  'trade': self.trade.serialize() if self.trade is not None else None,
                  'duels': [i.serialize() for i in self.duels]}
        return serial

    @staticmethod
    def deserialize_player(json):
        # FIXME: ugly code
        try:
            chat_id = json['_id']
        except KeyError as e:
            chat_id = None
            logging.error(e)
        try:
            username = json['username']
        except KeyError as e:
            username = None
            logging.error(e)
        try:
            friendlist = [i for i in json['friendlist']]
        except KeyError as e:
            friendlist = None
            logging.error(e)
        try:
            items = json['items']
        except KeyError as e:
            items = None
            logging.error(e)
        try:
            pokemon = [Pokemon.deserialize_pokemon(i) for i in json['pokemon']]
        except KeyError as e:
            pokemon = None
            logging.error(e)
        try:
            pokemon_team = [Pokemon.deserialize_pokemon(i) for i in json['pokemon_team']]
        except KeyError as e:
            pokemon_team = None
            logging.error(e)
        try:
            last_encounter = json['last_encounter']
        except KeyError as e:
            last_encounter = None
            logging.error(e)
        try:
            nc_msg_state = json['nc_msg_state']
        except KeyError as e:
            nc_msg_state = None
            logging.error(e)
        try:
            edit_pokemon_id = json['edit_pokemon_id']
        except KeyError as e:
            edit_pokemon_id = None
            logging.error(e)
        try:
            encounters = json['encounters']
        except KeyError as e:
            encounters = None
            logging.error(e)
        try:
            messages_to_delete = [Message.deserialize_msg(i) for i in json['messages_to_delete']]
        except KeyError as e:
            messages_to_delete = None
            logging.error(e)
        try:
            encounter = Encounter.deserialize(json['encounter']) if json['encounter'] is not None else None
        except KeyError as e:
            encounter = None
            logging.error(e)
        try:
            trade = Trade.deserialize(json['trade']) if json['trade'] is not None else None
        except KeyError as e:
            trade = None
            logging.error(e)
        try:
            duels = [i for i in json['duels']]
        except KeyError as e:
            duels = None
            logging.error(e)

        player = Player(chat_id=chat_id,
                        username=username,
                        friendlist=friendlist,
                        items=items,
                        pokemon=pokemon,
                        pokemon_team=pokemon_team,
                        last_encounter=last_encounter,
                        nc_msg_state=nc_msg_state,
                        edit_pokemon_id=edit_pokemon_id,
                        encounters=encounters,
                        messages_to_delete=messages_to_delete,
                        encounter=encounter,
                        trade=trade,
                        duels=duels)
        return player
