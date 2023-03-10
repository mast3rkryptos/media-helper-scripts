import glob
import os


from pydub import AudioSegment

workingPath = "D:\\Audio\\Music (Input)\\"

files = []
files.extend(glob.glob(os.path.join(workingPath, f"**/*.wav"), recursive=True))
for file in files:
    print("Source:", file)
    print("Destination:", os.path.splitext(file)[0] + ".flac")
    audioFile = AudioSegment.from_file(file)
    audioFile.export(os.path.splitext(file)[0] + ".flac", format="flac")
