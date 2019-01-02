import src.Player as Player
from src.EichState import EichState


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

# import random
# from src import Pokemon
# from pprint import pprint
# from src import MessageBuilder
#
# MessageBuilder.prepare_environment()
# pokemon_name = EichState.names_dict['pokenames'][
#     random.choice(list(EichState.names_dict['pokenames'].keys()))]
# pokemon_direction = random.randint(0, 8)
# pokemon = Pokemon.get_random_poke(Pokemon.get_pokemon_json(pokemon_name), 10)
# player = Player.Player(chat_id=12345678, items={}, pokemon=[pokemon],
#                        last_encounter=23456789.643653, in_encounter=False, pokemon_direction=None,
#                        catch_message_id=None, catch_pokemon=None, encounters=False)
#
# delete_player(12345678)
#
# insert_new_player(player=player)
#
# pprint(get_player(12345678))
#
# update_player(12345678, {'$set': {'encounters': True}})
#
# pprint(get_player(12345678))
# delete_player(12345678)
