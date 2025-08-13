import subprocess
import sys

def install(package):
    if package == "pip --upgrade":
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    else:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if input("Would you like to upgrade pip to the latest version? Y/N ").lower() == "y":
    install("pip --upgrade")

packages = [
    "certifi",
    "opencv-python",
    "pyxdelta",
    "requests",
    "simpleaudio",
    "Pillow",
    "beautifulsoup4",
    "pybanana",
    "selenium"
]

for package in packages:
    try:
        install(package)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")
