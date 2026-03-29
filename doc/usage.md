# Usage

## Identifying Image IDs

In order to find the ID of an Image, use the Devtools of a browser as follows (Can usually be opened by pressing `F12`):

1. Select the `Console` tab
2. Enter `viewer.activeBildId` into the prompt and press `Enter`
3. the ID of the currently active image will be printed in the console

## Run application

You can call application directly with some arguments to skip interactive prompting:

```
$ python main.py -h
usage: main.py [-h] [-i ID [ID ...]] [-z ZOOM] [--version]

Downloads an Image by ID from https://nea.geofly.eu.
If not arguments are set, values will be prompted for interactively.

options:
  -h, --help            show this help message and exit
  -i ID [ID ...], --id ID [ID ...]
                        Image ID(s).
  -z ZOOM, --zoom ZOOM  Zoom level. You can specify 'max' or 'min' to use the highest/lowest zoom level for any image.
  --version             Show the application version and exit.

Version: 0.0.0
```
