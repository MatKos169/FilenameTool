import exifread
import datetime
from time import sleep
import os #os.rename('old','new')
from sys import exit as quit
import configparser
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

if not ((os.path.exists('config.ini') or os.path.isfile('config.ini'))):
    print('"config.ini" could not be found. Creating new (empty) config File')
    config = configparser.ConfigParser()
    config['config'] = {'workdir': './data',
                        'imgext': 'png,jpg,jpeg',
                        'vidext': 'mp4,mov,avi',
                        'logfile': 'result.log'
                        }

    with open('config.ini', 'w') as configfile:
        config.write(configfile)
        configfile.close()
    sleep(5)
    quit()


config = configparser.ConfigParser()
config.read('config.ini')

print(config['config']['workdir'])

LogFile = open(config['config']['logfile'], "a")

if not os.path.exists(config['config']['workdir']):
    print(f"Work dir could not be found {config['config']['workdir']}")
    quit()

def log(msg):
    LogFile.write(msg+'\n')
    print(msg)


def getAllFiles():
    allImages = []
    allVideos = []
    dirList = os.listdir(config['config']['workdir'])
    imgExt = config['config']['imgext'].split(',')
    vidExt = config['config']['vidext'].split(',')
    for item in dirList:
        print(f'checking {item}')
        if os.path.isfile(config['config']['workdir']+'/'+item):
            if item.split('.')[-1].lower() in imgExt:
                print(f'{item} is an Image')
                allImages.append(config['config']['workdir']+'/'+item)
            elif item.split('.')[-1].lower() in vidExt:
                print(f'{item} is an Video')
                allVideos.append(config['config']['workdir']+'/'+item)
            else:
                log(f"{config['config']['workdir']+'/'+item} is unsupported/unknown format")
        else:
            print(f'{item} is not a File')
        print('\n')
    return allImages, allVideos

def getCaptureTime(filepath):
    imgExt = config['config']['imgext'].split(',')
    vidExt = config['config']['vidext'].split(',')
    if filepath.split('.')[-1] in vidExt:
        try:
            file = createParser(filepath)
            metadata = extractMetadata(file)
            file.close()
            for line in metadata.exportPlaintext():
                if line.split(':')[0] == '- Creation date':
                    time = ''.join(line.split('Creation date:')[1:])[1:]
                    dateobj = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            return [True, dateobj]
        except:
            return [False,]

    elif filepath.split('.')[-1] in imgExt:

        fh = open(filepath, 'rb')
        try:
            tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
            dateTaken = tags["EXIF DateTimeOriginal"]
            #try:
            dateobj = datetime.datetime.strptime(str(dateTaken), '%Y:%m:%d %H:%M:%S')
            fh.close()
            return [True, dateobj]
        except:
            fh.close()
            return [False, ]











###Runtime
images, videos = getAllFiles()
failed, success, skipped = 0, 0, 0
print(str(images)+'\n\n'+str(videos))


for item in videos+images:
    action = getCaptureTime(item)
    if not action[0]:
        log(f"error:    could not find metadata for File: {item}")
        failed += 1
    elif action[0]:
        newFileName = f"{config['config']['workdir']}/{action[1].strftime('%Y-%m-%d_%H-%M-%S')}.{item.split('.')[-1]}"

        try:
            if item == newFileName:
                log(f"info:    {item} is formated correctly. skipping")
                skipped += 1
            else:
                log(f"info:    renaming {item} to {newFileName}")
                os.rename(item, newFileName)
                success += 1
        except:
            log(f"error:    renaming of {item} failed")
            failed += 1
log(f"\nresults:\ntotal Files:{len(videos)+len(images)}\nsuccess: {success}\nfailed: {failed}\nskipped: {skipped}")



"""for item in images:
    action = getCaptureTime(item)
    if not action[0]:
        log(f"could not find metadata for File: {item}")
    elif action[0]:
        print(item)
        print(action[1].strftime('%Y%m%d-%H%M%S'))
        try:
            os.rename(item, f"{item.split('/')[0]}/{action[1].strftime('%Y%m%d-%H%M%S')}.{action[1].split('.')[-1]}")
            success += 1
        except:
            failed += 1
"""





"""
for bild in liste:
    if not os.path.isdir(bild):
        with open(config['config']['workdir']+'/'+bild, 'rb') as fh:
            try:
                tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
                dateTaken = tags["EXIF DateTimeOriginal"]
                try:
                    print(datetime.datetime.strptime(str(dateTaken), '%Y:%m:%d %H:%M:%S').strftime('%Y%m%d'))
                    dateTaken = datetime.datetime.strptime(str(dateTaken), '%Y:%m:%d %H:%M:%S').strftime('%Y%m%d')
                except:
                    print('Unknown timeformat found in file')
            except:
                print('capture timestamp not found. Using modification timestamp')
                try:
                    t = os.path.getmtime(config['config']['workdir']+'/'+bild)
                    dateTaken = "mod_" + datetime.datetime.fromtimestamp(t).strftime('%Y%m%d')
                    print(dateTaken)
                except:
                    if not os.path.exists('./error'):
                        os.mkdir('./error')
                    os.rename(config['config']['workdir']+'/'+bild, './error/'+bild)
            print(bild)

            print()
            fh.close()

            os.rename(config['config']['workdir']+'/'+bild, f"{config['config']['workdir']}/{bild.split('.')[0]}_" + dateTaken + '.' + str(bild.split('.')[1]))
    else:
        print(f'Wound touch "{bild}". Cause it is not a file')
}
"""