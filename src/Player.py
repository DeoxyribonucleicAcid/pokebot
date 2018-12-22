import datetime


class Player:
    def __init__(self, chatId, items=None, pokemon=None, lastEncounter=None):
        self.chatId = chatId
        self.items = {} if items is None else items
        self.pokemon = {} if pokemon is None else pokemon
        self.lastEncounter = datetime.datetime.now() if lastEncounter == None else lastEncounter

    def serialize_player(self):
        serial = {'chatId': self.chatId,
                  'items': self.items,
                  'pokemon': self.pokemon,
                  'lastEncounter': self.lastEncounter.isoformat()}
        return serial
