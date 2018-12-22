import threading
import queue
import os
import json
import datetime

from src.Player import Player


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
            newPlayer = self.queue.get()
            self.write_to_file(newPlayer)
            self.queue.task_done()

    def write_to_file(self, newPlayer: Player):
        if os.path.isfile('./' + self.playersFile):
            with open('players.json', mode='w', encoding='utf-8') as f:
                players = json.load(f)
                print(players)
                if newPlayer.chatId in players:
                    pass
                else:
                    jsonPlayer = {newPlayer.chatId: Player.serialize_player(newPlayer)}
                    players.append(jsonPlayer)
                    json.dump(players, f)
        else:
            with open('players.json', mode='w', encoding='utf-8') as f:
                json.dump({str(newPlayer.chatId): Player.serialize_player(newPlayer)}, f)

    def get_players(self):
        if os.path.isfile('./' + self.playersFile):
            player_list = list()
            with open('players.json', mode='r', encoding='utf-8') as f:
                players = json.load(f)
                for playerId in players:
                    playerJson = players[playerId]
                    player = Player(playerJson['chatId'],
                                    playerJson['items'],
                                    playerJson['pokemon'],
                                    datetime.datetime.strptime(playerJson['lastEncounter'], '%Y-%m-%dT%H:%M:%S.%f'))
                    player_list.append(player)
            return player_list
        else:
            return None
