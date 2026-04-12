# Usage

## Identifying Image IDs

Image ID extraction can be done in two ways:

### Bookmarklet

1. Create a bookmark in your browser name it e.g. "Image-ID" and **set the URL** to the following code:

```text
javascript:(function()%7Bu%3D%22nea.geofly.eu%22%2Cwindow.location.host%3D%3Du%3F(m%3D%22Image-ID%20copied%20to%20Clipboard%3A%5Cn%22%2Bviewer.activeBildId%2Cnavigator.clipboard.writeText(viewer.activeBildId))%3Am%3D%22Bookmarklet%20works%20only%20on%20https%3A%2F%2F%22%2Bu%2Calert(m)%3B%7D)()%3B
```

2. Select an image on https://nea.geofly.eu
3. click the bookmark to copy the Image ID to the clipboard

**Non minified version of the bookmarklet code:**

```javascript
u = 'nea.geofly.eu';
if (window.location.host == u) {
    m = 'Image-ID copied to Clipboard:\n' + viewer.activeBildId;
    navigator.clipboard.writeText(viewer.activeBildId);
} else {
    m = 'Bookmarklet works only on https://' + u;
}
alert(m);
```

### Manually

In order to find the ID of an Image, use the Devtools of a browser as follows (Can usually be opened by pressing `F12`):

1. Select the `Console` tab
2. Enter `viewer.activeBildId` into the prompt and press `Enter`
3. the ID of the currently active image will be printed in the console

## Run application

You can call application directly with some arguments to skip interactive prompting:

```text
$ poetry run python src/main.py -h
usage: main.py [-h] [-i ID [ID ...]] [-z ZOOM] [-o OUTPUT_DIR]
               [-n FILENAME_PATTERN] [--version]

Downloads an Image by ID from https://nea.geofly.eu.
If not arguments are set, values will be prompted for interactively.

options:
  -h, --help            show this help message and exit
  -i ID [ID ...], --id ID [ID ...]
                        Image ID(s).
  -z ZOOM, --zoom ZOOM  Zoom level. You can specify 'max' or 'min' to use the highest/lowest zoom level for any image.
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Destination directory for downloaded files.
  -n FILENAME_PATTERN, --filename-pattern FILENAME_PATTERN
                        Custom file-name pattern using str.format placeholders like
                        {name}, {date}, {location}, {id},
                        and {zoom}.
  --version             Show the application version and exit.

Version: 0.0.0
```

Use `--output-dir` to store the generated `.jpg`, `.txt`, and `.kml` files in a specific directory:

```bash
poetry run python src/main.py --id 123456 --zoom max --output-dir downloads
```

Use `--filename-pattern` to customize the shared base name of the generated files.
The pattern uses Python `str.format(...)` placeholders.

Available placeholders include:

- `id`
- `name`
- `date`
- `location`
- `width`
- `height`
- `origin`
- `spectral`
- `zoom`

Example:

```bash
poetry run python src/main.py --id 123456 --zoom max --filename-pattern "{date}_{id}_{zoom}"
```
