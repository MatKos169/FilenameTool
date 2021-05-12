from time import sleep
import os
from sys import exit as quit
import configparser

if not (os.path.exists('config.ini') or os.path.isfile('config.ini')):
    #print('"config.ini" could not be found. Creating new (empty) config File')
    config = configparser.ConfigParser()
    config['config'] = {'workdir': ''}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
        configfile.close()
    sleep(5)
    quit()

config = configparser.ConfigParser()
config.read('config.ini')

#print(config['config']['workdir'])

if not os.path.exists(config['config']['workdir']):

    os.mkdir(config['config']['workdir'])
    #print('Copy Images to data folder and restart the programm')
    quit()

dirList = os.listdir(config['config']['workdir'])
for item in dirList:
    if item.count('(') == 1 and item.count(')') == 1:
        print(f'{item} wird bearbeitet')
        if item.split('(')[0][-1] == ' ':
            target = item.split('(')[0][:-1]+item.split(')')[-1]
        else:
            target = item.split('(')[0] + item.split(')')[-1]
        try:
            os.rename(config['config']['workdir'] + '/' + item, config['config']['workdir'] + '/' + target.replace('__', '_'))
        except:
            print(f'{item} kann nicht umbenannt werden. Duplikat?')

    elif item.count('(') >= 1 or item.count('(') >= 1:
        print(f'{item} hat mehrere tags und wird nicht bearbeitet!')

    else:
        print('Keine aktion notwending')