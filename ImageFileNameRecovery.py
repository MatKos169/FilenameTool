import exifread
import platform
import datetime
from time import sleep
import os #os.rename('old','new')
from sys import exit as quit
import configparser
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


class FileHandler:
    def __init__(self, path, filename):
        self.path = path
        self.filename = str('.').join(filename.split('.')[:-1])
        self.filetype = filename.split('.')[-1].lower()
        self.targetName = self.filename
        self.validName = False
        self.meta_lock = False

    def isLocked(self):
        return self.meta_lock

    def setMetaLock(self):
        self.meta_lock = True

    def resetMetaLock(self):
        self.meta_lock = False

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

    def getDateFromMetadata(self):
        #pictures only
        try:
            file = open(self.getFullPath(), 'rb')
            tags = exifread.process_file(file, stop_tag="EXIF DateTimeOriginal")
            file.close()
            if len(tags) == 0:
                raise UnboundLocalError('Datei hat kein Aufnahmezeitpunkt')
            dateTaken = tags["EXIF DateTimeOriginal"]
            # try:
            dateobj = datetime.datetime.strptime(str(dateTaken), '%Y:%m:%d %H:%M:%S')
            self.setTargetName(dateobj.strftime('%Y%m%d') + '_' + self.getTargetName())
            self.setValidName(True)
        except UnboundLocalError as e:
            pass
        except Exception as e:
            print(e)

        #video
        if not self.validName:
            try:
                file = createParser(self.getFullPath())
                metadata = extractMetadata(file)
                file.close()
                for line in metadata.exportPlaintext():
                    if line.split(':')[0] == '- Creation date':
                        time = ''.join(line.split('Creation date:')[1:])[1:]
                        dateobj = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                if dateobj.strftime('%Y%m%d') != '19040101':
                    self.setTargetName(dateobj.strftime('%Y%m%d') + '_' + self.getTargetName())
                    self.setValidName(True)
                else:
                    print('Kein Datum in Metadaten gefunden. Verwende Datei erstellungs Datum (UTC)')
            except Exception as e:
                print(e)
        if not self.validName:
            stamp = os.path.getctime(self.getFullPath())
            dateobj = datetime.datetime.fromtimestamp(stamp)
            self.setTargetName(dateobj.strftime('%Y%m%d') + '_' + self.getTargetName())
            self.setValidName(True)

    def setValidName(self, status):
        self.validName = status

    def setTargetName(self, name):
        self.targetName = name

    def rename(self):
        if len(self.targetName) >= 2 and self.targetName[-1] == '_':
            self.setTargetName(self.targetName[0:-1])

        if not(self.targetName == self.filename) and self.validName:
            print(f'   {self.filename}.{self.filetype} --> {self.targetName}.{self.filetype}')
            try:
                os.rename(self.getFullPath(), os.path.join(self.path, self.targetName+'.'+self.filetype))
            except FileExistsError as e:
                print(f'Dateiname ist bereits vorhanden. Erweitere Dateiname...')
                count = 1
                done = False
                while not done:
                    try:
                        os.rename(self.getFullPath(), os.path.join(self.path, self.targetName + f'_{count}.' + self.filetype))
                    except FileExistsError as e:
                        count += 1
                    except Exception as e:
                        print(e)
                    else:
                        done = True

            except Exception as e:
                print(e)
            self.filename = self.targetName
        elif self.targetName == self.filename:
            pass
        else:
            print(' Name ist noch nicht Final bestimmt. ')


