import json
import logging
import os
import random
import urllib.request
from io import BytesIO
from typing import List

import math
import requests
from PIL import Image

from src.EichState import EichState

logger = logging.getLogger(__name__)


class Pokemon:
    def __init__(self, pokedex_id=None, name=None, moves=None, health=None, level=None, types=None, sprites=None,
                 height=None, weight=None, female=None, is_shiny=None, poke_id=None, max_health=None,
                 speed=None,
                 special_defense=None,
                 special_attack=None,
                 defense=None,
                 attack=None
                 ):
        self.poke_id = id(self) if poke_id is None else poke_id
        self.pokedex_id: int = pokedex_id
        self.name: str = name
        self.level: int = level
        self.moves: List[dict] = moves if moves is not None else []
        self.types: List[dict] = types if types is not None else []
        self.sprites: dict = sprites if sprites is not None else {'front': None, 'back': None}
        self.weight: int = weight
        self.height: int = height
        self.female: bool = female
        self.is_shiny: bool = is_shiny

        # BASE-STATS
        self.speed = speed
        self.special_defense = special_defense
        self.special_attack = special_attack
        self.defense = defense
        self.attack = attack
        self.health: float = health if health is not None else 0
        self.max_health: float = max_health if max_health is not None else 0

    def serialize(self):
        serial = {
            '_id': self.poke_id,
            'pokedex_id': self.pokedex_id,
            'name': self.name,
            'level': self.level,
            'moves': self.moves,
            'health': self.health,
            'max_health': self.max_health,
            'types': self.types,
            'sprites': self.sprites,
            'weight': self.weight,
            'height': self.height,
            'female': self.female,
            'is_shiny': self.is_shiny,
            'speed ': self.speed,
            'special_defense ': self.special_defense,
            'special_attack ': self.special_attack,
            'defense ': self.defense,
            'attack ': self.attack
        }
        return serial


def deserialize_pokemon(json):
    try:
        poke_id = json['_id']
    except KeyError as e:
        poke_id = None
        logging.error(e)
    try:
        pokedex_id = json['pokedex_id']
    except KeyError as e:
        try:
            pokedex_id = json['id']
        except KeyError as f:
            pokedex_id = None
            logging.error(e, f)
    try:
        name = json['name']
    except KeyError as e:
        name = None
        logging.error(e)
    try:
        level = json['level']
    except KeyError as e:
        level = None
        logging.error(e)
    try:
        moves = json['moves']
    except KeyError as e:
        moves = None
        logging.error(e)
    try:
        types = json['types']
    except KeyError as e:
        types = None
        logging.error(e)
    try:
        sprites = json['sprites']
    except KeyError as e:
        sprites = None
        logging.error(e)
    try:
        weight = json['weight']
    except KeyError as e:
        weight = None
        logging.error(e)
    try:
        height = json['height']
    except KeyError as e:
        height = None
        logging.error(e)
    try:
        female = json['female']
    except KeyError as e:
        female = None
        logging.error(e)
    try:
        is_shiny = json['is_shiny']
    except KeyError as e:
        is_shiny = None
        logging.error(e)
    # BASE STATS

    try:
        speed = json['speed']
    except KeyError as e:
        speed = None
        logging.error(e)
    try:
        special_defense = json['special_defense']
    except KeyError as e:
        special_defense = None
        logging.error(e)
    try:
        special_attack = json['special_attack']
    except KeyError as e:
        special_attack = None
        logging.error(e)
    try:
        defense = json['defense']
    except KeyError as e:
        defense = None
        logging.error(e)
    try:
        attack = json['attack']
    except KeyError as e:
        attack = None
        logging.error(e)
    try:
        health = json['health']
    except KeyError as e:
        health = None
        logging.error(e)
    try:
        max_health = json['max_health']
    except KeyError as e:
        max_health = None
        logging.error(e)

    pokemon = Pokemon(poke_id=poke_id,
                      pokedex_id=pokedex_id,
                      name=name,
                      level=level,
                      moves=moves,
                      types=types,
                      sprites=sprites,
                      weight=weight,
                      height=height,
                      female=female,
                      is_shiny=is_shiny,
                      speed=speed,
                      special_defense=special_defense,
                      special_attack=special_attack,
                      defense=defense,
                      attack=attack,
                      health=health,
                      max_health=max_health,
                      )
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
    pokedex_id = poke_json['id']
    name = poke_json['name']
    is_shiny = True if random.random() > 0.98 else False
    female = True if random.random() > 0.5 else False

    sprites = define_sprite_by_attributes(poke_json=poke_json, female=female, is_shiny=is_shiny)

    height = poke_json['height']
    weight = poke_json['weight']
    speed = list(filter(lambda x: x['stat']['name'] == 'speed', poke_json['stats']))[0]['base_stat']
    special_defense = list(filter(lambda x: x['stat']['name'] == 'special-defense', poke_json['stats']))[0]['base_stat']
    special_attack = list(filter(lambda x: x['stat']['name'] == 'special-attack', poke_json['stats']))[0]['base_stat']
    defense = list(filter(lambda x: x['stat']['name'] == 'defense', poke_json['stats']))[0]['base_stat']
    attack = list(filter(lambda x: x['stat']['name'] == 'attack', poke_json['stats']))[0]['base_stat']
    health = list(filter(lambda x: x['stat']['name'] == 'hp', poke_json['stats']))[0]['base_stat']
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
    pokemon = Pokemon(pokedex_id=pokedex_id, name=name, moves=moves, health=health, max_health=health, level=level,
                      types=types, sprites=sprites, height=height, weight=weight, female=female, is_shiny=is_shiny,
                      speed=speed,
                      special_defense=special_defense,
                      special_attack=special_attack,
                      defense=defense,
                      attack=attack,
                      )
    return pokemon


