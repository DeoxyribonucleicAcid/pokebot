import logging
import time
from typing import List

import src.Message as Message
import src.Pokemon as Pokemon

logger = logging.getLogger(__name__)


class Player:
    def __init__(self, chat_id, items=None, pokemon=None, last_encounter=None, in_encounter=None,
                 pokemon_direction=None, catch_message_id=None, catch_pokemon=None, encounters=False,
                 messages_to_delete=None):
        self.chat_id: int = chat_id
        self.items = {} if items is None else items
        self.pokemon: List[Pokemon.Pokemon] = [] if pokemon is None else pokemon

        # Encounter
        self.last_encounter: float = time.time() if last_encounter is None else last_encounter
        self.in_encounter: bool = False if in_encounter is None else in_encounter
        self.pokemon_direction: int = pokemon_direction
        self.catch_message_id: int = catch_message_id
        self.catch_pokemon: Pokemon = catch_pokemon
        self.encounters: bool = encounters
        self.messages_to_delete: List[Message.Message] = [] if messages_to_delete is None else messages_to_delete

    def get_messages(self, identifier: str):
        return [i for i in self.messages_to_delete if i._title == identifier]

    def delete_message_from_list(self, msg_id):
        for i in self.messages_to_delete:
            if i._id == msg_id:
                self.messages_to_delete.remove(i)
                return True
        return False


def serialize_player(player: Player):
    serial = {'_id': player.chat_id,
              'items': player.items,
              'pokemon': [i.serialize_pokemon() for i in player.pokemon],
              'last_encounter': player.last_encounter,
              'in_encounter': player.in_encounter,
              'pokemon_direction': player.pokemon_direction,
              'catch_message_id': player.catch_message_id,
              'catch_pokemon': player.catch_pokemon.serialize_pokemon() if player.catch_pokemon is not None else None,
              'encounters': player.encounters,
              'messages_to_delete': [i.serialize_msg() for i in player.messages_to_delete]}
    return serial


def deserialize_player(json):
    player = Player(json['_id'],
                    json['items'],
                    [Pokemon.deserialize_pokemon(i) for i in json['pokemon']],
                    json['last_encounter'],
                    json['in_encounter'],
                    json['pokemon_direction'],
                    json['catch_message_id'],
                    Pokemon.deserialize_pokemon(json['catch_pokemon']) if json['catch_pokemon'] is not None else None,
                    json['encounters'],
                    [Message.deserialize_msg(i) for i in json['messages_to_delete']])
    return player
