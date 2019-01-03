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
    def __init__(self, id, name, moves, health, level, types, sprites, height, weight, female, is_shiny):
        self.id = id
        self.name = name
        self.level = level
        self.moves = moves
        self.health = health
        self.types = types
        self.sprites = sprites
        self.weight = weight
        self.height = height
        self.female = female
        self.is_shiny = is_shiny

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
            'height': self.height,
            'female': self.female,
            'is_shiny': self.is_shiny
        }
        return serial


def deserialize_pokemon(json):
    pokemon = Pokemon(id=json['id'],
                      name=json['name'],
                      level=json['level'],
                      moves=json['moves'],
                      health=json['health'],
                      types=json['types'],
                      sprites=json['sprites'],
                      weight=json['weight'],
                      height=json['height'],
                      female=json['female'],
                      is_shiny=json['is_shiny'])
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
    name = poke_json['name']
    is_shiny = True if random.random() > 0.98 else False
    female = True if random.random() > 0.5 else False
    sprites = {}
    ps = poke_json['sprites']

    if not female and not is_shiny:
        sprites = {'front': ps['front_default'], 'back': ps['back_default']}
    elif not female and is_shiny:
        sprites = {'front': ps['front_shiny'] if ps['front_shiny'] is not None else ps['front_default'],
                   'back': ps['back_shiny'] if ps['back_shiny'] is not None else ps['back_default']}
    elif female and not is_shiny:
        sprites = {'front': ps['front_female'] if ps['front_female'] is not None else ps['front_default'],
                   'back': ps['back_female'] if ps['back_female'] is not None else ps['back_default']}
    elif female and is_shiny:
        sprites = {
            'front': ps['front_shiny_female'] if ps['front_shiny_female'] is not None
            else ps['front_shiny'] if ps['front_shiny'] is not None
            else ps['front_default'],
            'back': ps['back_shiny_female'] if ps['back_shiny_female'] is not None
            else ps['back_shiny'] if ps['back_shiny'] is not None
            else ps['back_default']}
    height = poke_json['height']
    weight = poke_json['weight']
    health = level_reference * 1.5
    level = random.randint(max(level_reference - 5, 0), level_reference + 5)
    types = []
    for type in poke_json[u'types']:
        types.append(type[u'type'])
    possible_moves = []
    for move in poke_json[u'moves']:
        move_ = move[u'move']
        move_['level_learned_at'] = move['version_group_details'][0]['level_learned_at']
        if move_['level_learned_at'] <= level:
            possible_moves.append(move_)
    max_moves = 4 if len(possible_moves) > 4 else len(possible_moves)
    moves = random.sample(possible_moves, max_moves)
    pokemon = Pokemon(id=id, name=name, moves=moves, health=health, level=level, types=types,
                      sprites=sprites, height=height, weight=weight, female=female, is_shiny=is_shiny)
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
    alpha = image.convert('RGBA').split()[-1]
    background = Image.open('../res/img/background1.png')
    w, h = background.size
    background = background.crop(((w - h) / 2, 0, w - (w - h) / 2, h))
    background.thumbnail((width_total, height_total), Image.ANTIALIAS)
    background.paste(image, (width * (direction % edge_length), height * int(direction / edge_length)), mask=alpha)
    return background


def build_pokemon_bag_image(pokemon_sprite_list):
    if len(pokemon_sprite_list) is 0:
        return None
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

        alpha = im.convert('RGBA').split()[-1]
        if i % 2 is 0:
            bg = Image.new("RGBA", im.size, (255, 247, 153, 255))
        else:
            bg = Image.new("RGBA", im.size, (226, 215, 74, 255))
        bg.paste(im, mask=alpha)
        new_im.paste(bg, (x_offset, int(i / max_row_len) * max_height))
        x_offset += im.size[0]

    for i in range(max_row_len - (len(pokemon_sprite_list) % max_row_len)):
        if (len(pokemon_sprite_list) + i) % 2 is 0:
            bg = Image.new("RGBA", images[0].size, (255, 247, 153, 255))
        else:
            bg = Image.new("RGBA", images[0].size, (226, 215, 74, 255))
        new_im.paste(bg, (x_offset, int(len(pokemon_sprite_list) / max_row_len) * max_height))
        x_offset += images[0].size[0]

    return new_im


def build_item_bag_image(item_list):
    pass
