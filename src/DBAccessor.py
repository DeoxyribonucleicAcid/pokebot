import logging
from typing import List

from src import Player, Message, Pokemon, EichState

logger = logging.getLogger(__name__)

def insert_new_player(player: Player.Player):
    player_serialized = Player.serialize_player(player)
    return EichState.EichState.player_col.insert_one(player_serialized)


def get_player(_id: int):
    query = {"_id": _id}
    result = EichState.EichState.player_col.find(query)
    if result.count() is 1:
        return Player.deserialize_player(result.next())
    else:
        return None


def delete_player(_id: int):
    query = {"_id": _id}
    return EichState.EichState.player_col.delete_one(query)


def update_player(_id: int, update: dict):
    query = {"_id": _id}
    EichState.EichState.player_col.update_one(query, update)


def get_encounter_players_cursor():
    query = {'encounters': True}
    cursor = EichState.EichState.player_col.find(query)
    result = []
    for player in cursor:
        result.append(Player.deserialize_player(player))
    return result


def get_update_query(chat_id=None, items=None, pokemon: List[Pokemon.Pokemon] = None, last_encounter=None,
                     in_encounter=None, pokemon_direction=None, catch_message_id=None, catch_pokemon=None,
                     encounters=None, messages_to_delete: List[Message.Message] = None):
    query = {'$set': {}}
    if chat_id is not None: query['$set']['chat_id'] = chat_id
    if items is not None: query['$set']['items'] = items
    if pokemon is not None: query['$set']['pokemon'] = [i.serialize_pokemon() for i in pokemon]
    if last_encounter is not None: query['$set']['last_encounter'] = last_encounter
    if in_encounter is not None: query['$set']['in_encounter'] = in_encounter
    if pokemon_direction is not None: query['$set']['pokemon_direction'] = pokemon_direction
    if catch_message_id is not None: query['$set']['catch_message_id'] = catch_message_id
    if catch_pokemon is not None: query['$set']['catch_pokemon'] = catch_pokemon.serialize_pokemon()
    if encounters is not None: query['$set']['encounters'] = encounters
    if messages_to_delete is not None: query['$set']['messages_to_delete'] = [i.serialize_msg() for i in
                                                                              messages_to_delete]
    return query
