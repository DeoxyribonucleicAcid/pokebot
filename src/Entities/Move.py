import json
import logging
import urllib.request

import EichState


class Move:
    def __init__(self, move_id, name, accuracy, power, priority, type_name):
        self.move_id = move_id
        self.name = name
        self.accuracy = accuracy
        self.power = power
        self.priority = priority
        self.type_name = type_name

    @staticmethod
    def get_move_json(url):
        try:
            poke_response = EichState.EichState.opener.open(url)
        except urllib.request.HTTPError as e:
            logging.error('Pokemon not found: ' + '\n' + url)
            raise e
        move_json = json.load(poke_response)
        return move_json

    @staticmethod
    def get_move(url):
        move_json = Move.get_move_json(url)
        return Move(move_json['id'], move_json['name'], move_json['accuracy'],
                    move_json['power'], move_json['priority'], move_json['type']['name'])
