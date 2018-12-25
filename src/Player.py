import time

from src import Pokemon


class Player:
    def __init__(self, chat_id, items=None, pokemon=None, last_encounter=None, in_encounter=None,
                 pokemon_direction=None, catch_message_id=None, catch_pokemon=None):
        self.chat_id = chat_id
        self.items = {} if items is None else items
        self.pokemon = [] if pokemon is None else pokemon

        # Encounter
        self.last_encounter = time.time() if last_encounter is None else last_encounter
        self.in_encounter = False if in_encounter is None else in_encounter
        self.pokemon_direction = pokemon_direction
        self.catch_message_id = catch_message_id
        self.catch_pokemon = catch_pokemon

    def serialize_player(self):
        serial = {'chat_id': self.chat_id,
                  'items': self.items,
                  'pokemon': [i.serialize_pokemon() for i in self.pokemon],
                  'last_encounter': self.last_encounter,
                  'in_encounter': self.in_encounter,
                  'pokemon_direction': self.pokemon_direction,
                  'catch_message_id': self.catch_message_id,
                  'catch_pokemon': self.catch_pokemon.serialize_pokemon() if self.catch_pokemon is not None else None}
        return serial


def deserialize_player(json):
    player = Player(json['chat_id'],
                    json['items'],
                    [Pokemon.deserialize_pokemon(i) for i in json['pokemon']],
                    json['last_encounter'],
                    json['in_encounter'],
                    json['pokemon_direction'],
                    json['catch_message_id'],
                    Pokemon.deserialize_pokemon(json['catch_pokemon']) if json['catch_pokemon'] is not None else None)
    return player
