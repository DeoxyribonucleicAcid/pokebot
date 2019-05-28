import json
import logging
import urllib.request

import EichState


class Move:
    def __init__(self, move_id, name, accuracy, power, priority, type_name, target):
        self.move_id = move_id
        self.name = name
        self.accuracy = accuracy
        self.power = power
        self.priority = priority
        self.type_name = type_name
        self.target = target

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
                    move_json['power'], move_json['priority'], move_json['type']['name'],
                    move_json['target']['name'])

    @staticmethod
    def get_move_url(move_id):
        return 'https://pokeapi.co/api/v2/move/{}/'.format(move_id)

    def serialize(self):
        return {
            'move_id': self.move_id,
            'name': self.name,
            'accuracy': self.accuracy,
            'power': self.power,
            'priority': self.priority,
            'type_name': self.type_name,
            'target': self.target
        }

    @staticmethod
    def deserialize(json):
        # FIXME: ugly code
        try:
            move_id = json['move_id']
        except KeyError as e:
            move_id = None
            logging.error(e)
        try:
            name = json['name']
        except KeyError as e:
            name = None
            logging.error(e)
        try:
            accuracy = json['accuracy']
        except KeyError as e:
            accuracy = None
            logging.error(e)
        try:
            power = json['power']
        except KeyError as e:
            power = None
            logging.error(e)
        try:
            priority = json['priority']
        except KeyError as e:
            priority = None
            logging.error(e)
        try:
            type_name = json['type_name']
        except KeyError as e:
            type_name = None
            logging.error(e)
        try:
            target = json['target']
        except KeyError as e:
            target = None
            logging.error(e)

        move = Move(move_id=move_id,
                    name=name,
                    accuracy=accuracy,
                    power=power,
                    priority=priority,
                    type_name=type_name,
                    target=target)
        return move
