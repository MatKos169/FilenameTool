import exifread
import datetime
from time import sleep
import os #os.rename('old','new')
from sys import exit as quit
import configparser
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


##datum_nummer
##index von nummer immer datum + 1
##wenn schon vorhanden nummer + 1


class FileHandler:
    def __init__(self, path, filename):
        self.path = path
        self.filename = str('.').join(filename.split('.')[:-1])
        self.filetype = filename.split('.')[-1]
        self.targetName = self.filename
        self.validName = False
        self.prefix = str()

    def getFiletype(self):
        return self.filetype

    def getName(self):
        return self.filename

    def getPath(self):
        return self.path

    def getFullPath(self):
        return os.path.join(self.path, self.filename+'.'+self.filetype)

    def getFullTargetPath(self):
        return os.path.join(self.path, self.targetName+'.'+self.filetype)

    def getTargetName(self):
        return self.targetName

    def getValidName(self):
        return self.validName

    def getPrefix(self):
        return self.prefix

    def setPrefix(self, prefix):
        self.prefix = prefix

    def setValidName(self, status):
        self.validName = status

    def setTargetName(self, name):
        self.targetName = name

    def rename(self):
        if not(self.targetName == self.filename):
            print(f'{self.filename}.{self.filetype} --> {self.targetName}.{self.filetype} - removed prefix: {self.prefix}')
            os.rename(self.getFullPath(), os.path.join(self.path, self.targetName+'.'+self.filetype))
            self.filename = self.targetName


def run(config):
    ToDo = getFiles(config)
    print(ToDo)
    TotalToDo = len(ToDo)
    print(f'Found {TotalToDo} Files to Check')
    ignoreList = list()

    for Task in ToDo:
        removeTag(config, Task, ignoreList)
        found, section = check4Date(Task)

        # Move Date to first name section
        if found and not section == 0:
            splitName = Task.getTargetName().split('_')
            splitName.insert(0, splitName.pop(section))
            Task.setTargetName('_'.join(splitName))
    targetNames = list()

    #Doppelte Dateinamen erkennen
    for Task in ToDo:
        if Task.getFullTargetPath() in targetNames:
            index = 1
            Task.setTargetName(f'{Task.getTargetName()}_{index}')
            while Task.getFullTargetPath() in targetNames:
                index += 1
                Task.setTargetName(f'{Task.getTargetName()}_{index}')
        targetNames.append(Task.getFullTargetPath())
        Task.rename()
        Task.setValidName(found)


#ToDo set new names if not already valid name

    for Task in ToDo:
        Task.rename()


def check4Date(Task):
    position = int()
    splitName = Task.getTargetName().split('_')
    for junk in splitName:
        found = False
        if not found:
            if all(c in "0123456789-." for c in junk):
                result = validateDate(junk)
                if result:
                    found = True
                    position = splitName.index(junk)
    result = (found, position)
    return result


def validateDate(part):
    result = False
    if len(part) == 8:
        if not result:
            try:
                date = datetime.datetime.strptime(part, '%Y%m%d')
                result = True
            except ValueError as e:
                pass
        if not result:
            try:
                date = datetime.datetime.strptime(part, '%Y%d%m')
            except ValueError as e:
                pass
    return result


def removeTag(config, Task, ignoreList):
    splitName = Task.getName().split('_')
    if len(splitName) >= 2:
        if splitName[0] in config['config']['prefix'].split(':'):
            Task.setPrefix(splitName[0])
            splitName.pop(0)
            Task.setTargetName('_'.join(splitName))

        elif splitName[0] not in ignoreList and not all(c in "0123456789-." for c in splitName[0]):
            aws = str()
            while aws.lower() not in ('y', 'n'):
                aws = input(f'Soll "{splitName[0]}" als Tag entfernt werden?')
            if aws.lower() == 'y':
                oldConfig = config['config']['prefix']
                config.set('config', 'prefix', oldConfig+f":{splitName[0]}")

                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
                configfile.close()
                splitName.pop(0)
                Task.setTargetName('_'.join(splitName))
            else:
                ignoreList.append(splitName[0])
        else:
            pass


def getFiles(config):
    totalFiles = list()
    for root, dirs, files in os.walk(config['config']['workdir'], topdown=True):
        for name in files:
            if name.endswith(tuple(config['config']['filetypes'].split(','))):
                totalFiles.append(FileHandler(root, name))
    return totalFiles


##Configuration Functions

def load_config(configFile):
    config = configparser.ConfigParser()
    config.read(configFile)

    return config


def newConfig(filename):
    print('config.ini could not be found. Creating new config File')
    config = configparser.ConfigParser()
    config['config'] = {'workdir': '.\\data',
                        'prefix': 'MOV:VID:DSC:IMG'}
    with open(filename, 'w') as configfile:
        config.write(configfile)
        configfile.close()


if __name__ == '__main__':
    if os.path.exists('config.ini'):
        load_config('config.ini')
        run(load_config('config.ini'))
    else:
        newConfig('config.ini')
        print('Created new config file')
        sleep(10)
        quit()

