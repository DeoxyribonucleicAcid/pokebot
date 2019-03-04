from MessageBuilders import TradeMessageBuilder, BagMessageBuilder, PokeDisplayBuilder, \
    FriendlistMessageBuilder, EncounterMessageBuilder, MenuMessageBuilder, ItemBagMessageBuilder


class CALLBACK_HANDLER:
    callbacks = {
        'menu': {
            'bag': BagMessageBuilder.build_msg_bag,
            'trade': TradeMessageBuilder.build_msg_trade,
            'catch': MenuMessageBuilder.toggle_encounter,
            'items': ItemBagMessageBuilder.build_msg_item_bag,
            'friendlist': FriendlistMessageBuilder.build_friendlist_message
        },
        'bag': {
            'page': BagMessageBuilder.build_msg_bag,
        },
        'pokemon': {
            'display': {
                'edit': {
                    'name': PokeDisplayBuilder.poke_edit_name,
                    'team': None
                },
                'view': PokeDisplayBuilder.build_poke_display
            }
        },
        'trade': {
            'choose': {
                'page': BagMessageBuilder.build_msg_bag,
                'pokemon': TradeMessageBuilder.trade_pokemon_chosen
            },
            'invite': {
                'confirm': TradeMessageBuilder.trade_invite_confirm,
                'deny': TradeMessageBuilder.trade_invite_deny
            },
            'inspect': {
                'pokemon': PokeDisplayBuilder.build_poke_display
            },
            'abort': TradeMessageBuilder.trade_abort,
            'accept': TradeMessageBuilder.trade_accept
        },
        'friend': {
            'name': None,
            'trade': TradeMessageBuilder.build_msg_trade,
            'duel': None,
            'delete': FriendlistMessageBuilder.delete_friend,

            'conf_delete': {
                'yes': FriendlistMessageBuilder.delete_friend_confirm,
                'no': FriendlistMessageBuilder.delete_friend_deny
            },
            'add': FriendlistMessageBuilder.build_add_friend_initial_message,
            'notify_on_add': {
                'yes': FriendlistMessageBuilder.add_friend_callback,
                'no': FriendlistMessageBuilder.add_friend_no_callback
            }
        },
        'catch': EncounterMessageBuilder.catch,
    }

    @staticmethod
    def handle(bot, chat_id, callback):
        elems = callback.split('%')
        id_elems = elems[0].split('-')
        params = elems[1:]
        cb_function = CALLBACK_HANDLER.callbacks[id_elems[0]]
        for id in id_elems[1:]:
            cb_function = cb_function[id]
        if type(cb_function) is type(None):
            return bot.send_message(chat_id=chat_id,
                                    text='Method not implemented :/')
        return cb_function(bot, chat_id, *params)


def process_callback(bot, update):
    CALLBACK_HANDLER.handle(bot=bot, chat_id=update.effective_message.chat_id, callback=update.callback_query.data)
