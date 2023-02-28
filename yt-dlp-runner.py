import os
import subprocess

executablePath = "U:\\Installers\\application_standalone_installs\\yt-dlp\\yt-dlp.exe"
urlListPath = "S:\\Video\\yt-dlp-downloads\\url-list.txt"
outputPath = "S:\\Video\\yt-dlp-downloads"

# Update the executable
print(subprocess.run([executablePath, "--update"], capture_output=True).stdout.decode('UTF-8'))

# Change current directory
os.chdir(outputPath)

# Download videos
with open(urlListPath) as f:
    for line in f:
        splitline = line.split(" ")
        print(splitline[1])
        if len(splitline) == 2 and "a" in splitline[0]:
            subprocess.run([executablePath, "--extract-audio", "--audio-format", "flac", "-o", "Audio/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s", splitline[1]], capture_output=True)
        if len(splitline) == 2 and "v" in splitline[0]:
            subprocess.run([executablePath, "--format", "bestvideo+bestaudio", "--remux-video", "mp4", "-o", "Video/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s", splitline[1]], capture_output=True)
