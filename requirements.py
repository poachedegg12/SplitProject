import subprocess
import sys

packages = [
    "certifi",
    "opencv-python",
    "pyxdelta",
    "requests",
    "simpleaudio",
    "Pillow",
    "beautifulsoup4",
    "pybanana"
]

for package in packages:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
