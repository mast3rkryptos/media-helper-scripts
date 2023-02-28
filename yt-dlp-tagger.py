import glob
import mutagen
import os
import re

workingPath = "S:\\Video\\yt-dlp-downloads\\Audio\\Uncharted 4： A Thief's End - Original Soundtracks"
searchPattern = "(\d+) - .+ OST - (.+)\.flac"
album = "Uncharted 4： A Thief's End"
albumArtist = "Henry Jackman"
disc = "1"

files = []
files.extend(glob.glob(os.path.join(workingPath, f"**/*.flac"), recursive=True))
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
