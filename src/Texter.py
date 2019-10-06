from Entities import Player
from src.EichState import EichState


def get_text(player: Player, strId):
    print(player.lang, strId, EichState.string_dicts[player.lang][strId])
    return EichState.string_dicts[player.lang][strId]
