# MESSAGE IDENTIFIERS
from enum import Enum

# Message Types
ENCOUNTER_MSG = 'encounter_msg'
MENU_MSG = 'menu_msg'
BAG_MSG = 'bag_msg'
MENU_INFO_MSG = 'menu_info_msg'
FRIENDLIST_MSG = 'friendlist_msg'
FRIEND_CONFIRM_DELETE_MSG = 'conf_del_friend_msg'
TRADE_FRIENDLIST_MSG = 'trade_firendlist_msg'
TRADE_CHOOSE_MSG = 'trade_choose_msg'
TRADE_CONFIRM_MSG = 'trade_confirm_msg'
TRADE_INVITE_MSG = 'trade_confirm_msg'
POKE_DISPLAY_MSG = 'poke_display_msg'


class NC_MSG_States(Enum):
    INFO = 0
    USERNAME = 1
    DISPLAY_EDIT_NAME = 2


class CALLBACK:
    # MENU CALLBACKS
    MENU_BAG = 'menu-bag%0%0'
    MENU_TRADE = 'menu-trade'
    MENU_CATCH = 'menu-catch'
    MENU_ITEMS = 'menu-items'
    MENU_FRIENDLIST = 'menu-friendlist'

    # BAG CALLBACKS
    @staticmethod
    def BAG_PAGE(trade_mode: bool, page_num: int):
        return 'bag-page%' + str(int(trade_mode)) + '%' + str(page_num)

    # DISPlAY CALLBACKS
    @staticmethod
    def POKE_DISPLAY_EDIT_NAME(pokemon_id: int):
        return 'pokemon-display-edit-name%' + str(pokemon_id)

    @staticmethod
    def POKE_DISPLAY_EDIT_TEAM(pokemon_id: int):
        return 'pokemon-display-edit-team%' + str(pokemon_id)

    @staticmethod
    def POKE_DISPLAY_CONFIG(trade_mode: bool, page_number: int, pokemon_id: int):
        return 'pokemon-display-view%' + str(int(trade_mode)) + '%' + str(page_number) + '%' + str(pokemon_id)

    # TRADE CALLBACKS
    @staticmethod
    def TRADE_CHOOSE_POKEMON(pokemon_id: int):
        return 'trade-choose-pokemon%' + str(pokemon_id)

    @staticmethod
    def TRADE_IVITE_CONFIRM(chat_id: int):
        return 'trade-invite-confirm%' + str(chat_id)

    @staticmethod
    def TRADE_INVITE_DENY(chat_id: int):
        return 'trade-invite-deny%' + str(chat_id)

    # FRIEND CALLBACKS
    FRIEND_ADD = 'friend-add'
    FRIEND_NAME = 'friend_name'

    @staticmethod
    def FRIEND_TRADE(friend_id: int):
        return 'friend-trade%' + str(friend_id)

    @staticmethod
    def FRIEND_DUEL(friend_id: int):
        return 'friend-duel%' + str(friend_id)

    @staticmethod
    def FRIEND_DELETE(friend_id: int):
        return 'friend-delete%' + str(friend_id)

    @staticmethod
    def FRIEND_CONFIRM_DELETE_YES(friend_id: int):
        return 'friend-confirm-delete-yes%' + str(friend_id)

    FRIEND_CONFIRM_DELETE_NO = 'friend-confirm-delete-no'

    @staticmethod
    def FRIEND_ADD_NOTIFY_YES(player_username: str):
        return 'friend-add-notify-yes%' + player_username

    FRIEND_ADD_NOTIFY_NO = 'friend-add-notify-no'

    @staticmethod
    def CATCH(direction: int):
        return 'catch%' + str(direction)
