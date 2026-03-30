# Usage

## Identifying Image IDs

Image ID extraction can be done in two ways:

### Bookmarklet
1. Drag Bookmarklet to Bookmarks.
2. Select an image on https://nea.geofly.eu 
3. click the bookmarklet to copy the Image ID to the clipboard

<div style="display:inline-block;padding:0.5em 1.2em;background:#1976d2;color:#fff;border-radius:6px;text-decoration:none;font-weight:bold;box-shadow:0 2px 6px rgba(0,0,0,0.12);transition:background 0.2s;cursor:pointer;">
<a title="Copy Image ID to Clipboard" style="color:inherit;text-decoration:none;" 
    href="javascript:(function()%7Bu%3D%22nea.geofly.eu%22%2Cwindow.location.host%3D%3Du%3F(m%3D%22Image-ID%20copied%20to%20Clipboard%3A%5Cn%22%2Bviewer.activeBildId%2Cnavigator.clipboard.writeText(viewer.activeBildId))%3Am%3D%22Bookmarklet%20works%20only%20on%20https%3A%2F%2F%22%2Bu%2Calert(m)%3B%7D)()%3B">Drag me to Bookmarks</a>
</div>

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
