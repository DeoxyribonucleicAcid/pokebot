import logging

from Entities import Pokemon as Pokemon

logger = logging.getLogger(__name__)


class Encounter:
    def __init__(self, encounter_id=None,
                 pokemon_direction=None, pokemon=None):
        self.encounter_id = id(self) if encounter_id is None else encounter_id
        self.pokemon_direction: int = pokemon_direction
        self.pokemon: Pokemon = pokemon

    def serialize(self):
        serial = {'encounter_id': self.encounter_id,
                  'pokemon_direction': self.pokemon_direction,
                  'pokemon': self.pokemon.serialize_pokemon() if self.pokemon is not None else None}
        return serial

    @staticmethod
    def deserialize(json):
        # FIXME: ugly code
        try:
            encounter_id = json['encounter_id']
        except KeyError as e:
            encounter_id = None
            logging.error(e)
        try:
            pokemon_direction = json['pokemon_direction']
        except KeyError as e:
            pokemon_direction = None
            logging.error(e)
        try:
            pokemon = Pokemon.deserialize_pokemon(
                json['pokemon']
            ) if json['pokemon'] is not None else None
        except KeyError as e:
            pokemon = None
            logging.error(e)

        encounter = Encounter(encounter_id=encounter_id,
                              pokemon_direction=pokemon_direction,
                              pokemon=pokemon)
        return encounter
