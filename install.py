import json
import os
import subprocess
import sys


def install(package):
    subprocess.call([sys.executable, "-m", "pip", "install", package])


subprocess.call(['virtualenv', 'venv'])
subprocess.call(['source', 'venv/bin/activate'])
# Example
if __name__ == '__main__':
    install('python-telegram-bot')
    install('setproctitle')
    install('requests')
    install('Pillow')
    install('pymongo')
    install('dnspython')
    install('emoji')

if os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + '/src/conf.json'):
    with open(os.path.dirname(os.path.abspath(__file__)) + '/src/conf.json') as f:
        json.load(f)
else:
    raise EnvironmentError("Config file not existent or wrong format")

if os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + '/src/name_dict.json'):
    with open(os.path.dirname(os.path.abspath(__file__)) + '/src/name_dict.json') as f:
        json.load(f)
else:
    raise EnvironmentError("Names file not existent or wrong format")

directory = os.path.dirname(os.path.abspath(__file__)) + '/res/tmp'
if not os.path.exists(directory):
    os.makedirs(directory)
