from Entities import Player
from src.EichState import EichState


def get_text(player: Player, strId):
    try:
        string = EichState.string_dicts[player.lang][strId]
    except KeyError as e:
        string = EichState.string_dicts['EN'][strId]
    return string
