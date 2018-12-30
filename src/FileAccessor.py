import json
import os
import queue
import threading

from src.Player import Player, deserialize_player


class FileAccessor:
    def __init__(self):
        self.playersFile = 'players.json'
        self.queue = queue.Queue()
        self.lock = threading.Lock()

    def commit_player(self, player: Player):
        self.lock.acquire()
        self.queue.put(player)
        self.lock.release()

    def persist_players(self):
        while not self.queue.empty():
            new_player = self.queue.get()
            self.write_to_file(new_player)
            self.queue.task_done()

    def write_to_file(self, new_player: Player):
        if os.path.isfile('./' + self.playersFile) and os.stat("players.json").st_size > 0:
            with open('players.json', encoding='utf-8') as f:
                players = json.load(f)
                players['players'][str(new_player.chat_id)] = Player.serialize_player(new_player)
            with open('players.json', 'w') as f:
                json.dump(players, f)

            # if self.get_player(newPlayer.chat_id):
            #     pass
        else:
            with open('players.json', mode='w', encoding='utf-8') as f:
                json.dump({'players': {str(new_player.chat_id): Player.serialize_player(new_player)}}, f)

    def get_players(self):
        if os.path.isfile('./' + self.playersFile) and os.stat("players.json").st_size > 0:
            player_list = list()
            with open('players.json', mode='r', encoding='utf-8') as f:
                players = json.load(f)['players']
                for playerId in players:
                    player_json = players[playerId]
                    player = deserialize_player(player_json)
                    player_list.append(player)
            return player_list
        else:
            return None

    def get_player(self, player_id):
        if os.path.isfile('./' + self.playersFile) and os.stat("players.json").st_size > 0:
            with open('players.json', mode='r', encoding='utf-8') as f:
                players = json.load(f)['players']
                if str(player_id) in list(players.keys()):
                    player_json = players[str(player_id)]
                    player = deserialize_player(player_json)
                    return player
                else:
                    return None
        else:
            return None
