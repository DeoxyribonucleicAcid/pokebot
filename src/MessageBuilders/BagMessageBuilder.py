import logging
import os
import time

import telegram
from telegram import ParseMode

import Constants
import DBAccessor
import Message
import Pokemon


def build_msg_bag(bot, chat_id):
    player = DBAccessor.get_player(chat_id)
    if player is None:
        bot.send_message(chat_id=chat_id,
                         text='I have not met you yet. Want to be a Pok\xe9mon trainer? Type /catch.')
        return
    for i in player.get_messages(Constants.BAG_MSG):
        try:
            bot.delete_message(chat_id=player.chat_id, message_id=i._id)
        except telegram.error.BadRequest as e:
            logging.error(e)
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

        msg = bot.send_photo(chat_id=chat_id,
                             photo=open(filename, 'rb'),
                             caption=caption, parse_mode=ParseMode.MARKDOWN)
        os.remove(filename)
    else:
        msg = bot.send_message(chat_id=chat_id,
                               text='Your bag is empty, catch some pokemon!')
    player.messages_to_delete.append(
        Message.Message(_id=msg.message_id, _title=Constants.BAG_MSG, _time_sent=time.time()))
    update = DBAccessor.get_update_query(messages_to_delete=player.messages_to_delete)
    DBAccessor.update_player(_id=player.chat_id, update=update)
