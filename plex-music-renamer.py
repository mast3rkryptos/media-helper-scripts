import csv
import glob
import mutagen
import os
import shutil
import sys
import time
import re

from pydub import AudioSegment

# TODO: Change skipped log file and messages to timestamped log or "messages.log"
# TODO: Update to use argparse for command-line arguments
# TODO: Implement in-place "fix" operation
# TODO: Determine if we want to completely replace existing tags

# Configuration variables, would like to move these to argparse command line arguments
baseInputDir = "U:\\Media\\Audio\\Music"
baseOutputDir = "U:\\Media\\Audio\\Music (Copy-Fix)"
types = ['.mp3', '.ogg', '.m4a', '.flac', '.wav', '.wma']
outputType = "mp3"
operation = "copy"  # Can be convert, copy, fix, list, test


# Used to mirror stdout to a log file; helps with debugging unattended test runs
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("stdout.log", "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)


def writetag(path, artist, album, discNumber, trackNumber, title):
    mutFileWritetag = mutagen.File(path, easy=True)
    #mutFileWritetag.delete() # Maybe don't delete the original tag info, for now
    mutFileWritetag.tags["albumartist"] = artist
    mutFileWritetag.tags["album"] = album
    mutFileWritetag.tags["discnumber"] = discNumber
    mutFileWritetag.tags["tracknumber"] = str(int(trackNumber))
    mutFileWritetag.tags["title"] = title
    mutFileWritetag.save()


# Begin timer for overall runtime tracker
scriptStartTime = time.time()

# Remove existing output directory
shutil.rmtree(baseOutputDir)

# Tee stdout to a file (does not work with "check_unicode"? Maybe OBE)
#sys.stdout = Logger()

# Get list of all applicable files (based on extension) in the input directory
audioFiles = []
for files in types:
    audioFiles.extend(glob.glob(os.path.join(baseInputDir, f"**/*{files}"), recursive=True))
print(audioFiles)

# Side task, keep track of all audio file tags in a csv for easy data crunching later
with open("library.csv", "w", newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["Artist", "Album", "Disc", "Track", "Title"])
    # This log used for specific info/warning/error messages for the user (dont' want to lose them in the stdout noise)
    with open("skipped_files.log", "w", encoding="utf-8") as skippedFilesLog:
        # These two variables used to monitor real-time progress
        counter = 0
        processingTimes = []
        # Iterate through each file, extract essential tags, if present, and perform the requested operation
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
            else:
                print("ERROR: Missing essential file tags:", f)
                skippedFilesLog.write(f'Missing essential file tags: {f} AlbumArtist:{"albumartist" in mutFile.keys()} Artist:{"artist" in mutFile.keys()} Album:{"album" in mutFile.keys()} Track:{"tracknumber" in mutFile.keys()} Title:{"title" in mutFile.keys()}\n')
                continue
            csvwriter.writerow([artist, album, discNumber, int(trackNumber), title])

            # Create a file in the source directory to store the album artist and album. This will aid in copying over any existing album art to the destination folder
            with open(os.path.join(os.path.dirname(f), "folder.jpg.tag"), "w", encoding="utf-8") as albumArtHelperFile:
                albumArtHelperFile.write(f"{artist}\n{album}")

            # Create the formatted output path
            subPattern = '[<>:"/\\\|\?\*]'
            outputPath = os.path.join(baseOutputDir,
                                      re.sub(subPattern, '', str(artist).rstrip(".")),
                                      re.sub(subPattern, '', str(album).rstrip(".")),
                                      re.sub(subPattern, '', f"{discNumber}{trackNumber} - {re.sub(':', '-', title)}") + f"{os.path.splitext(f)[1] if operation != 'convert' else ('.' + outputType)}")
            if len(outputPath) + 1 > 260:
                print("WARNING: Output path exceeds Windows path limitations:", f)
            else:
                print(f"\tDestination: {outputPath}")

            # Do operation
            os.makedirs(os.path.dirname(outputPath), exist_ok=True)
            if operation == "convert" and os.path.splitext(f)[1][1:] != outputType:
                if outputType == "flac":
                    print("\tConverting...")
                    audioFile = AudioSegment.from_file(f)
                    audioFile.export(outputPath, format="flac")
                    writetag(outputPath, artist, album, discNumber, trackNumber, title)
                elif outputType == "mp3":
                    print("\tConverting...")
                    audioFile = AudioSegment.from_file(f)
                    audioFile.export(outputPath, format="mp3", bitrate="192k")
                    writetag(outputPath, artist, album, discNumber, trackNumber, title)
            elif operation == "copy" or (operation == "convert" and os.path.splitext(f)[1][1:] == outputType):
                # Do a non-converting copy if specified or the source and destination extensions are the same
                print("\tCopying...")
                shutil.copy(f, outputPath)
                writetag(outputPath, artist, album, discNumber, trackNumber, title)
            elif operation == "fix":
                print("\tERROR: Unimplemented operation!!!")
                continue
            elif operation == "list":
                print(f"\t[{artist}] [{album}] [{discNumber}] [{trackNumber}] [{title}]")
            elif operation == "test":
                print("\tTesting...")
            else:
                print("\tERROR: Unsupported operation!!!")
                continue

            # Print out file processing time
            fileEndTime = time.time()
            print(f"\tFile Processing Time: {(fileEndTime - fileStartTime):.2f} seconds")

            # Calculate and print out estimated time remaining
            processingTimes.append(fileEndTime - fileStartTime)
            print(f"Estimated Time Remaining: {((sum(processingTimes) / len(processingTimes)) * (len(audioFiles) - counter)):.2f} seconds")

        # Copy over existing album artwork, if present. Delete the album art helper file.
        albumArtFiles = glob.glob(os.path.join(baseInputDir, f"**/folder.jpg"), recursive=True)
        print("\n", albumArtFiles)
        for albumArtFile in albumArtFiles:
            with open(os.path.join(os.path.dirname(albumArtFile), "folder.jpg.tag"), "r", encoding="utf-8") as albumArtHelperFile:
                artist = albumArtHelperFile.readline().strip()
                album = albumArtHelperFile.readline().strip()
                subPattern = '[<>:"/\\\|\?\*]'
                outputPath = os.path.join(baseOutputDir,
                                          re.sub(subPattern, '', str(artist).rstrip(".")),
                                          re.sub(subPattern, '', str(album).rstrip(".")),
                                          "folder.jpg")
                if len(outputPath) + 1 > 260:
                    print("WARNING: Output path exceeds Windows path limitations:", albumArtFile)
                shutil.copy(albumArtFile, outputPath)
            os.remove(os.path.join(os.path.dirname(albumArtFile), "folder.jpg.tag"))

        # List out any files not touched by the script
        allFiles = glob.glob(os.path.join(baseInputDir, f"**/*"), recursive=True)
        for f in allFiles:
            if os.path.isfile(f) and os.path.splitext(f)[1] not in types and os.path.basename(f) != "folder.jpg":
                skippedFilesLog.write(f"INFO: Untouched File: {f}\n")


# Print out script execution time
print(f"\nScript Execution Time: {(time.time() - scriptStartTime):.2f} seconds")
