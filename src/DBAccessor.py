import Player
from EichState import EichState


def insert_new_player(player: Player.Player):
    player_serialized = Player.serialize_player(player)
    return EichState.player_col.insert_one(player_serialized)


def get_player(_id: int):
    query = {"_id": _id}
    result = EichState.player_col.find(query)
    if result.count() is 1:
        return Player.deserialize_player(result.next())
    else:
        return None


def delete_player(_id: int):
    query = {"_id": _id}
    return EichState.player_col.delete_one(query)


def update_player(_id: int, update: dict):
    query = {"_id": _id}
    EichState.player_col.update_one(query, update)


def get_encounter_players_cursor():
    query = {'encounters': True}
    cursor = EichState.player_col.find(query)
    result = []
    for player in cursor:
        result.append(Player.deserialize_player(player))
    print('Found ' + str(cursor.count()) + ' active players')
    return result


def get_update_query(chat_id=None, items=None, pokemon=None, last_encounter=None, in_encounter=None,
                     pokemon_direction=None, catch_message_id=None, catch_pokemon=None, encounters=None):
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
    return query
