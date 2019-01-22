# MESSAGE IDENTIFIERS
from enum import Enum

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
