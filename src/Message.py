import logging
logger = logging.getLogger(__name__)


class Message:
    def __init__(self, _id, _title, _time_sent):
        self._id = _id
        self._title = _title
        self._time_sent = _time_sent

    def serialize_msg(self):
        return {'_id': self._id,
                '_title': self._title,
                '_time_sent': self._time_sent}


def deserialize_msg(json):
    return Message(json['_id'],
                   json['_title'],
                   json['_time_sent'])
