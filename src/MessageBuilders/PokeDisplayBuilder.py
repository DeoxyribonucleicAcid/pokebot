import logging
from io import BytesIO

from telegram import ParseMode

import Pokemon


def build_poke_display(bot, chat_id, pokemon):
    bot.send_message(chat_id=chat_id, text='Poke-Displays are currently under development. Please try again later.')
    text = 'Pokedex ID: ' + str(pokemon.pokedex_id) + '\n' + \
           'Name: ' + str(pokemon.name) + '\n' + \
           'Level: ' + str(pokemon.level) + '\n'

    bio = BytesIO()
    bio.name = 'image_displ_' + str(chat_id) + '.png'
    image = Pokemon.get_pokemon_portrait_image(pokemon_sprite=pokemon.sprites['front'])
    image.save(bio, 'PNG')
    bio.seek(0)

    try:
        bot.send_photo(chat_id=chat_id,
                       photo=bio,
                       caption=text,
                       parse_mode=ParseMode.MARKDOWN)
    except ConnectionResetError as e:
        logging.error(e)
