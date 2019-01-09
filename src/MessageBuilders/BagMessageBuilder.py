import os

from telegram import ParseMode

import DBAccessor
import Pokemon


def build_msg_bag(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='I have not met you yet. Want to be a Pok\xe9mon trainer? Type /catch.')
        return
    pokemon_sprite_list = []
    caption = ''
    for i in player.pokemon:
        # sprites = [v[1] for v in i.sprites.items() if v[1] is not None]
        caption += '#' + str(i.id) + ' ' + str(i.name) + ' ' + str(int(i.level)) + '\n'
        # pokemon_sprite_list.append(sprites[random.randint(0, len(sprites) - 1)])
        pokemon_sprite_list.append(i.sprites['front'])

    image = Pokemon.build_pokemon_bag_image(pokemon_sprite_list)
    if image is not None:
        directory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/res/tmp/'
        filename = directory + 'image_bag_' + str(chat_id) + '.png'
        image.save(filename, 'PNG')

        bot.send_photo(chat_id=chat_id,
                       photo=open(filename, 'rb'),
                       caption=caption, parse_mode=ParseMode.MARKDOWN)
        os.remove(filename)
    else:
        bot.send_message(chat_id=chat_id,
                         text='Your bag is empty, catch some pokemon!')