def run(config):
    print('Suche nach Dateien')
    ToDo = getFiles(config)
    TotalToDo = len(ToDo)
    print(f'{TotalToDo} Dateien zur verarbeitung gefunden')
    ignoreList = list()

    print('Beginne arbeit')

    for Task in ToDo:
        print(f'Datei {ToDo.index(Task)+1} / {TotalToDo}')
        removeTags(config, Task, ignoreList)
        found, section = check4Date(Task)

        # Move Date to first name section
        if found and not section == 0:
            splitName = Task.getTargetName().split('_')
            splitName.insert(0, splitName.pop(section))
            Task.setTargetName('_'.join(splitName))
        Task.setValidName(found)

    print("\n\nPasse Dateinamen an...\n\n")

    #Doppelte Dateinamen erkennen
    for Task in ToDo:
        print(f'\nDatei {ToDo.index(Task) + 1} / {TotalToDo}')
        Task.rename()

    print('\n\nEntferne bearbeitete Dateien aus der ToDo liste...\n\n')
    #Remove ToDos with valid Names
    newToDo = ToDo.copy()
    for Task in ToDo:
        if Task.getValidName():
            newToDo.pop(newToDo.index(Task))
        else:
            #rename from metadata
            print(f'Datei "{Task.getTargetName()}.{Task.getFiletype()}" muss noch verarbeitet werden.')
    ToDo = newToDo
    del newToDo
    TotalToDo = len(ToDo)
    print(f'\n\nEs werden insgesamt {TotalToDo} Dateien weiter verarbeiet.\n\n')

    #Rename Files from Metadata
    print('Versuche neuen Dateinamen aus Metadaten zu holen...')
    for Task in ToDo:
        print(f'Datei {ToDo.index(Task)+1} / {TotalToDo}')
        if not Task.isLocked():
            Task.getDateFromMetadata()
        else:
            print(f'Ignoriere {Task.getName()}.{Task.getFiletype()} --> Tag in Blacklist gefunden (config.ini)')

    print("\n\nPasse Dateinamen an...\n\n")
    #Doppelte Dateinamen erkennen
    for Task in ToDo:
        print(f'\nDatei {ToDo.index(Task) + 1} / {TotalToDo}')
        Task.rename()
    print('Done')
    sleep(300)


def check4Date(Task):
    position = int()
    splitName = Task.getTargetName().split('_')
    found = False
    for junk in splitName:

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


def removeTags(config, Task, ignoreList):
    print('   Suche nach Tags')
    splitName = Task.getName().split('_')
    if len(splitName) == 1:
        splitName = Task.getName().split('-')

    newSplitName = splitName.copy()
    for part in splitName:
        if part in config['config']['blacklist'].split(':'):
            Task.setMetaLock()

        if part not in config['config']['tag'].split(':') and bool(config['config']['removeShortSegments']) and len(part) < int(config['config']['segmentLength']):
            print(f'Kurzes Segment gefunden --> {part}')
            try:
                newSplitName.pop(newSplitName.index(part))
            except:
                print('Segment konnte nicht entfernt werden. Ist das segment ein definierter Tag?')
            finally:
                Task.setTargetName('_'.join(newSplitName))
                print('Kurzes Segment entfernt')
                pass

        if part in config['config']['tag'].split(':'):
            print(f'   Tag gefunden {part}')
            newSplitName.pop(newSplitName.index(part))
            print('   Tag entfernt')
            Task.setTargetName('_'.join(newSplitName))

        elif part not in ignoreList and not all(c in "0123456789-." for c in part):
            print(f'   Potentielles Tag {part} gefunden.')
            aws = str()
            while aws.lower() not in ('y', 'n'):
                aws = input(f'Soll "{part}" als Tag entfernt werden? y/n')
            if aws.lower() == 'y':
                oldConfig = config['config']['tag']
                config.set('config', 'tag', oldConfig+f":{part}")

                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
                configfile.close()
                newSplitName.pop(newSplitName.index(part))
                Task.setTargetName('_'.join(newSplitName))
            else:
                ignoreList.append(splitName.index(part))
                print(f'{part} wird nicht weiter als Tag behandelt')
        else:
            pass


def getFiles(config):
    extentions = list()
    for ext in config['config']['filetypes'].split(','):
        extentions.append(ext.lower())
        extentions.append(ext.upper())

    totalFiles = list()
    for root, dirs, files in os.walk(config['config']['workdir'], topdown=True):
        for name in files:
            if name.endswith(tuple(extentions)):
                totalFiles.append(FileHandler(root, name))
    return totalFiles


##Configuration Functions

def load_config(configFile):
    config = configparser.ConfigParser()
    config.read(configFile)
    print('Config geladen')

    return config


def newConfig(filename):
    config = configparser.ConfigParser()
    config['config'] = {'workdir': '.\\data',
                        'tag': 'MOV:VID:DSC:IMG',
                        'blacklist': 'SCAN:SCV',
                        'filetypes': 'mp4,jpg,jpeg,png,avi,flv',
                        'removeShortSegments' : 'True',
                        'segmentLength' : '4'}
    with open(filename, 'w') as configfile:
        config.write(configfile)
        configfile.close()
    print('Neue config.ini angelegt. Einstellungen festlegen und erneut starten')


if __name__ == '__main__':
    if platform.system() != 'Windows':
        print("Nicht unterstütze Platform... Umbenennen könnte zu fehlern führen")
    print('Suche config.ini...')
    if os.path.exists('config.ini'):
        run(load_config('config.ini'))
    else:
        print('config.ini nicht gefunden. Lege neue an')
        newConfig('config.ini')
        sleep(10)
        quit()