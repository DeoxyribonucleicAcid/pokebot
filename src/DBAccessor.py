import logging
from typing import List

import src.EichState as EichState
from Entities import Pokemon, Player, Message, Duel

logger = logging.getLogger(__name__)


def insert_new_player(player: Player.Player):
    player_serialized = player.serialize()
    return EichState.EichState.player_col.insert_one(player_serialized)


def insert_new_duel(duel: Duel.Duel):
    duel_serialized = duel.serialize()
    return EichState.EichState.duel_col.insert_one(duel_serialized)


def get_player(_id: int):
    query = {"_id": _id}
    result = EichState.EichState.player_col.find(query)
    if result.count() is 1:
        return Player.Player.deserialize_player(result.next())
    else:
        return None


def get_player_by_name(username):
    query = {'username': username}
    result = EichState.EichState.player_col.find(query)
    if result.count() is 1:
        return Player.Player.deserialize_player(result.next())
    else:
        return None


def delete_player(_id: int):
    query = {"_id": int(_id)}
    return EichState.EichState.player_col.delete_one(query)


def delete_duel(_id: int):
    query = {"event_id": int(_id)}
    return EichState.EichState.duel_col.delete_one(query)


def update_player(_id: int, update: dict):
    query = {"_id": int(_id)}
    EichState.EichState.player_col.update_one(query, update)


def update_duel(_id: int, update: dict):
    query = {"event_id": int(_id)}
    EichState.EichState.duel_col.update_one(query, update)


def get_encounter_players_cursor():
    query = {'encounters': True}
    cursor = EichState.EichState.player_col.find(query)
    result = []
    for player in cursor:
        result.append(Player.Player.deserialize_player(player))
    return result


def get_duel_by_id(event_id: int):
    query = {"event_id": int(event_id)}
    result = EichState.EichState.duel_col.find(query)
    if result.count() is 1:
        return Duel.Duel.deserialize(result.next())
    else:
        return None


def get_duel_by_participants(participant1_id: int, participant2_id: int = None):
    participant1_id, participant2_id = int(participant1_id), int(participant2_id)

    #   {'$or': [{'$and': [{'participant_1.player_id': 252269446}, {'participant_2.player_id': 111146123}]},
    #   {'$and': [{'participant_2.player_id': 252269446}, {'participant_1.player_id': 111146123}]}]}

    # query = {'$or': [{'$and': [{'participant_1.player_id': 252269446},
    #                      {'participant_2.player_id': 111146123}]},
    #            {'$and': [{'participant_2.player_id': 252269446},
    #                  {'participant_1.player_id': 111146123}]}]}

    query = {'$or': [{'$and': [{'participant_1.player_id': participant1_id}]},
                     {'$and': [{'participant_2.player_id': participant1_id}]}]}
    if participant2_id is not None:
        query['$or'][0]['$and'].append({'participant_2.player_id': participant2_id})
        query['$or'][1]['$and'].append({'participant_1.player_id': participant2_id})
    result = EichState.EichState.duel_col.find(query)
    if result.count() is 1:
        return Duel.Duel.deserialize(result.next())
    else:
        return None


def insert_new_pokemon(poke: Pokemon.Pokemon):
    poke_serialized = poke.serialize()
    return EichState.EichState.poke_col.insert_one(poke_serialized)


def get_pokemon_by_id(target_id):
    query = {"_id": target_id}
    result = EichState.EichState.poke_col.find(query)
    if result.count() is 1:
        return Pokemon.deserialize_pokemon(result.next())
    else:
        return None


def delete_pokemon(_id: int):
    query = {"_id": _id}
    return EichState.EichState.poke_col.delete_one(query)


def update_pokemon(_id: int, update: dict):
    query = {"_id": _id}
    EichState.EichState.poke_col.update_one(query, update)


def get_update_query_player(chat_id=None, username=None, friendlist=None, items=None,
                            pokemon: List[Pokemon.Pokemon] = None,
                            pokemon_team: List[Pokemon.Pokemon] = None,
                            last_encounter=None, nc_msg_state=None,
                            edit_pokemon_id=None, encounters=None,
                            messages_to_delete: List[Message.Message] = None,
                            encounter=None, trade=None, duels=None):
    query = {'$set': {}, '$unset': {}}
    if chat_id is not None: query['$set']['chat_id'] = chat_id
    if username is not None: query['$set']['username'] = username
    if friendlist is not None: query['$set']['friendlist'] = [i for i in friendlist]
    if items is not None: query['$set']['items'] = items
    if pokemon is not None: query['$set']['pokemon'] = [i for i in pokemon]
    if pokemon_team is not None: query['$set']['pokemon_team'] = [i for i in pokemon_team]
    if last_encounter is not None: query['$set']['last_encounter'] = last_encounter
    if nc_msg_state is not None: query['$set']['nc_msg_state'] = nc_msg_state.value
    if edit_pokemon_id is not None: query['$set']['edit_pokemon_id'] = edit_pokemon_id
    if encounters is not None: query['$set']['encounters'] = encounters
    if messages_to_delete is not None: query['$set']['messages_to_delete'] = [i.serialize_msg() for i in
                                                                              messages_to_delete]
    if encounter is not None: query['$set']['encounter'] = encounter.serialize()
    if trade is not None: query['$set']['trade'] = trade.serialize()
    if duels is not None: query['$set']['duels'] = [i for i in duels]

    query['$unset']['catch_message_id'] = 1
    query['$unset']['catch_pokemon'] = 1
    query['$unset']['trade_pokemon'] = 1
    query['$unset']['pokemon_direction'] = 1
    query['$unset']['in_encounter'] = 1
    return query


def get_update_query_duel(participant_1: Duel.Participant = None, participant_2: Duel.Participant = None):
    query = {'$set': {}}
    if participant_1 is not None: query['$set']['participant_1'] = participant_1.serialize()
    if participant_2 is not None: query['$set']['participant_2'] = participant_2.serialize()
    return query


def get_update_query_pokemon(
        pokedex_id=None, name=None, moves=None, health=None, level=None, types=None, sprites=None,
        height=None, weight=None, female=None, is_shiny=None, poke_id=None, max_health=None,
        speed=None,
        special_defense=None,
        special_attack=None,
        defense=None,
        attack=None
):
    query = {'$set': {}}

    if pokedex_id is not None: query['$set']['pokedex_id'] = pokedex_id
    if name is not None: query['$set']['name'] = name
    if moves is not None: query['$set']['moves'] = [i for i in moves]
    if health is not None: query['$set']['health'] = health
    if level is not None: query['$set']['level'] = level
    if types is not None: query['$set']['types'] = [i for i in types]
    if sprites is not None: query['$set']['sprites'] = [i for i in sprites]
    if height is not None: query['$set']['height'] = height
    if weight is not None: query['$set']['weight'] = weight
    if female is not None: query['$set']['female'] = female
    if is_shiny is not None: query['$set']['is_shiny'] = is_shiny
    if poke_id is not None: query['$set']['poke_id'] = poke_id
    if max_health is not None: query['$set']['max_health'] = max_health
    if speed is not None: query['$set']['speed'] = speed
    if special_defense is not None: query['$set']['special_defense'] = special_defense
    if special_attack is not None: query['$set']['special_attack'] = special_attack
    if defense is not None: query['$set']['defense'] = defense
    if attack is not None: query['$set']['attack'] = attack
    return query
