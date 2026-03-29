"""KML generation logic for nea-geofly-mapper.

This module provides functionality to generate KML documents from aerial image
metadata, including image center points and corner outlines.
"""
from fastkml import atom, geometry, kml
from pygeoif import geometry as pygeo

def generator(metainfos):
    """Generate a KML document for a single aerial image.

    Creates a KML structure containing one :class:`~fastkml.kml.Placemark`
    with a :class:`~fastkml.geometry.MultiGeometry` consisting of:

    * a **Point** at the image's center coordinate (WGS84/EPSG:4326), and
    * a **LineString** tracing the four corner coordinates as a closed loop.

    Args:
        metainfos (Metainfos): Metadata object for the aerial image.

    Returns:
        KML root object ready to be serialised.
    """
    k = kml.KML()
    doc = kml.Document(name=f"{metainfos.image_name}",
                                atom_link=atom.Link(href='https://github.com/wonno/neageoflymapper',
                                           title='nea-geofly-mapper')
                                )
    k.append(doc)
    corners = metainfos.corner_coords_wgs84g()
    corners.append(corners[0]) # create a loop
    corners[:] = [(*c, 0) for c in corners] # add z coord with value zero to every tuple

    line = pygeo.LineString(corners)
    line = geometry.LineString(tessellate=True,
                               geometry=line)
    x,y = metainfos.center_coords_wgs84g()
    point = pygeo.Point(x,y, 0)
    point = geometry.Point(geometry=point)

    #language=HTML
    desc= f"""<ul>
                <li>id: {metainfos.image_id}</li>
                <li>name: {metainfos.image_name}</li>
                <li>location: {metainfos.image_location}</li>
                <li>date: {metainfos.image_date}</li>
              </ul>"""
    mg = geometry.MultiGeometry(kml_geometries=[point, line])
    pm = kml.Placemark(name=f"{metainfos.image_name}",
                       # TODO: how to properly wrap description CDATA?
                       description=desc,
                       id=f"{metainfos.image_name}",
                       kml_geometry=mg)
    doc.append(pm)
    return k
