import json
import logging
import urllib.request

from src.EichState import EichState


class Pokemon:
    def __init__(self, id, name, attacks, health, level):
        self.id = id
        self.name = name
        self.level = level
        self.attacks = attacks
        self.health = health


def get_pokemon_json(name):
    name = name.lower()
    pokeurl = EichState.url + 'pokemon/' + name + '/'
    try:
        poke_response = EichState.opener.open(pokeurl)
    except urllib.request.HTTPError as e:
        logging.error('Pokemon not found: ' + '\n' + pokeurl)
        raise e
    poke_json = json.load(poke_response)
    return poke_json


def get_random_poke(poke_json):
    pokemon = Pokemon(None, None, None, None, None)
    # pprint(poke_json)
    id = poke_json['id']
    moves = []
    for move in poke_json['moves']:
        moves.append(move['move'])
    name = poke_json['name']
    sprites = poke_json['sprites']
    height = poke_json['height']
    weight = poke_json['weight']
    types = []
    for type in poke_json[u'types']: types.append(type[u'type'])
    return pokemon
