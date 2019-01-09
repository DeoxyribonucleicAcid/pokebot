import logging
logger = logging.getLogger(__name__)


class Item:
    def __init__(self, item_id, name, attributes):
        self.id = item_id
        self.name = name
        self.attributes = attributes

    def serialize_item(self):
        serial = {
            'id': self.id,
            'name': self.name,
            'attributes': self.attributes
        }
        return serial


def deserialize_item(json):
    item = Item(json['id'],
                json['name'],
                json['attributes'])
    return item
