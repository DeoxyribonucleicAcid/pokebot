import json
import logging
import random
import urllib.request
from io import BytesIO

from telegram import ParseMode

import Pokemon
from src.EichState import EichState


def get_poke_info(pokemon):
    poke_json = Pokemon.get_pokemon_json(pokemon)
    # sprites = {k: v for k, v in poke_json[u'sprites'].items() if v is not None}
    type_urls = []
    for poke_type in poke_json[u'types']:
        type_urls.append(poke_type[u'type'][u'url'])
    double_damage_types = []
    half_damage_types = []
    no_damage_types = []
    types = []
    for poke_type in type_urls:
        try:
            type_json = json.load(EichState.opener.open(poke_type))
            types.append(type_json[u'name'])
            dd_relations = type_json[u'damage_relations'][u'double_damage_from']
            hd_relations = type_json[u'damage_relations'][u'half_damage_from']
            nd_relations = type_json[u'damage_relations'][u'no_damage_from']
            for dd_type in dd_relations:
                double_damage_types.append(dd_type[u'name'])
            for hd_type in hd_relations:
                half_damage_types.append(hd_type[u'name'])
            for nd_type in nd_relations:
                no_damage_types.append(nd_type[u'name'])
        except urllib.request.HTTPError as e:
            logging.error('Type not found: ' + '\n' + poke_type)
            raise e

    if random.random() > 0.90:
        sprite = poke_json['sprites']['front_shiny']
    else:
        sprite = poke_json['sprites']['front_default']

    dd_types_str = ', '.join(map(str, list(set(double_damage_types))))
    hd_types_str = ', '.join(map(str, list(set(half_damage_types))))
    nd_types_str = ', '.join(map(str, list(set(no_damage_types))))
    types_str = ', '.join(map(str, types))
    name_str = str(poke_json[u'name'])
    id_str = str(poke_json[u'id'])

    text = name_str + ' #' + id_str + '\n' + types_str + '\nAttack with:\n' + dd_types_str + '\nDon\'t use:\n' + hd_types_str
    if len(no_damage_types) != 0:
        text += '\nor worse:\n' + nd_types_str
    return text, sprite


def build_msg_info(bot, update):
    pokemon = update.message.text.lower()
    if pokemon in EichState.names_dict["pokenames"].keys():
        pokemon = EichState.names_dict["pokenames"][pokemon]
    pokemon = pokemon.lower()
    try:
        text, sprite = get_poke_info(pokemon)
        bio = BytesIO()
        bio.name = 'image_info_' + str(update.message.chat_id) + '.png'
        image = Pokemon.get_pokemon_portrait_image(sprite)
        image.save(bio,'PNG')
        bio.seek(0)

        bot.send_photo(chat_id=update.message.chat_id,
                       photo=bio,
                       caption=text,
                       parse_mode=ParseMode.MARKDOWN)
    except urllib.request.HTTPError as e:
        bot.send_message(chat_id=update.message.chat_id, text=':( i didn\'t catch that')
    except ConnectionResetError as e:
        logging.error(e)
