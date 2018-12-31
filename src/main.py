from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler

import src.MessageBuilder as MessageBuilder
from src.EichState import EichState


# TODO-List:
#   items
#   use items
#   trade pokemon
#   mongo-db - wip
#   config/game menu - wip
#   edit image background
#   Tests


@MessageBuilder.send_typing_action
def command_handler_bag(bot, update):
    MessageBuilder.build_msg_bag(bot, update.message.chat_id)


def command_handler_encounter(bot, job):
    MessageBuilder.build_msg_encounter(bot)


@MessageBuilder.send_typing_action
def command_handler_item_bag(bot, update):
    MessageBuilder.build_msg_item_bag(bot, update=update)


@MessageBuilder.send_typing_action
def command_handler_info(bot, update):
    MessageBuilder.build_msg_info(bot=bot, update=update)


@MessageBuilder.send_typing_action
def command_handler_start(bot, update):
    MessageBuilder.build_msg_start(bot=bot, update=update)


def command_handler_catch(bot, update):
    MessageBuilder.build_msg_catch(bot=bot, chat_id=update.message.chat_id)


def command_handler_no_catch(bot, update):
    MessageBuilder.build_msg_no_catch(bot=bot, chat_id=update.message.chat_id)


def command_handler_menu(bot, update):
    MessageBuilder.build_msg_menu(bot=bot, update=update)


def callback_handler(bot, update):
    MessageBuilder.process_callback(bot=bot, update=update)


# DEBUG
def command_handler_restart(bot, update):
    MessageBuilder.build_msg_restart(bot=bot, update=update)


def command_handler_chance(bot, update, args):
    MessageBuilder.adjust_encounter_chance(bot, update.message.chat_id, int(args[0]) if len(args) > 0 else None)


def main():
    print('MAIN')
    MessageBuilder.prepare_environment()

    updater = Updater(token=EichState.token)
    dispatcher = updater.dispatcher
    # DEBUG
    restart_handler = CommandHandler('restart', callback=command_handler_restart)
    chance_handler = CommandHandler('chance', callback=command_handler_chance, pass_args=True)
    #
    poke_handler = MessageHandler(Filters.text, callback=command_handler_info)
    start_handler = CommandHandler('start', callback=command_handler_start)
    catch_handler = CommandHandler('catch', callback=command_handler_catch)
    no_catch_handler = CommandHandler('nocatch', callback=command_handler_no_catch)
    bag_handler = CommandHandler('bag', callback=command_handler_bag)
    items_handler = CommandHandler('items', callback=command_handler_item_bag)
    menu_handler = CommandHandler('menu', callback=command_handler_menu)
    callback_query_handler = CallbackQueryHandler(callback=callback_handler)
    # DEBUG
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(chance_handler)
    #
    dispatcher.add_handler(poke_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(catch_handler)
    dispatcher.add_handler(no_catch_handler)
    dispatcher.add_handler(bag_handler)
    dispatcher.add_handler(items_handler)
    dispatcher.add_handler(callback_query_handler)
    dispatcher.add_handler(menu_handler)

    updater.start_polling()
    j = updater.job_queue
    autoup = j.run_repeating(command_handler_encounter, interval=60, first=0)


main()
