import logging
import urllib.request

logger = logging.getLogger(__name__)

class EichState:
    DEBUG = False
    token = None
    url = 'https://pokeapi.co/api/v2/'
    names_dict = {}
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent',
                          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.2 Safari/602.3.12')]
    db = None
    player_col = None

    # LOG_FILENAME = '.log'
    # # Set up a specific logger with our desired output level
    # logger = logging.getLogger('Logger')
    # logger.setLevel(logging.DEBUG)
    #
    # # Add the log message handler to the logger
    # handler = logging.handlers.RotatingFileHandler(
    #     LOG_FILENAME, maxBytes=20, backupCount=5)
    #
    # logger.addHandler(handler)
