# neageoflymapper

Download a single photo from https://nea.geofly.eu/?desktop= of various zoom levels.
(Download and stitch tiles)

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

## Usage
In order to find the ID of an Image,
use the Devtools of a browser as follows (Can usually be opened by pressing `F12`):

1. Select the `Network` or `Networking` tab\
   ![Devtools Network Tab](/assets/image1.png)
2. Enter `getFeature?` into the filter\
   ![Filter](/assets/image2.png)
3. Upon selection of a `Circle` on the map, the corresponding Network request showing the ID should appear.\
   ![Filter](/assets/image3.png)\
   In this Case the ID is `55345746`. This is the ID to enter in the program.

## CLI
You can call the python file directly with some arguments to skip interactive prompting:
```
$ python main.py -h
usage: main.py [-h] [-i ID] [-z ZOOM]

Downloads an Image by ID from https://nea.geofly.eu.
If not arguments are set, values will be prompted for interactively.

options:
  -h, --help            show this help message and exit
  -i ID, --id ID        Image ID.
  -z ZOOM, --zoom ZOOM  Zoom level. You can specify 'max' or 'min' to use the highest/lowest zoom level for
                        any image.
```
