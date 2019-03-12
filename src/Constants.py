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
DUEL_FRIENDLIST_MSG = 'duel_friendlist_msg'
DUEL_STATUS_MSG = 'duel_status_msg'
DUEL_INVITE_MSG = 'duel_invite_msg'
DUEL_CHOOSE_MSG = 'duel_choose_msg'


class NC_MSG_States(Enum):
    INFO = 0
    USERNAME = 1
    DISPLAY_EDIT_NAME = 2


class CHOOSE_FRIEND_MODE(Enum):
    TRADE = 0
    DUEL = 1


class INITIATIVE_LEVEL(Enum):
    CHOOSE_POKE = 0
    USE_ITEM = 1


class CALLBACK:
    # MENU CALLBACKS
    MENU_BAG = 'menu-bag%0%0'
    MENU_TRADE = 'menu-trade'
    MENU_CATCH = 'menu-catch'
    MENU_ITEMS = 'menu-items'
    MENU_FRIENDLIST = 'menu-friendlist'

    # BAG CALLBACKS
    @staticmethod
    def BAG_PAGE(trade_mode: bool, page_num: int): return 'bag-page%' + str(int(trade_mode)) + '%' + str(
        page_num)

    # DISPlAY CALLBACKS
    @staticmethod
    def POKE_DISPLAY_EDIT_NAME(pokemon_id: int): return 'pokemon-display-edit-name%' + str(pokemon_id)

    @staticmethod
    def POKE_DISPLAY_EDIT_TEAM(pokemon_id: int): return 'pokemon-display-edit-team%' + str(pokemon_id)

    @staticmethod
    def POKE_DISPLAY_CONFIG(trade_mode: int, page_number: int, pokemon_id: int):
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

    TRADE_ACCEPT = 'trade-accept'
    TRADE_ABORT = 'trade-abort'

    # DUEL CALLBACKS
    DUEL_START_NOFRIEND = 'duel-start-nofriend'

    @staticmethod
    def DUEL_START_FRIEND(friend_id: int): return 'duel-start-friend%' + str(friend_id)

    @staticmethod
    def DUEL_INVITE_ACCEPT(chat_id: int): return 'duel-invite-accept%' + str(chat_id)

    @staticmethod
    def DUEL_INVITE_DENY(chat_id: int): return 'duel-invite-deny%' + str(chat_id)

    @staticmethod
    def DUEL_ACTION_CHOSEN(event_id: int, source_id: int):
        return 'duel-action-chosen%' + str(event_id) + '%' + str(source_id)

    @staticmethod
    def DUEL_ACTION_POKEMON(event_id: int): return 'duel-action-pokemon%' + str(event_id)

    DUEL_ACTION_ATTACK = 'duel-action-attack'
    DUEL_ACTION_ITEM = 'duel-action-item'
    DUEL_ACTIVE = 'duel-active'

    @staticmethod
    def DUEL_ABORT(event_id: int): return 'duel-abort%' + str(event_id)

    # FRIEND CALLBACKS
    FRIEND_ADD = 'friend-add'
    FRIEND_NAME = 'friend_name'

    @staticmethod
    def FRIEND_TRADE(friend_id: int): return 'friend-trade%' + str(friend_id)

    @staticmethod
    def FRIEND_DUEL(friend_id: int): return 'friend-duel%' + str(friend_id)

    @staticmethod
    def FRIEND_DELETE(friend_id: int): return 'friend-delete%' + str(friend_id)

    @staticmethod
    def FRIEND_CONFIRM_DELETE_YES(friend_id: int): return 'friend-conf_delete-yes%' + str(friend_id)

    FRIEND_CONFIRM_DELETE_NO = 'friend-conf_delete-no'

    @staticmethod
    def FRIEND_ADD_NOTIFY_YES(player_username: str): return 'friend-notify_on_add-yes%' + player_username

    FRIEND_ADD_NOTIFY_NO = 'friend-notify_on_add-no'

    @staticmethod
    def CATCH(direction: int): return 'catch%' + str(direction)
