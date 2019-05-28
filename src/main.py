import logging

from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler

import MessageBuilder as MessageBuilder
import setup as setup
from MessageBuilders import ToggleCatchMessageBuilder, EncounterMessageBuilder, BagMessageBuilder, \
    ItemBagMessageBuilder, TradeMessageBuilder, MenuMessageBuilder, ReplyCallbackHandler, \
    UpdateUsernameHandler, FriendlistMessageBuilder, NoCommandMessageBuilder, MessageHelper
from src.EichState import EichState


# TODO-List:
#   items
#   use items
#   trade pokemon
#   duels
#   inspect pokemon
#   train pokemon
#   config/game menu - wip
#   Tests
#   German
#   use tempfile


@MessageBuilder.send_typing_action
def command_handler_bag(bot, update):
    BagMessageBuilder.build_msg_bag(bot, update.message.chat_id, page_number=0, trade_mode=False)


def command_handler_encounter(bot, job):
    EncounterMessageBuilder.build_encounter_message(bot)


@MessageBuilder.send_typing_action
def command_handler_item_bag(bot, update):
    ItemBagMessageBuilder.build_msg_item_bag(bot, chat_id=update.message.chat_id)


@MessageBuilder.send_typing_action
def command_handler_nc_msg(bot, update):
    NoCommandMessageBuilder.build_nc_msg(bot, update)


@MessageBuilder.send_typing_action
def command_handler_start(bot, update):
    MessageBuilder.build_msg_start(bot=bot, update=update)


@MessageBuilder.send_typing_action
def command_handler_help(bot, update):
    MessageBuilder.build_msg_help(bot=bot, chat_id=update.message.chat_id)


def command_handler_catch(bot, update):
    ToggleCatchMessageBuilder.build_catch_message(bot=bot, chat_id=update.message.chat_id)


def command_handler_trade(bot, update):
    TradeMessageBuilder.build_msg_trade(bot=bot, chat_id=update.message.chat_id)


def command_handler_no_catch(bot, update):
    ToggleCatchMessageBuilder.build_no_catch_message(bot=bot, chat_id=update.message.chat_id)


def command_handler_menu(bot, update):
    MenuMessageBuilder.send_menu_message(bot=bot, update=update)


def callback_handler(bot, update):
    ReplyCallbackHandler.process_callback(bot=bot, update=update)


def command_handler_update_username(bot, update):
    UpdateUsernameHandler.update_username(bot=bot, update=update)


def command_handler_firendlist(bot, update):
    FriendlistMessageBuilder.build_friendlist_message(bot=bot, chat_id=update.message.chat_id)


def command_handler_add_friend(bot, update):
    FriendlistMessageBuilder.build_add_friend_initial_message(bot=bot, chat_id=update.message.chat_id)

# Keepalive
def logfile_handler(bot, job):
    MessageHelper.shorten_logfile()

# DEBUG
def command_handler_restart(bot, update):
    MessageBuilder.build_msg_restart(bot=bot, update=update)


def command_handler_chance(bot, update, args):
    MessageBuilder.adjust_encounter_chance(bot, update.message.chat_id, int(args[0]) if len(args) > 0 else None)

def command_handler_test(bot, update, args):
    MessageBuilder.test(bot, update)


def command_handler_reset(bot, update):
    MessageHelper.reset_states(bot, update.message.chat_id)


def command_handler_clear_duels(bot, update):
    MessageHelper.clear_duels(bot, update)


def main():
    logging.basicConfig(filename='.log', level=logging.DEBUG, filemode='w')
    setup.prepare_environment()

    updater = Updater(token=EichState.token, request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
    dispatcher = updater.dispatcher
    # DEBUG
    restart_handler = CommandHandler('restart', callback=command_handler_restart)
    chance_handler = CommandHandler('chance', callback=command_handler_chance, pass_args=True)
    test_handler = CommandHandler('test', callback=command_handler_test, pass_args=True)
    clear_duels_handler = CommandHandler('clearduels', callback=command_handler_clear_duels)
    #
    nc_msg_handler = MessageHandler(Filters.text, callback=command_handler_nc_msg)
    start_handler = CommandHandler('start', callback=command_handler_start)
    help_handler = CommandHandler('help', callback=command_handler_help)
    catch_handler = CommandHandler('catch', callback=command_handler_catch)
    trade_handler = CommandHandler('trade', callback=command_handler_trade)
    no_catch_handler = CommandHandler('nocatch', callback=command_handler_no_catch)
    bag_handler = CommandHandler('bag', callback=command_handler_bag)
    items_handler = CommandHandler('items', callback=command_handler_item_bag)
    menu_handler = CommandHandler('menu', callback=command_handler_menu)
    callback_query_handler = CallbackQueryHandler(callback=callback_handler)
    update_username_handler = CommandHandler('username', callback=command_handler_update_username)
    friendlist_handler = CommandHandler('friendlist', callback=command_handler_firendlist)
    addfriend_handler = CommandHandler('addfriend', callback=command_handler_add_friend)
    reset_handler = CommandHandler('exit', callback=command_handler_reset)
    # DEBUG
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(chance_handler)
    dispatcher.add_handler(test_handler)
    #
    dispatcher.add_handler(nc_msg_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(catch_handler)
    dispatcher.add_handler(trade_handler)
    dispatcher.add_handler(no_catch_handler)
    dispatcher.add_handler(bag_handler)
    dispatcher.add_handler(items_handler)
    dispatcher.add_handler(callback_query_handler)
    dispatcher.add_handler(menu_handler)
    dispatcher.add_handler(update_username_handler)
    dispatcher.add_handler(friendlist_handler)
    dispatcher.add_handler(addfriend_handler)
    dispatcher.add_handler(reset_handler)
    dispatcher.add_handler(clear_duels_handler)

    updater.start_polling()
    j = updater.job_queue
    j.run_repeating(command_handler_encounter, interval=60 * 15, first=0)
    j.run_repeating(logfile_handler, interval=60 * 15, first=0)


main()
