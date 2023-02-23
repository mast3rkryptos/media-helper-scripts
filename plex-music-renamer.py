import csv
import glob
import mutagen
import os
import shutil
import sys
import time
import re

from pydub import AudioSegment


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("stdout.log", "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)


scriptStartTime = time.time()

baseInputDir = "U:\\Media\\Audio\\Music"
baseOutputDir = "U:\\Media\\Audio\\Music (Copy-Fix)"

# Remove existing output directory
shutil.rmtree(baseOutputDir)

# Tee stdout to a file (does not work with "check_unicode"
#sys.stdout = Logger()

types = ['.mp3', '.ogg', '.m4a', '.flac', '.wav', '.wma']
outputTypes = ['.flac', '.mp3']
outputType = "copy"
audioFiles = []
for files in types:
    audioFiles.extend(glob.glob(os.path.join(baseInputDir, f"**/*{files}"), recursive=True))
print(audioFiles)

with open("library.csv", "w", newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["Artist", "Album", "Disc", "Track", "Title"])
    with open("skipped_files.log", "w", encoding="utf-8") as skippedFilesLog:
        counter = 0
        processingTimes = []
        for f in audioFiles:
            fileStartTime = time.time()
            counter += 1
            print(f"\nProcessing file {counter} of {len(audioFiles)} ({(counter / len(audioFiles) * 100):.2f}%)")
            #print(f"\n[{'='*int(counter / len(audioFiles) * 100)}{' '*(100-int(counter / len(audioFiles) * 100))}]")
            mutFile = mutagen.File(f, easy=True)
            print(f"\tSource: {f}")
            #print(f"\t{mutFile}")
            artist = ""
            album = ""
            discNumber = "1"
            trackNumber = ""
            title = ""

            # Extract the essential tag value
            # Generally, prefer Album Artist over Artist
            # Vorbis comments and EasyID3
            if mutFile is None or mutFile.keys() is None:
                print("ERROR: Missing all file tags:", f)
                skippedFilesLog.write(f"Missing all file tags: {f}\n")
                continue
            if ("albumartist" in mutFile.keys() or "artist" in mutFile.keys()) and "album" in mutFile.keys() and "tracknumber" in mutFile.keys() and "title" in mutFile.keys():
                artist = str(mutFile['albumartist'][0] if "albumartist" in mutFile.keys() else mutFile['artist'][0]).rstrip()
                album = str(mutFile['album'][0]).rstrip()
                discNumberStr = str(mutFile['discnumber'][0] if 'discnumber' in mutFile.keys() else "1")
                if "/" in discNumberStr:
                    discNumberStr = f"{discNumberStr.split('/')[0]}"
                discNumber = f"{int(discNumberStr)}"
                trackNumberStr = str(mutFile['tracknumber'][0])
                if "/" in trackNumberStr:
                    trackNumberStr = f"{trackNumberStr.split('/')[0]}"
                trackNumber = f"{int(trackNumberStr):03d}"
                title = mutFile['title'][0]
            # ID3 Tags (deprecated since moving to EasyID3)
            elif ("TPE2" in mutFile.keys() or "TPE1" in mutFile.keys()) and "TALB" in mutFile.keys() and "TRCK" in mutFile.keys() and "TIT2" in mutFile.keys():
                artist = mutFile['TPE2'][0] if "TPE2" in mutFile.keys() else mutFile['TPE1'][0]
                album = mutFile['TALB'][0]
                discNumber = mutFile['TPOS'][0] if 'TPOS' in mutFile.keys() else "1"
                try:
                    trackNumber = f"{int(+mutFile['TRCK']):02d}"    # The unary plus pulls only the current track number (excluding the total track count)
                except ValueError:
                    trackNumber = 0
                title = mutFile['TIT2'][0]
            else:
                print("ERROR: Missing essential file tags:", f)
                skippedFilesLog.write(f'Missing essential file tags: {f} AlbumArtist:{"albumartist" in mutFile.keys()} Artist:{"artist" in mutFile.keys()} Album:{"album" in mutFile.keys()} Track:{"tracknumber" in mutFile.keys()} Title:{"title" in mutFile.keys()}\n')
                continue
            csvwriter.writerow([artist, album, discNumber, int(trackNumber), title])

            # Create the formatted output path
            subPattern = '[<>:"/\\\|\?\*]'
            outputPath = os.path.join(baseOutputDir,
                                      re.sub(subPattern, '', str(artist).rstrip(".")),
                                      re.sub(subPattern, '', str(album).rstrip(".")),
                                      re.sub(subPattern, '', f"{discNumber}{trackNumber} - {re.sub(':', '-', title)}") + f"{os.path.splitext(f)[1] if outputType not in outputTypes else outputType}")
            if len(outputPath) + 1 > 260:
                print("WARNING: Output path exceeds Windows path limitations:", f)
            else:
                print(f"\tDestination: {outputPath}")

            # Copy/convert to output path
            os.makedirs(os.path.dirname(outputPath), exist_ok=True)
            if outputType == "test":
                print("\tTesting...")
            elif outputType == "list":
                print(f"\t[{artist}] [{album}] [{discNumber}] [{trackNumber}] [{title}]")
            elif outputType is None or outputType == "copy" or os.path.splitext(f)[1] == outputType:
                # Do a non-converting copy if the output type isn't specified or the source and destination extensions are the same
                #shutil.copy(f, outputPath)
                print("\tCopying...")
                audioFile = AudioSegment.from_file(f)
                audioFile.export(outputPath,
                                 tags={"album_artist": artist,
                                       "album": album,
                                       "disc": discNumber,
                                       "track": trackNumber,
                                       "title": title})
            elif outputType == ".flac":
                print("\tConverting...")
                audioFile = AudioSegment.from_file(f)
                audioFile.export(outputPath,
                                 format="flac",
                                 tags={"album_artist": artist,
                                       "album": album,
                                       "disc": discNumber,
                                       "track": trackNumber,
                                       "title": title})
            elif outputType == ".mp3":
                print("\tConverting...")
                audioFile = AudioSegment.from_file(f)
                audioFile.export(outputPath,
                                 format="mp3",
                                 bitrate="192k",
                                 tags={"album_artist": artist,
                                       "album": album,
                                       "disc": discNumber,
                                       "track": trackNumber,
                                       "title": title})
            else:
                print("\tERROR: Unsupported conversion!!!")
                continue

            # Print out file processing time
            fileEndTime = time.time()
            print(f"\tFile Processing Time: {(fileEndTime - fileStartTime):.2f} seconds")

            # Calculate and print out estimated time remaining
            processingTimes.append(fileEndTime - fileStartTime)
            print(f"Estimated Time Remaining: {((sum(processingTimes) / len(processingTimes)) * (len(audioFiles) - counter)):.2f} seconds")

# Print out script execution time
print(f"\nScript Execution Time: {(time.time() - scriptStartTime):.2f} seconds")
