import glob
import mutagen
import os
import re

workingPath = "D:\\Audio\\Music (Input)\\NA"
searchPattern = "NA - (.+) ｜ Suite Soundtracks\.flac"
album = "Suite Soundtracks"
albumArtist = "Suite Soundtracks"
disc = "1"

files = []
files.extend(glob.glob(os.path.join(workingPath, f"**/*.*"), recursive=True))
for file in files:
    print(file)
    mutfile = mutagen.File(file, easy=True)
    result = re.search(searchPattern, file)
    if result:
        print(result.groups()[0], result.groups()[1])
        #continue
        mutfile.tags["album"] = album
        mutfile.tags["albumartist"] = albumArtist
        mutfile.tags["discnumber"] = disc
        mutfile.tags["tracknumber"] = result.groups()[0]
        mutfile.tags["title"] = result.groups()[1]
        mutfile.save()
        print(mutfile.tags.pprint())
