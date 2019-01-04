import time
from typing import List

import Pokemon


class Player:
    def __init__(self, chat_id, items=None, pokemon=None, last_encounter=None, in_encounter=None,
                 pokemon_direction=None, catch_message_id=None, catch_pokemon=None, encounters=False):
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

    @classmethod
    def update_player(cls, player, chat_id=None, items=None, pokemon=None, last_encounter=None, in_encounter=None,
                      pokemon_direction=None, catch_message_id=None, catch_pokemon=None, encounters=None):
        return Player(
            chat_id=player.chat_id if chat_id is None else chat_id,
            items=player.items if items is None else items,
            pokemon=player.pokemon if pokemon is None else pokemon,
            last_encounter=player.last_encounter if last_encounter is None else last_encounter,
            in_encounter=player.in_encounter if in_encounter is None else in_encounter,
            pokemon_direction=player.pokemon_direction if pokemon_direction is None else pokemon_direction,
            catch_message_id=player.catch_message_id if catch_message_id is None else catch_message_id,
            catch_pokemon=player.catch_pokemon if catch_pokemon is None else catch_pokemon,
            encounters=player.encounters if encounters is None else encounters
        )


def serialize_player(player: Player):
    serial = {'_id': player.chat_id,
              'items': player.items,
              'pokemon': [i.serialize_pokemon() for i in player.pokemon],
              'last_encounter': player.last_encounter,
              'in_encounter': player.in_encounter,
              'pokemon_direction': player.pokemon_direction,
              'catch_message_id': player.catch_message_id,
              'catch_pokemon': player.catch_pokemon.serialize_pokemon() if player.catch_pokemon is not None else None,
              'encounters': player.encounters}
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
                    json['encounters'])
    return player
