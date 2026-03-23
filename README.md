# neageoflymapper

[![Build](https://github.com/Wonno/neageoflymapper/actions/workflows/build.yaml/badge.svg)](https://github.com/Wonno/neageoflymapper/actions/workflows/build.yaml)

Download and stitch tiles to a single photo from [NEA Viewer](https://nea.geofly.eu/) of various zoom levels.

## Installation (Windows)
Execute the file:
```
setup.bat
```

## Start (Windows)
Execute the file:
```
start.bat
```

## Installation & Start (Linux)
Python 3 is required. (Should work with all major versions)
```sh
git clone https://github.com/fabyr/neageoflymapper.git
cd neageoflymapper
python3 -m venv env
source env/bin/activate
python -m pip install -r requirements.txt

python main.py
```

## Binary Build
Needs to be run separately for Linux and Windows.

```sh
pyinstaller --onefile --name neageoflymapper main.py
```

## Usage
In order to find the ID of an Image,
use the Devtools of a browser as follows (Can usually be opened by pressing `F12`):

1. Select the `Console` tab
2. Enter `viewer.activeBildId` into the prompt and press `Enter`
3. the ID of the currently active image will be printed in the console
   

## CLI
You can call the python file directly with some arguments to skip interactive prompting:
```
$ python main.py -h
usage: main.py [-h] [-i ID] [-z ZOOM]

Downloads an Image by ID from https://nea.geofly.eu.
If not arguments are set, values will be prompted for interactively.

options:
  -h, --help            show this help message and exit
  -i ID, --id ID        single Image ID or multiple IDs separated by space
  -z ZOOM, --zoom ZOOM  Zoom level. You can specify 'max' or 'min' to use the highest/lowest zoom level for
                        any image.
```
