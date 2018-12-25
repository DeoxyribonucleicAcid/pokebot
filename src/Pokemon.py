import json
import logging
import math
import random
import urllib.request
from io import BytesIO

import requests
from PIL import Image

from src.EichState import EichState


class Pokemon:
    def __init__(self, id, name, moves, health, level, types, sprites, height, weight):
        self.id = id
        self.name = name
        self.level = level
        self.moves = moves
        self.health = health
        self.types = types
        self.sprites = sprites
        self.weight = weight
        self.height = height

    def serialize_pokemon(self):
        serial = {
            'id': self.id,
            'name': self.name,
            'level': self.level,
            'moves': self.moves,
            'health': self.health,
            'types': self.types,
            'sprites': self.sprites,
            'weight': self.weight,
            'height': self.height
        }
        return serial


def deserialize_pokemon(json):
    pokemon = Pokemon(json['id'],
                      json['name'],
                      json['level'],
                      json['moves'],
                      json['health'],
                      json['types'],
                      json['sprites'],
                      json['weight'],
                      json['height'])
    return pokemon


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


def get_random_poke(poke_json, level_reference):
    id = poke_json['id']
    moves = []
    for move in poke_json['moves']:
        moves.append(move['move'])
    name = poke_json['name']
    sprites = poke_json['sprites']
    height = poke_json['height']
    weight = poke_json['weight']
    health = level_reference * 1.5
    level = random.randint(max(level_reference - 5, 0), level_reference + 5)
    types = []
    for type in poke_json[u'types']:
        types.append(type[u'type'])
    moves = []
    for move in poke_json[u'moves']:
        move_ = move[u'move']
        move_['level_learned_at'] = move['version_group_details'][0]['level_learned_at']
        moves.append(move_)
    pokemon = Pokemon(id=id, name=name, moves=moves, health=health, level=level,
                      types=types, sprites=sprites, height=height, weight=weight)
    return pokemon


def get_sprite_dir(poke_name):
    return '../res/img/' + poke_name + '.png'


def get_poke_image(sprite):
    try:
        default_sprite = Image.open(BytesIO(requests.get(sprite).content))
        return default_sprite
    except requests.HTTPError as e:
        logging.error(e)


def build_pokemon_catch_img(pokemon_sprite, direction):
    edge_length = 3
    image = get_poke_image(sprite=pokemon_sprite)
    width, height = image.size
    width_total = edge_length * width
    height_total = edge_length * height
    new_im = Image.new('RGBA', (width_total, height_total))
    new_im.paste(image, (width * (direction % edge_length), height * int(direction / edge_length)))
    return new_im


def build_pokemon_bag_image(pokemon_list):
    dir_list = list()
    max_row_len = 4
    for pokemon in pokemon_list:
        dir_list.append(get_sprite_dir(pokemon))

    images = [Image.open(i) for i in dir_list]  # map(Image.open, dir_list)
    widths, heights = zip(*(i.size for i in images))
    max_height = max(heights)
    width = max(widths) * max_row_len if len(images) >= max_row_len else max(widths) * len(images)
    height = max(heights) * (math.ceil(len(images) / max_row_len))
    new_im = Image.new('RGBA', (width, height))

    x_offset = 0
    for i, im in enumerate(images):
        if i % max_row_len is 0:
            x_offset = 0
        new_im.paste(im, (x_offset, int(i / max_row_len) * max_height))
        x_offset += im.size[0]
    return new_im


def build_pokemon_bag_image_dyn(pokemon_sprite_list):
    max_row_len = 4

    images = [get_poke_image(i) for i in pokemon_sprite_list]  # map(Image.open, dir_list)
    widths, heights = zip(*(i.size for i in images))
    max_height = max(heights)
    width = max(widths) * max_row_len if len(images) >= max_row_len else max(widths) * len(images)
    height = max(heights) * (math.ceil(len(images) / max_row_len))
    new_im = Image.new('RGBA', (width, height))

    x_offset = 0
    for i, im in enumerate(images):
        if i % max_row_len is 0:
            x_offset = 0
        new_im.paste(im, (x_offset, int(i / max_row_len) * max_height))
        x_offset += im.size[0]
    return new_im


def build_item_bag_image(item_list):
    pass
