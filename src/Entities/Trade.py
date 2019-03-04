import logging

from Entities import Pokemon as Pokemon

logger = logging.getLogger(__name__)


class Trade:
    def __init__(self, trade_id=None, pokemon=None, partner_id=None, accepted=None):
        self.trade_id = id(self) if trade_id is None else trade_id
        self.pokemon: Pokemon = pokemon
        self.partner_id: int = partner_id
        self.accepted: bool = accepted

    def serialize(self):
        serial = {'trade_id': self.trade_id,
                  'pokemon': self.pokemon.serialize_pokemon() if self.pokemon is not None else None,
                  'partner_id': self.partner_id,
                  'accepted': self.accepted}
        return serial

    @staticmethod
    def deserialize(json):
        # FIXME: ugly code
        try:
            trade_id = json['trade_id']
        except KeyError as e:
            trade_id = None
            logging.error(e)
        try:
            pokemon = Pokemon.deserialize_pokemon(
                json['pokemon']
            ) if json['pokemon'] is not None else None
        except KeyError as e:
            pokemon = None
            logging.error(e)
        try:
            partner_id = int(json['partner_id'])
        except KeyError as e:
            partner_id = None
            logging.error(e)
        try:
            accepted = json['accepted']
        except KeyError as e:
            accepted = None
            logging.error(e)

        trade = Trade(trade_id=trade_id,
                      pokemon=pokemon,
                      partner_id=partner_id,
                      accepted=accepted)
        return trade
