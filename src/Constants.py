# MESSAGE IDENTIFIERS
from enum import Enum

ENCOUNTER_MSG = 'encounter_msg'
MENU_MSG = 'menu_msg'
BAG_MSG = 'bag_msg'
MENU_INFO_MSG = 'menu_info_msg'


class NC_MSG_States(Enum):
    INFO = 0
    USERNAME = 1