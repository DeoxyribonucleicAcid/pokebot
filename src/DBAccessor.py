import logging
from typing import List

import src.EichState as EichState
from Entities import Pokemon, Player, Message

logger = logging.getLogger(__name__)


def insert_new_player(player: Player.Player):
    player_serialized = player.serialize()
    return EichState.EichState.player_col.insert_one(player_serialized)


def get_player(_id: int):
    query = {"_id": _id}
    result = EichState.EichState.player_col.find(query)
    if result.count() is 1:
        return Player.Player.deserialize_player(result.next())
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
        result.append(Player.Player.deserialize_player(player))
    return result


def get_update_query(chat_id=None, username=None, friendlist=None, items=None, pokemon: List[Pokemon.Pokemon] = None,
                     pokemon_team=None, last_encounter=None, nc_msg_state=None, edit_pokemon_id=None, encounters=None,
                     messages_to_delete: List[Message.Message] = None, encounter=None, trade=None):
    query = {'$set': {}, '$unset': {}}
    if chat_id is not None: query['$set']['chat_id'] = chat_id
    if username is not None: query['$set']['username'] = username
    if friendlist is not None: query['$set']['friendlist'] = [i for i in friendlist]
    if items is not None: query['$set']['items'] = items
    if pokemon is not None: query['$set']['pokemon'] = [i.serialize_pokemon() for i in pokemon]
    if pokemon_team is not None: query['$set']['pokemon_team'] = [i.serialize_pokemon() for i in pokemon_team]
    if last_encounter is not None: query['$set']['last_encounter'] = last_encounter
    if nc_msg_state is not None: query['$set']['nc_msg_state'] = nc_msg_state.value
    if edit_pokemon_id is not None: query['$set']['edit_pokemon_id'] = edit_pokemon_id
    if encounters is not None: query['$set']['encounters'] = encounters
    if messages_to_delete is not None: query['$set']['messages_to_delete'] = [i.serialize_msg() for i in
                                                                              messages_to_delete]
    if encounter is not None: query['$set']['encounter'] = encounter.serialize()
    if trade is not None: query['$set']['trade'] = trade.serialize()

    query['$unset']['catch_message_id'] = 1
    query['$unset']['catch_pokemon'] = 1
    query['$unset']['trade_pokemon'] = 1
    query['$unset']['pokemon_direction'] = 1
    query['$unset']['in_encounter'] = 1
    return query


def get_player_by_name(username):
    query = {'username': username}
    result = EichState.EichState.player_col.find(query)
    if result.count() is 1:
        return Player.Player.deserialize_player(result.next())
    else:
        return None