def define_sprite_by_attributes(poke_json, female, is_shiny):
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
    return sprites


def get_sprite_dir(poke_name):
    filepath = os.path.join('.', 'res', 'img', poke_name + '.png')[1:]
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + filepath


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
    filepath = os.path.join('.', 'res', 'img', 'background1.png')[1:]
    background = Image.open(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + filepath)
    w, h = background.size
    background = background.crop(((w - h) / 2, 0, w - (w - h) / 2, h))
    background.thumbnail((width_total, height_total), Image.ANTIALIAS)
    background.paste(image, (width * (direction % edge_length), height * int(direction / edge_length)), mask=alpha)
    return background


def build_pokemon_bag_image(pokemon_sprite_list, max_row_len=4):
    if len(pokemon_sprite_list) is 0:
        return None

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


def build_pokemon_trade_image(pokemon_going_sprite, pokemon_coming_sprite):
    image_going = get_poke_image(sprite=pokemon_going_sprite)
    alpha_going = image_going.convert('RGBA').split()[-1]

    width, height = image_going.size
    width_total, height_total = 3 * width, 3 * height

    image_coming = get_poke_image(sprite=pokemon_coming_sprite)
    alpha_coming = image_coming.convert('RGBA').split()[-1]

    filepath = os.path.join('.', 'res', 'img', 'background1.png')[1:]
    background = Image.open(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + filepath)
    background.thumbnail((int(width_total), int(height_total)), Image.ANTIALIAS)

    background.paste(image_going, (int(width_total * 0.18), int(height_total * 0.25)), mask=alpha_going)
    background.paste(image_coming, (int(width_total * 0.50), int(height_total * 0.8)), mask=alpha_coming)
    return background


def get_pokemon_portrait_image(pokemon_sprite):
    image = get_poke_image(sprite=pokemon_sprite)
    width, height = image.size
    alpha = image.convert('RGBA').split()[-1]
    filepath = os.path.join('.', 'res', 'img', 'background1.png')[1:]
    background = Image.open(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + filepath)
    w, h = background.size
    background = background.crop(((w - h) / 2, 0, w - (w - h) / 2, h))
    background.thumbnail((width, height), Image.ANTIALIAS)
    background.paste(image, (0, 0), mask=alpha)
    return background


def build_item_bag_image(item_list):
    pass
