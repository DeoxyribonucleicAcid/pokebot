import logging
import time
from typing import List

import Message as Message
import Pokemon as Pokemon

logger = logging.getLogger(__name__)


class Player:
    def __init__(self, chat_id, username: str = None, friendlist=None, items=None, pokemon=None, pokemon_team=None,
                 last_encounter=None,
                 in_encounter=None, trade_pokemon=None, edit_pokemon_id=None,
                 pokemon_direction=None, nc_msg_state=None, catch_pokemon=None, encounters=False,
                 messages_to_delete=None):
        self.chat_id: int = chat_id
        self.username = None if username is None else username.lower()
        self.friendlist: List[int] = [] if friendlist is None else friendlist
        self.items = {} if items is None else items
        self.pokemon: List[Pokemon.Pokemon] = [] if pokemon is None else pokemon
        self.pokemon_team: List[Pokemon.Pokemon] = [] if pokemon_team is None else pokemon_team

        # Encounter
        self.last_encounter: float = time.time() if last_encounter is None else last_encounter
        self.in_encounter: bool = False if in_encounter is None else in_encounter
        self.pokemon_direction: int = pokemon_direction
        self.nc_msg_state: int = nc_msg_state
        self.catch_pokemon: Pokemon = catch_pokemon
        self.trade_pokemon: Pokemon = trade_pokemon
        self.edit_pokemon_id = edit_pokemon_id
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

    def get_pokemon(self, pokemon_id):
        for pokemon in self.pokemon:
            if pokemon_id == pokemon._id:
                return pokemon
        return None

    def remove_pokemon(self, pokemon_id):
        for i, poke in enumerate(self.pokemon):
            if pokemon_id == poke._id:
                self.pokemon.remove(poke)
                return poke
        return None

    def update_pokemon(self, pokemon: Pokemon):
        for i, poke in enumerate(self.pokemon):
            if pokemon._id == poke._id:
                self.pokemon[i] = pokemon
                return True
        return False


def serialize_player(player: Player):
    serial = {'_id': player.chat_id,
              'username': player.username,
              'firendlist': [i for i in player.friendlist],
              'items': player.items,
              'pokemon': [i.serialize_pokemon() for i in player.pokemon],
              'pokemon_team': [i.serialize_pokemon() for i in player.pokemon_team],
              'last_encounter': player.last_encounter,
              'in_encounter': player.in_encounter,
              'pokemon_direction': player.pokemon_direction,
              'nc_msg_state': player.nc_msg_state,
              'catch_pokemon': player.catch_pokemon.serialize_pokemon() if player.catch_pokemon is not None else None,
              'trade_pokemon': player.trade_pokemon.serialize_pokemon() if player.trade_pokemon is not None else None,
              'edit_pokemon_id': player.edit_pokemon_id,
              'encounters': player.encounters,
              'messages_to_delete': [i.serialize_msg() for i in player.messages_to_delete]}
    return serial


def deserialize_player(json):
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
        in_encounter = json['in_encounter']
    except KeyError as e:
        in_encounter = None
        logging.error(e)
    try:
        pokemon_direction = json['pokemon_direction']
    except KeyError as e:
        pokemon_direction = None
        logging.error(e)
    try:
        nc_msg_state = json['nc_msg_state']
    except KeyError as e:
        nc_msg_state = None
        logging.error(e)
    try:
        catch_pokemon = Pokemon.deserialize_pokemon(
            json['catch_pokemon']
        ) if json['catch_pokemon'] is not None else None
    except KeyError as e:
        catch_pokemon = None
        logging.error(e)
    try:
        trade_pokemon = Pokemon.deserialize_pokemon(
            json['trade_pokemon']
        ) if json['trade_pokemon'] is not None else None
    except KeyError as e:
        trade_pokemon = None
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

    player = Player(chat_id=chat_id,
                    username=username,
                    friendlist=friendlist,
                    items=items,
                    pokemon=pokemon,
                    pokemon_team=pokemon_team,
                    last_encounter=last_encounter,
                    in_encounter=in_encounter,
                    pokemon_direction=pokemon_direction,
                    nc_msg_state=nc_msg_state,
                    catch_pokemon=catch_pokemon,
                    trade_pokemon=trade_pokemon,
                    edit_pokemon_id=edit_pokemon_id,
                    encounters=encounters,
                    messages_to_delete=messages_to_delete)
    return player
