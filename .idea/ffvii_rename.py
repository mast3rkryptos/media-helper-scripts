import glob
import mutagen
import os
import re
import shutil

pattern = "^\d+\t(.+)"
count = 1
with open("D:\\ffviiremakeraw.txt", "r", encoding="utf-8") as f:
    with open("D:\\ffviiremakeout.txt", "w", encoding="utf-8") as out:
        for line in f:
            match = re.match(pattern, line)
            if match is not None:
                out.write(f"{count} - {match.groups()[0]}\n")
                count = count + 1
album = "Final Fantasy VII Remake (incl. Plus and Acoustic)"
albumArtist = "Nobuo Uematsu"
disc = "1"

# Get list of all applicable files (based on extension) in the input directory
audioFiles = glob.glob(os.path.join("D:\\Audio\\Music (Input)\\OST： FINAL FANTASY VII REMAKE Original Soundtrack + Plus + Acoustic (Arranged)", f"**/*.flac"), recursive=True)
audioFiles.sort()
audioFileIndex = 0
with open("D:\\ffviiremake_tracklist.txt", "r", encoding="utf-8") as f:
    for line in f:
        #shutil.copy(audioFiles[audioFileIndex], os.path.join("D:\\Audio\\Music (Input)\\FFVII_Remake_Out", line.rstrip() + ".flac"))
        mutfile = mutagen.File(audioFiles[audioFileIndex], easy=True)
        mutfile.tags["album"] = album
        mutfile.tags["albumartist"] = albumArtist
        mutfile.tags["discnumber"] = disc
        mutfile.tags["tracknumber"] = line.split("---")[0].strip()
        mutfile.tags["title"] = line.split("---")[1].strip()
        mutfile.save()
        print(mutfile.tags.pprint())
        audioFileIndex = audioFileIndex + 1