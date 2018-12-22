from src.FileAccessor import FileAccessor
import urllib.request


class EichState:
    DEBUG = False
    url = 'https://pokeapi.co/api/v2/'
    names_dict = {}
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent',
                          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.2 Safari/602.3.12')]
    fileAccessor = FileAccessor()
